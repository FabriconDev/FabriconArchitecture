"""Promote Fabric workspace content from a development stage to production.

Steps: gate, sync, deploy, bind, verify, refresh, clean up. Each one raises on
failure so a partial promotion stops the run instead of continuing quietly.

Required environment:
    FABRIC_TOKEN            bearer token for https://api.fabric.microsoft.com
    DEV_WORKSPACE_ID        code workspace tracking the develop branch
    PROD_WORKSPACE_ID       code workspace receiving the deployment
    DEPLOYMENT_PIPELINE_ID  Fabric deployment pipeline
    DEV_STAGE_ID            source stage of that pipeline
    PROD_STAGE_ID           target stage

Optional:
    DEV_DATA_WORKSPACE_ID   data workspaces, under Fabricon 3 and R, where the
    PROD_DATA_WORKSPACE_ID  lakehouses live. Defaults to the code workspaces.
    SYNC_ONLY               set to true to update the dev workspace and stop
    VERIFY_ACTIVE_VALUE_SETS  e.g. "Config=Workspace_<prod-guid>"
    FEATURE_WS_PREFIX       enables feature workspace cleanup
    ADO_* or GITHUB_*       credentials for the branch check used by cleanup
"""

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

FABRIC = "https://api.fabric.microsoft.com/v1"
POWERBI = "https://api.powerbi.com/v1.0/myorg"

RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 5
OPERATION_TIMEOUT = 30 * 60
REFRESH_TIMEOUT = 60 * 60
REFRESH_DONE = {"Completed", "Failed", "Disabled", "Cancelled"}


def call(method, url, body=None, ok=(200, 201, 202)):
    payload = json.dumps(body).encode() if body is not None else None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        req = urllib.request.Request(
            url,
            data=payload,
            method=method,
            headers={
                "Authorization": "Bearer " + os.environ["FABRIC_TOKEN"],
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read()
                if resp.status not in ok:
                    raise SystemExit(f"{method} {url}: unexpected status {resp.status}")
                return resp.status, resp.headers, json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            if e.code in RETRY_STATUSES and attempt < MAX_ATTEMPTS:
                # Fabric and Power BI both send Retry-After on a throttle.
                wait = int(e.headers.get("Retry-After") or 2 ** attempt)
                print(f"  {e.code} from {method} {url}, retrying in {wait}s")
                time.sleep(wait)
                continue
            raise SystemExit(f"{method} {url} failed: {e.code} {e.read().decode(errors='replace')}")
        except urllib.error.URLError as e:
            if attempt < MAX_ATTEMPTS:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f"{method} {url} failed: {e}")


def paged(url):
    """Fabric list endpoints return one page plus a continuation token."""
    results = []
    while url:
        _, _, body = call("GET", url)
        results.extend(body.get("value", []))
        token = body.get("continuationToken")
        url = f"{url.split('?')[0]}?continuationToken={urllib.parse.quote(token)}" if token else None
    return results


def wait_for_operation(headers, description):
    op_id = headers.get("x-ms-operation-id")
    if not op_id:
        return None
    deadline = time.time() + OPERATION_TIMEOUT
    while True:
        _, _, op = call("GET", f"{FABRIC}/operations/{op_id}")
        state = op.get("status")
        if state == "Succeeded":
            print(f"{description}: succeeded")
            return op_id
        if state in ("Failed", "Cancelled"):
            raise SystemExit(f"{description}: {state}: {op.get('error')}")
        if time.time() > deadline:
            raise SystemExit(f"{description}: still {state} after {OPERATION_TIMEOUT}s, giving up")
        time.sleep(10)


def list_items(workspace):
    return paged(f"{FABRIC}/workspaces/{workspace}/items")


def get_definition(workspace, item, fmt=None):
    suffix = f"?format={fmt}" if fmt else ""
    status, headers, body = call(
        "POST", f"{FABRIC}/workspaces/{workspace}/items/{item}/getDefinition{suffix}"
    )
    if status == 202:
        op_id = wait_for_operation(headers, "getDefinition")
        _, _, body = call("GET", f"{FABRIC}/operations/{op_id}/result")
    return body["definition"]


def update_definition(workspace, item, definition):
    _, headers, _ = call(
        "POST",
        f"{FABRIC}/workspaces/{workspace}/items/{item}/updateDefinition",
        {"definition": definition},
    )
    wait_for_operation(headers, "updateDefinition")


def gate_and_update(workspace):
    _, _, status = call("GET", f"{FABRIC}/workspaces/{workspace}/git/status")
    dirty = sorted(
        c["itemMetadata"]["displayName"]
        for c in status.get("changes", [])
        if c.get("workspaceChange")
    )
    if dirty:
        raise SystemExit(
            "Dev workspace has uncommitted changes, refusing to promote: " + ", ".join(dirty)
        )
    head, remote = status.get("workspaceHead"), status.get("remoteCommitHash")
    if head == remote:
        print("Dev workspace already matches the remote head")
        return remote
    print(f"updating Dev workspace from git: {head} -> {remote}")
    _, headers, _ = call(
        "POST",
        f"{FABRIC}/workspaces/{workspace}/git/updateFromGit",
        {
            "workspaceHead": head,
            "remoteCommitHash": remote,
            "conflictResolution": {
                "conflictResolutionType": "Workspace",
                "conflictResolutionPolicy": "PreferRemote",
            },
            # Safe only because the gate above proved there is nothing
            # uncommitted in the workspace to lose.
            "options": {"allowOverrideItems": True},
        },
    )
    wait_for_operation(headers, "updateFromGit")
    return remote


def deploy(pipeline, source_stage, target_stage, note):
    _, headers, _ = call(
        "POST",
        f"{FABRIC}/deploymentPipelines/{pipeline}/deploy",
        {"sourceStageId": source_stage, "targetStageId": target_stage, "note": note},
    )
    wait_for_operation(headers, "deploy")


def lakehouses_in(workspace):
    return {i["displayName"]: i["id"] for i in list_items(workspace) if i["type"] == "Lakehouse"}


def authored_semantic_models(items):
    """Every lakehouse and warehouse gets a default semantic model of the same
    name. Those are not ours to bind or refresh, and asking for their definition
    fails, so keep only the models somebody actually authored."""
    generated = {i["displayName"] for i in items if i["type"] in ("Lakehouse", "Warehouse")}
    return [i for i in items if i["type"] == "SemanticModel" and i["displayName"] not in generated]


def bind_notebook_lakehouses(target_workspace, data_workspace, items):
    """Point each notebook at the lakehouse of the same name in the target stage.

    Under Fabricon 3 and R the lakehouses live in a separate data workspace, so
    that is where the names are resolved and what the rewritten ids point at.
    """
    available = lakehouses_in(data_workspace)
    for nb in (i for i in items if i["type"] == "Notebook"):
        definition = get_definition(target_workspace, nb["id"], fmt="ipynb")
        part = next(p for p in definition["parts"] if p["path"].endswith(".ipynb"))
        content = json.loads(base64.b64decode(part["payload"]))
        dep = content.get("metadata", {}).get("dependencies", {}).get("lakehouse")
        if not dep or not dep.get("default_lakehouse_name"):
            print(f"bind: {nb['displayName']}: no default lakehouse declared, skipping")
            continue

        name = dep["default_lakehouse_name"]
        if name not in available:
            raise SystemExit(
                f"bind: {nb['displayName']} wants lakehouse '{name}', which does not exist "
                f"in workspace {data_workspace}"
            )
        target_id = available[name]

        already_bound = (
            dep.get("default_lakehouse") == target_id
            and dep.get("default_lakehouse_workspace_id") == data_workspace
            and [k.get("id") for k in dep.get("known_lakehouses", [])] == [target_id]
        )
        if already_bound:
            print(f"bind: {nb['displayName']}: already bound to '{name}'")
            continue

        dep["default_lakehouse"] = target_id
        dep["default_lakehouse_workspace_id"] = data_workspace
        # known_lakehouses is what the session mounts. Leaving it behind means a
        # Prod notebook can still reach the Dev lakehouse.
        if "known_lakehouses" in dep:
            dep["known_lakehouses"] = [{"id": target_id}]
        part["payload"] = base64.b64encode(json.dumps(content).encode()).decode()
        update_definition(target_workspace, nb["id"], definition)
        print(f"bind: {nb['displayName']}: lakehouse -> '{name}' in workspace {data_workspace}")


def endpoint_map(source_data_workspace, target_data_workspace):
    """Source stage SQL endpoint identities mapped to their target equivalents,
    matched by lakehouse name."""
    def endpoints(ws):
        found = {}
        for lh in (i for i in list_items(ws) if i["type"] == "Lakehouse"):
            _, _, detail = call("GET", f"{FABRIC}/workspaces/{ws}/lakehouses/{lh['id']}")
            props = detail.get("properties", {}).get("sqlEndpointProperties") or {}
            if props.get("connectionString"):
                found[lh["displayName"]] = (props["connectionString"], props["id"])
        return found

    src, tgt = endpoints(source_data_workspace), endpoints(target_data_workspace)
    pairs = {}
    for name, (conn, db) in src.items():
        if name in tgt:
            pairs[conn] = tgt[name][0]
            pairs[db] = tgt[name][1]
    return pairs


def bind_semantic_models(target_workspace, pairs, items):
    """Direct Lake models do not autobind, so any source stage endpoint still
    named in a target model is rewritten here."""
    if not pairs:
        return
    for sm in authored_semantic_models(items):
        definition = get_definition(target_workspace, sm["id"])
        changed = 0
        for part in definition["parts"]:
            text = base64.b64decode(part["payload"]).decode("utf-8", errors="replace")
            rewritten = text
            for old, new in pairs.items():
                rewritten = rewritten.replace(old, new)
            if rewritten != text:
                part["payload"] = base64.b64encode(rewritten.encode()).decode()
                changed += 1
        if changed:
            update_definition(target_workspace, sm["id"], definition)
            print(f"bind: {sm['displayName']}: rebound to the target stage endpoint")
        else:
            print(f"bind: {sm['displayName']}: no source stage endpoint references")


def verify(source_workspaces, target_workspace, items, source_endpoints):
    """Nothing in the target stage may still reference the source stage."""
    source_ids = set(source_workspaces)
    for ws in source_workspaces:
        source_ids.update(i["id"] for i in list_items(ws))
    markers = source_ids | set(source_endpoints)
    failures = []

    for nb in (i for i in items if i["type"] == "Notebook"):
        definition = get_definition(target_workspace, nb["id"], fmt="ipynb")
        part = next(p for p in definition["parts"] if p["path"].endswith(".ipynb"))
        dep = (
            json.loads(base64.b64decode(part["payload"]))
            .get("metadata", {}).get("dependencies", {}).get("lakehouse") or {}
        )
        referenced = [dep.get("default_lakehouse"), dep.get("default_lakehouse_workspace_id")]
        referenced += [k.get("id") for k in dep.get("known_lakehouses", [])]
        if any(r in source_ids for r in referenced if r):
            failures.append(f"{nb['displayName']}: still attached to a source stage lakehouse")

    for item in (i for i in items if i["type"] in ("DataPipeline", "Report")):
        for part in get_definition(target_workspace, item["id"])["parts"]:
            text = base64.b64decode(part["payload"]).decode(errors="replace")
            for marker in source_ids:
                if marker in text:
                    failures.append(f"{item['displayName']}: {part['path']} references {marker}")

    for sm in authored_semantic_models(items):
        for part in get_definition(target_workspace, sm["id"])["parts"]:
            text = base64.b64decode(part["payload"]).decode(errors="replace")
            for marker in markers:
                if marker in text:
                    failures.append(f"{sm['displayName']}: {part['path']} references the source stage")

    expected = dict(
        pair.split("=", 1)
        for pair in os.environ.get("VERIFY_ACTIVE_VALUE_SETS", "").split(",")
        if "=" in pair
    )
    for vl in (i for i in items if i["type"] == "VariableLibrary"):
        want = expected.get(vl["displayName"])
        if not want:
            continue
        _, _, detail = call(
            "GET", f"{FABRIC}/workspaces/{target_workspace}/VariableLibraries/{vl['id']}"
        )
        active = detail.get("properties", {}).get("activeValueSetName")
        if active != want:
            failures.append(f"{vl['displayName']}: active value set is '{active}', expected '{want}'")

    if failures:
        raise SystemExit("verification failed:\n  " + "\n  ".join(failures))
    print(f"verify: {len(items)} target items checked, no source stage references")


def refresh_semantic_models(target_workspace, items):
    models = authored_semantic_models(items)
    started = {}
    for sm in models:
        # Remember the newest refresh before triggering, otherwise polling can
        # pick up a previous run and report it as this one.
        _, _, before = call(
            "GET", f"{POWERBI}/groups/{target_workspace}/datasets/{sm['id']}/refreshes?$top=1"
        )
        previous = before["value"][0].get("requestId") if before.get("value") else None
        call(
            "POST",
            f"{POWERBI}/groups/{target_workspace}/datasets/{sm['id']}/refreshes",
            {"type": "full", "commitMode": "transactional"},
        )
        started[sm["id"]] = previous
        print(f"refresh: {sm['displayName']}: triggered")

    deadline = time.time() + REFRESH_TIMEOUT
    for sm in models:
        while True:
            _, _, body = call(
                "GET", f"{POWERBI}/groups/{target_workspace}/datasets/{sm['id']}/refreshes?$top=1"
            )
            latest = body["value"][0] if body.get("value") else {}
            is_ours = latest.get("requestId") != started[sm["id"]]
            status = latest.get("status")
            if is_ours and status in REFRESH_DONE:
                if status != "Completed":
                    raise SystemExit(f"refresh: {sm['displayName']}: {status}")
                print(f"refresh: {sm['displayName']}: completed")
                break
            if time.time() > deadline:
                raise SystemExit(f"refresh: {sm['displayName']}: timed out waiting for completion")
            time.sleep(10)


def git_provider():
    """The configured repository, and a way to ask whether a branch still exists.

    Azure DevOps needs ADO_TOKEN, ADO_ORG_URL, ADO_PROJECT and ADO_REPO. GitHub
    needs GITHUB_TOKEN and GITHUB_REPOSITORY, both of which Actions provides.
    """
    ado_token = os.environ.get("ADO_TOKEN")
    gh_token = os.environ.get("GITHUB_TOKEN")

    if ado_token and os.environ.get("ADO_ORG_URL"):
        org_url = os.environ["ADO_ORG_URL"].rstrip("/")
        org = org_url.rstrip("/").split("/")[-1]
        project = os.environ["ADO_PROJECT"]
        repo = os.environ["ADO_REPO"]

        def exists(branch):
            req = urllib.request.Request(
                f"{org_url}/{project}/_apis/git/repositories/{repo}/refs"
                f"?filter=heads/{urllib.parse.quote(branch)}&api-version=7.1",
                headers={"Authorization": "Bearer " + ado_token},
            )
            with urllib.request.urlopen(req) as resp:
                refs = json.loads(resp.read()).get("value", [])
            return any(r.get("name") == f"refs/heads/{branch}" for r in refs)

        return {"organizationName": org, "projectName": project, "repositoryName": repo}, exists

    if gh_token and os.environ.get("GITHUB_REPOSITORY"):
        owner, repo = os.environ["GITHUB_REPOSITORY"].split("/", 1)

        def exists(branch):
            req = urllib.request.Request(
                f"https://api.github.com/repos/{owner}/{repo}/git/ref/"
                f"heads/{urllib.parse.quote(branch)}",
                headers={
                    "Authorization": "Bearer " + gh_token,
                    "Accept": "application/vnd.github+json",
                },
            )
            try:
                with urllib.request.urlopen(req) as resp:
                    return resp.status == 200
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return False
                raise

        return {"organizationName": owner, "repositoryName": repo}, exists

    return None, None


def cleanup_feature_workspaces():
    """Delete feature workspaces whose branch has been merged and removed.

    Three things have to be true before anything is deleted: the name matches
    the agreed prefix, the workspace is connected to the same repository this
    pipeline promotes from, and it holds no uncommitted work.
    """
    prefix = os.environ.get("FEATURE_WS_PREFIX")
    if not prefix:
        print("cleanup: FEATURE_WS_PREFIX not set, skipping")
        return

    repo, branch_exists = git_provider()
    if not repo:
        print("cleanup: no git provider credentials set, skipping")
        return

    for ws in paged(f"{FABRIC}/workspaces"):
        name = ws["displayName"]
        if not name.startswith(prefix):
            continue
        try:
            _, _, conn = call("GET", f"{FABRIC}/workspaces/{ws['id']}/git/connection")
        except SystemExit:
            print(f"cleanup: {name}: git connection not readable, leaving alone")
            continue

        details = conn.get("gitProviderDetails") or {}
        branch = details.get("branchName")
        if not branch:
            print(f"cleanup: {name}: not git connected, leaving alone")
            continue

        mismatched = [
            key for key, value in repo.items()
            if (details.get(key) or "").lower() != value.lower()
        ]
        if mismatched:
            print(f"cleanup: {name}: belongs to a different repository, leaving alone")
            continue

        if branch_exists(branch):
            print(f"cleanup: {name}: branch '{branch}' still exists, active work")
            continue

        _, _, status = call("GET", f"{FABRIC}/workspaces/{ws['id']}/git/status")
        if any(c.get("workspaceChange") for c in status.get("changes", [])):
            print(f"cleanup: {name}: has uncommitted changes, leaving alone")
            continue

        call("DELETE", f"{FABRIC}/workspaces/{ws['id']}", ok=(200, 204))
        print(f"cleanup: {name}: branch '{branch}' is gone, workspace deleted")


def main():
    dev = os.environ["DEV_WORKSPACE_ID"]
    prod = os.environ["PROD_WORKSPACE_ID"]
    dev_data = os.environ.get("DEV_DATA_WORKSPACE_ID", dev)
    prod_data = os.environ.get("PROD_DATA_WORKSPACE_ID", prod)

    remote = gate_and_update(dev)
    if os.environ.get("SYNC_ONLY", "").lower() in ("1", "true", "yes"):
        print("SYNC_ONLY is set, stopping before deployment")
        return

    deploy(
        os.environ["DEPLOYMENT_PIPELINE_ID"],
        os.environ["DEV_STAGE_ID"],
        os.environ["PROD_STAGE_ID"],
        f"Automated deploy of {remote[:8]}",
    )

    items = list_items(prod)
    pairs = endpoint_map(dev_data, prod_data)
    bind_notebook_lakehouses(prod, prod_data, items)
    bind_semantic_models(prod, pairs, items)
    verify({dev, dev_data}, prod, items, pairs.keys())
    refresh_semantic_models(prod, items)
    cleanup_feature_workspaces()
    print("promotion complete")


if __name__ == "__main__":
    main()
