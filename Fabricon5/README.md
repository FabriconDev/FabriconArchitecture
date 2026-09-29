# Fabricon 5: Automated Deployment and Promotion

> Fabricon 5 builds on the branching strategy in [Fabricon 2](../Fabricon2/README.md), the DevOps notebook in [Fabricon N](../FabriconN/README.md), and the report promotion approach in [Fabricon R](../FabriconR/README.md).

Three earlier patterns already cover the individual pieces of moving code from development to production. Fabricon 2 defines the branches and the feature workspace, Fabricon N provides the DevOps notebook that repoints notebooks and semantic models after a deployment, and Fabricon R explains how reports and models travel through a deployment pipeline. What none of them provides is the machinery that carries those steps out, so in practice a person has to merge the pull request, remember to open the target workspace and click Update, run the deployment pipeline, and then execute the DevOps notebook afterwards in the right workspace. Fabricon 5 replaces that sequence of remembered actions with a pipeline that performs them in order, refuses to start when the workspace is in a state that would make the result unsafe, and checks its own work before reporting the release as finished.

## The problems this solves

Teams promoting by hand tend to run into the following four problems.

Drift comes first, and it arises because anyone can create or edit an item directly in a workspace without committing it, while the only sign that they have done so is a badge on the Source control panel that nobody is watching. Given enough time, production ends up running notebooks that exist in no branch at all, so rebuilding that workspace would lose them permanently.

The second problem is the promotion that never happens, since merging a pull request updates the branch rather than the workspace, and somebody still has to open the target workspace and apply the change. When that step is missed, a fix that was reviewed and approved weeks earlier is still not running anywhere, and because nothing reports the gap it is usually discovered only when the original bug is reported for a second time.

The third is the reference that quietly points at the wrong environment. Item IDs are assigned per workspace and are never stored in git, so anything outside Fabric that refers to an item by ID breaks the moment that item is deleted and recreated. Direct Lake semantic models have a related weakness, in that one arriving in production carries on reading the development lakehouse until the rebind described in Fabricon R is executed against it.

The fourth is environment leakage, where notebooks and models carry hardcoded workspace and lakehouse IDs and therefore cannot run unchanged in more than one environment.

All four share the same root cause, which is that the process depends on a person remembering to do something.

## 1. Where Git stops

Fabricon 2 links the `main` branch to the production workspace and promotes code by merging `develop` into `main`. That works, but it leaves production reachable from two directions, because git can push into it and anyone holding Contributor access can edit it directly. Fabricon 5 narrows this to a single direction by disconnecting the production code workspace from git altogether and feeding it only through the deployment pipeline that Fabricon R already uses for reports.

> Fabricon recommends that the production code workspace has no Git connection and is treated as read-only, with the promotion pipeline as its only writer. If the pipeline is the only way in, then editing production directly is not merely discouraged, it is impossible, and the production environment is protected by the structure rather than by convention.

This supersedes the `main` to production link described in Fabricon 2, Fabricon 3 and Fabricon R, and it leaves three kinds of workspace with clearly different rules. Feature workspaces are created per ticket with the `Branch out to new workspace` feature from Fabricon 2, and the developer who created one owns it, works in it freely and deletes it once the ticket is done. The development workspace tracks `develop` and mirrors it, which means developers no longer need Contributor access there and are better given Viewer, since with a feature workspace of their own there is nothing left that they would legitimately edit in the shared one. The production workspace tracks nothing and receives content only when the pipeline promotes it.

From a developer's point of view the whole workflow is to branch out, work, commit from the Source control panel and open a pull request, which is the same sequence Fabricon 2 already describes. Everything that happens after the merge is automated.

## 2. The promotion pipeline

An Azure DevOps pipeline or a GitHub Actions workflow runs on merges to `develop` and carries out seven steps, each of which raises on failure so that a partial or unverified promotion stops the run rather than continuing quietly.

1. **Gate.** The run begins by reading the [git status](https://learn.microsoft.com/en-us/rest/api/fabric/core/git/get-status) of the development workspace, and if any item has uncommitted changes it stops and lists them, which is what makes drift impossible to ship.
2. **Sync.** The workspace is then [updated from git](https://learn.microsoft.com/en-us/rest/api/fabric/core/git/update-from-git). This call needs an `allowOverrideItems` consent flag before it will touch existing items, and passing it is only safe because the gate has just established that there is nothing uncommitted to lose, so the order of these two steps matters more than either step considered alone.
3. **Deploy.** With development matching the branch, the [deployment pipeline](https://learn.microsoft.com/en-us/rest/api/fabric/core/deployment-pipelines/deploy-stage-content) moves content to the production stage, overwriting the paired items in place so that their IDs and URLs remain the same from one release to the next.
4. **Bind.** The references that a deployment cannot resolve on its own are then repointed, using the same operations as the DevOps notebook in Fabricon N and Fabricon R but running them automatically rather than waiting for someone to execute the notebook.
5. **Verify.** Every production item is read back and its definition searched for development identities, meaning the workspace ID, item IDs and SQL endpoint names, and any match fails the release and names the item responsible.
6. **Refresh.** The semantic models that were deployed are refreshed, because a deployment does not refresh them and until it happens the reports built on them return an error.
7. **Clean up.** Finally, feature workspaces whose branch has been merged and deleted are removed, subject to two guards: the workspace name must match the agreed feature prefix, and the branch must genuinely be gone.

A reference implementation is included in this folder as [`promote.py`](./promote.py), written against the standard library and configured entirely through environment variables, alongside pipeline definitions for [Azure DevOps](./ado-pipeline.yml) and [GitHub Actions](./github-pipeline.yml). Bringing another domain onto the pattern is a copy of the pipeline definition with different IDs.

Under Fabricon 3 and R the lakehouses sit in their own data workspaces, so the promotion needs to know about those as well as the code workspaces. Set `DEV_DATA_WORKSPACE_ID` and `PROD_DATA_WORKSPACE_ID` in that case, and leave them out when code and data share a workspace.

> Fabricon recommends running the promotion as a service principal rather than as a person, so that releases are attributed to the process and do not depend on an individual's account. This requires the *Service principals can use Fabric APIs* tenant setting, with the principal added as an Admin on both workspaces and on the deployment pipeline.

## 3. Keeping references correct

Most references look after themselves, because Fabric maintains a pairing between each source item and its counterpart in the target stage and rewires the connections between paired items as it deploys them, which covers a report and its semantic model, a data pipeline and the notebook it calls, a notebook and a lakehouse in the same pipeline, and the targets of OneLake shortcuts.

Two kinds of reference are left over, and they are the reason the bind step exists. The first is a notebook whose default lakehouse lives in a different workspace, which is the normal arrangement under Fabricon 3 where data workspaces are kept separate from code, and it is handled by looking up the lakehouse of the same name in the target stage and rewriting the attachment, exactly as the DevOps notebook in Fabricon N does with `DATA_WORKSPACE_ID`. The second is a Direct Lake semantic model, which [by design](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/understand-the-deployment-process#considerations-and-limitations) still points at the source stage after being deployed, and which Fabricon R repoints using Semantic Link Labs; the same rebind happens here, driven by a map of endpoints built by matching lakehouses by name across the two stages.

Because both rebinds work by name rather than by identifier, a notebook or model created yesterday is handled correctly on its first deployment without anyone configuring anything on its behalf.

Fabric also offers [deployment rules](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/create-rules), which perform the same repointing through the portal and are worth knowing about, although they are set one item at a time and only by that item's owner, they are invisible to git, and they are lost if the workspace is ever unassigned and reassigned to the pipeline.

> Fabricon recommends rebinding through automation rather than deployment rules, because a rule has to be created by somebody who remembers that a new model needs one, and until they do, production is reading development data.

Whichever mechanism did the rebinding, the verify step is what makes the result trustworthy, since it is cheap to run and turns an assumption about production into a release that fails when the assumption turns out to be wrong.

## 4. Runtime configuration

Values that differ between environments belong in a [variable library](https://learn.microsoft.com/en-us/fabric/cicd/variable-library/variable-library-overview) rather than in the code. The variables and their value sets are versioned in git, while the choice of which value set is active is a per-workspace setting that survives deployments, so the same committed notebook resolves development values in one workspace and production values in another. Fabricon R already recommends variable libraries for environment-specific shortcut targets, and the same mechanism covers the workspace and lakehouse identifiers that would otherwise be hardcoded in notebooks.

The resolution itself belongs in the shared `Common` notebook that every pipeline step already runs with `%run`, which is where Fabricon N places it, and the change is to read the values from the library rather than from constants declared in the notebook. The fallback to development values for an unrecognised workspace, which Fabricon N already includes, remains exactly as important, because a branched-out feature workspace has an identifier that no configuration can know in advance:

```python
config = variable_library_values()          # normal path
if config is None:                          # unknown workspace = branched-out feature workspace
    print("WARNING: unknown workspace - assuming feature workspace, using Dev values")
    config = dev_defaults()
```

## 5. Working as a team

A common worry when several people are working at once is that their changes will collide during deployment, but they never meet there, because changes converge in git through pull requests and two people who have edited the same notebook find out at review time, in a readable text diff, rather than at release time. By the time `develop` moves it is a single history, and the pipeline treats a batch of forty merges exactly as it treats one.

That leaves the question of cadence. Promoting on every merge keeps batches small, so that when something does break the change responsible is a single pull request, whereas a release train lets merges keep the development workspace current and promotes to production on a schedule or behind an [environment approval](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals). Both work with the same pipeline. Setting `SYNC_ONLY` stops the run after the development workspace has been brought up to date, so a merge-triggered run can keep development current while a separate scheduled or approved run carries out the promotion.

> Fabricon recommends enabling *delete source branch on merge* in the repository, because together with the cleanup step it allows feature workspaces to retire themselves.

## 6. Exceptions and limitations

Deletions do not propagate, since a deployment never removes a production item that is missing from the source, which means retiring something is a separate manual step that belongs in the runbook.

Some state is deliberately not copied, including schedules, permissions, credentials and the active value set of a variable library. This is the behaviour you want, as a development schedule should never overwrite a production one, but it does mean each stage needs configuring once, and the verify step is a convenient place to assert the settings that matter.

Deleting an item and recreating it is the one action that undoes the guarantees described here, because the replacement is issued a new ID and everything that referenced the old one breaks, so publish over the existing item instead. A pull request check that flags deleted `.platform` files is a reasonable guard against doing it by accident.

Connections defined at tenant level, and shortcuts that reach into other workspaces, may be genuinely shared between stages or may need to differ, so classify them when a domain is onboarded rather than assuming either.

Support for some item types is still in preview for git, for deployment pipelines, or for both, which makes it worth testing a domain's inventory in a throwaway pair of workspaces before onboarding it.

## 7. Onboarding a domain

1. Reconcile what is already in production, committing or deliberately retiring every item that exists only in the workspace, resolving conflicts, and aligning folder structures, since pairing matches on name, type and folder.
2. Create the deployment pipeline, assign both workspaces and confirm that every item is paired before deploying anything.
3. Set the state that deployment does not copy, which is the active value set, schedules and credentials.
4. Classify connections and shortcuts as shared or stage-specific.
5. Copy the pipeline definition, set the IDs and the feature workspace prefix, and run it once with somebody watching.
6. Move developers to Viewer on the development workspace, remove standing access to production, and enable branch policies on `develop`.

## What Fabricon 5 Solves

| Problem | Solution |
| --- | --- |
| Direct edits in production workspaces | Production disconnected from Git and fed only by the promotion pipeline |
| Uncommitted work in the development workspace reaching production | Gate step refuses to promote a workspace that does not match its branch |
| Merged changes that are never promoted | Promotion triggered by the merge itself rather than by a person |
| DevOps notebook rebind forgotten or run out of order | Rebind performed automatically as a step of every release |
| Direct Lake models and notebooks silently reading the wrong environment | Verify step fails the release when production still references development |
| Reports erroring after a deployment | Semantic models refreshed as part of the release |
| Feature workspaces accumulating after their branch is merged | Cleanup step removes them once the branch is gone |

## References

- [CI/CD workflow options in Fabric](https://learn.microsoft.com/en-us/fabric/cicd/manage-deployment)
- [Understand the deployment pipelines process](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/understand-the-deployment-process)
- [Git integration in Fabric](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/intro-to-git-integration)
- [Variable libraries](https://learn.microsoft.com/en-us/fabric/cicd/variable-library/variable-library-overview)
- [fabric-cicd](https://microsoft.github.io/fabric-cicd/), a Microsoft library that applies the same definition-rewriting approach used by the bind step
