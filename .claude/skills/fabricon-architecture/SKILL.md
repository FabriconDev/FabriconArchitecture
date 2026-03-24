---
name: fabricon-architecture
description: Use when working on Microsoft Fabric projects that follow Fabricon patterns, making workspace or environment decisions, organizing notebooks or pipelines, setting up medallion architecture, planning deployment or source control strategy, writing pipeline step code, choosing between lakehouse and warehouse, promoting Power BI reports across environments, or managing lakehouse shortcuts. Also use when someone references a Fabricon pattern number (1-4, N, R).
---

# Fabricon Architecture

## Overview

Fabricon is a progressive architectural framework for managing software projects on Microsoft Fabric. It combines data engineering and software engineering best practices into numbered patterns of increasing complexity, plus lettered extensions that apply to any numbered pattern.

## Writing Style

- **No em dashes or double dashes.** Never use `—` or `--` as punctuation. Instead, rephrase using periods, commas, colons, parentheses, or conjunctions (e.g., "and", "so", "because").

Created by the engineering team at Unite Digital LLC.

## When to Use

- Making workspace or environment decisions on Microsoft Fabric
- Organizing notebooks, pipelines, or lakehouses
- Setting up medallion architecture (Bronze/Silver/Gold)
- Planning deployment or source control strategy
- Writing or modifying pipeline step code
- Choosing between lakehouse and warehouse
- Promoting Power BI reports or semantic models across environments
- Managing lakehouse shortcuts (creation, automation, cross-layer access)
- Someone says "Fabricon 1", "Fabricon 2N", "Fabricon R", etc.

## Pattern Progression

| Pattern | Name | When to Use |
|---------|------|-------------|
| **1** | Basic Environment Segregation | Any project needing dev/prod separation |
| **2** | Medallion-Based Environment | Projects needing structured Bronze/Silver/Gold data layers |
| **3** | Large Data Volumes | When duplicating bronze data across envs is impractical |
| **4** | Seamless Reporting | Near real-time reporting from mirrored databases |
| **5** | Realtime Reporting with EventHouse | (Coming soon) |
| **N** | Code Organization Using Notebooks | Extension for any numbered pattern (e.g., "2N") |
| **R** | Report Promotion Across Environments | Extension for promoting Power BI reports/semantic models across Dev/Prod |

> Numbered patterns build on each other (3 includes 2 includes 1). Letter extensions apply to any number.

## Quick Reference

| Decision | Fabricon Says |
|----------|--------------|
| Lakehouse vs Warehouse? | Lakehouse, unless explicit warehouse need |
| How many workspaces? | One per environment (not per medallion layer) |
| Cross-layer data access? | Shortcuts + named schemas |
| Large shared data? | Shared workspace with shortcuts (F3) |
| Code structure in notebooks? | Abstract base class with `_get_data` / `_write_to_lakehouse` / `run` |
| Pipeline orchestration? | Tiered: Main → Bronze → Silver → Gold |
| Shared utilities? | Python wheel packages, not custom Spark envs |
| Incremental loads? | Max-date tracking + Delta MERGE upsert |
| Deployment? | Post-deployment notebook for lakehouse rebinding |
| Reporting on mirrors? | Intermediary lakehouse with shortcuts (F4) |
| Report promotion? | Reports in Data workspaces (not Git), promote via Deployment Pipeline (FR) |
| Embed URLs? | Store `reportId` in app config; resolve per environment |
| Shortcut provisioning? | Tier notebooks (Silver, Gold) using `create_shortcut()` via REST API with `table_exists()` guard (idempotent, every run) |
| Naming convention? | `Domain-Environment[-Layer]` (e.g., `CRM-Dev`, `CRM-Data-Prod`) |

## Fabricon 1: Basic Environment Segregation

One Fabric workspace per environment. For a CRM data product:

- `CRM-Dev` (development and testing)
- `CRM-Prod` (production)

Each workspace contains all items: lakehouse, data pipeline, notebooks, reports.

## Fabricon 2: Medallion-Based Environment Architecture

Adds Bronze/Silver/Gold lakehouses **within** each workspace (not separate workspaces per layer, as that is overkill for most projects).

Each workspace has:
- `CRMBronze` lakehouse
- `CRMSilver` lakehouse
- `CRMGold` (or simply `CRM`) lakehouse

> Lakehouse names do not support dashes. Use PascalCase (e.g., CRMBronze). For the Gold layer, both CRM and CRMGold are valid since Gold is the externally facing layer.

### Lakehouse Schema (Cross-Layer Access)

Notebooks can only connect to one default lakehouse. Use schemas + shortcuts:

- `dbo` schema = current medallion layer
- Named schemas (`Bronze`, `Silver`) = shortcuts to other layers

Example on Silver lakehouse:
- `Bronze.Customer` → shortcut to Bronze `dbo.Customer`
- `dbo.CustomerOrder` → native Silver table

This enables multi-layer access within the one-lakehouse-per-session constraint.

### Source Control

- `main` branch ↔ `CRM-Prod` workspace
- `develop` branch ↔ `CRM-Dev` workspace
- Feature branches via "Branch out to new workspace"
- PR flow: feature → develop → main

### Folder Structure

- **Archive**: items pending deletion
- **Configuration**: environment configuration notebooks and Variable Libraries
- **Exploration**: research and ad-hoc analysis
- **Pipeline**: main workflow items
- **Reports**: Power BI reports (see Fabricon R for guidance on moving reports to Data workspaces)
- **Tests**: pipeline and data validation tests
- Readme notebook at workspace root

### Pipeline Notifications

Send HTML email on pipeline completion with per-step results: step name, start/end times, duration, success/failure, notes. Use Office 365 Connector.

## Fabricon 3: Large Data Volumes

Separates code and data into different workspaces to avoid duplicating large datasets:

- `CRM-Shared` (shared bronze lakehouse with large data)
- `CRM-Dev` (code: notebooks, pipelines; linked to `develop` branch)
- `CRM-Prod` (code; linked to `main` branch)
- `CRM-Data-Dev` (data lakehouses: Bronze, Silver, Gold)
- `CRM-Data-Prod` (data lakehouses)

Each `CRMBronze` lakehouse uses shortcuts to large tables in `CRM-Shared`.

## Fabricon 4: Seamless Reporting with Database Mirroring

Strategy for near real-time reporting from mirrored databases (SQL Server, Cosmos DB, etc.):

1. Mirror operational databases into Fabric
2. Create an intermediary **reporting lakehouse**
3. Bring mirrored tables in via **shortcuts**
4. Add tables to **Default Power BI semantic model**
5. Connect Power BI reports to the semantic model

> Connect Power BI to the intermediary lakehouse, not directly to mirrored databases.

For transformations on mirrored data:
- **SQL Views**: simple but slower (falls back to DirectQuery)
- **Traditional ETL**: when view performance is unacceptable

## Fabricon R: Report Promotion Across Environments

Extension that applies to Fabricon 2, 3, and 4, covering any pattern needing Power BI report/semantic model promotion.

### The Problem

Power BI reports and semantic models use logical IDs that are workspace-specific. Git integration causes logicalId conflicts when syncing reports between Dev and Prod workspaces. Fabric Deployment Pipelines assign different `reportId` GUIDs per stage, breaking hardcoded embed URLs. Separating report from semantic model across workspaces compounds the issue.

### Core Principle

**Reports and semantic models are data artifacts, not code artifacts.** They belong in Data workspaces (not Git-controlled) and are promoted via Fabric Deployment Pipelines, separate from notebooks/pipelines which flow through Git.

### Workspace Structure (extends Fabricon 3)

| Workspace | Contents | Source Control | Promotion |
|-----------|----------|---------------|-----------|
| `CRM-Dev` | Notebooks, pipelines, DevOps notebook | Git (`develop`) | PR merge → `CRM-Prod` |
| `CRM-Prod` | Notebooks, pipelines, DevOps notebook | Git (`main`) | N/A |
| `CRM-Data-Dev` | Lakehouses, semantic models, reports | None | Deployment Pipeline → |
| `CRM-Data-Prod` | Lakehouses, semantic models, reports | None | ← Target |

> Reports and semantic models live in Data workspaces, not Code workspaces. This eliminates logicalId conflicts entirely because reports never touch Git.

### Promotion Flow

1. **Code promotion (Git):** `develop` → PR → `main`. Notebooks and pipelines sync to `CRM-Prod`.
2. **Report/model promotion (Deployment Pipeline):** `CRM-Data-Dev` → `CRM-Data-Prod`. Reports and semantic models copied to Prod.
3. **Post-deploy rebind (DevOps notebook in CRM-Prod):**
   - `update_direct_lake_model_lakehouse_connection()` repoints semantic model to Prod lakehouse
   - `report_rebind()` repoints report to Prod semantic model
   - Notebook lakehouse connections updated in parallel

### DevOps Notebook Location

The DevOps notebook is **code** and lives in the Code workspace (`CRM-Dev`/`CRM-Prod`), not the Data workspace. It reaches across to the Data workspace via `DATA_WORKSPACE_ID` environment variable. Uses `semantic-link-labs` for Direct Lake connection updates and report rebinding.

### Deployment Pipeline Prerequisites

- Items must be **initially created in Data-Dev and first deployed through the pipeline** to establish pairing
- Once paired, subsequent deploys update the paired items
- Deployment pipelines copy metadata only. Lakehouse data is preserved and never overwritten.
- **Shortcuts are overwritten** during deployment. Use Variable Libraries for environment-specific targets.

### Embed URL Strategy

Embed URLs use the format: `https://app.fabric.microsoft.com/reportEmbed?reportId={reportId}&autoAuth=true&ctid={tenantId}`

- Only `reportId` differs between Dev and Prod (tenantId is constant)
- Store environment-specific `reportId` in app config (`appsettings.json`)
- Update after fresh pipeline deploy (reportId changes per stage)
- For long-term: consider dynamic resolution via `Get Reports In Group` REST API using workspace name + report name

### What Fabricon R Solves

| Problem | Solution |
|---------|----------|
| Git logicalId conflicts | Reports aren't in Git |
| Deployment pipeline logicalId conflicts | Pipeline pairing via initial deploy |
| Embed URL breaks on promotion | Environment-specific `reportId` in app config |
| Semantic model → wrong lakehouse | DevOps notebook rebinds via Semantic Link Labs |
| Report → wrong semantic model | DevOps notebook rebinds via `report_rebind()` |
| Code workspace clutter from report files | Reports in Data workspace, not Git-controlled |

## Fabricon N: Code Organization Using Notebooks

Extension that applies to any numbered pattern (Fabricon 1N, 2N, 3N).

### Pipeline Step Contract

```python
class PipelineStepBase(ABC):
    @abstractmethod
    def _get_data(self) -> DataFrame: pass

    @abstractmethod
    def _write_to_lakehouse(self, df: DataFrame): pass

    @abstractmethod
    def run(self) -> PipelineResult: pass
```

### Pipeline Result Tracking

`PipelineResult` captures: step_name, is_success, message, start/end times, exception.
`PipelineResultList` aggregates results for notification emails.

### Tiered Orchestration

- `00 - Main`: Fabric Data Pipeline orchestrating tier notebooks
- `01 - Bronze.Notebook`: all ingestion steps
- `02 - Silver.Notebook`: all transformation steps
- `03 - Gold.Notebook`: all aggregation/metric steps

Each tier runs independently (own timeout/retry). Steps ordered within tier notebook, not by filename.

> Watch for Fabric's notebook reference chain depth limit. Workaround: schedule tiers independently instead of chaining through `00 - Main`.

### Data Access Abstraction

`LakeHouseDataService` provides: `execute_query`, `execute_scalar`, `upsert` (Delta MERGE), `replace` (overwrite), `read_json_file`, `read_csv_file`. Share via Python wheel package.

### Incremental Processing

```python
def _get_data(self):
    max_date = self.data_service.execute_scalar(
        "SELECT MAX(Date) AS MaxDate FROM dbo.Metric", "MaxDate", FALLBACK_DATE
    )
    return self.data_service.execute_query(f"SELECT * FROM Bronze.Events WHERE Date >= '{max_date}'")

def _write_to_lakehouse(self, df):
    self.data_service.upsert(df, "dbo.Metric", "existing.Id = updates.Id AND existing.Date = updates.Date")
```

Use `upsert` for incremental updates, `replace` for reference data needing full refresh.

### Development Mode

```python
# Bottom of each pipeline step notebook
if __name__ == "__main__" and os.getenv("PIPELINE_RUN") != "True":
    step = MyStep(spark)
    result = step.run()
    print(result)
```

Orchestrator sets `os.environ["PIPELINE_RUN"] = "True"` before running steps.

### Wheel Packages over Custom Spark Environments

Use `%pip install https://yourblobstore.com/package.whl?token` instead of custom Spark environments. Custom envs increase session start from 3-10s to 50-120s.

Good candidates for wheel packages: `LakeHouseDataService`, logger, email sender.

### Deployment

Post-deployment notebook uses `notebookutils.notebook.updateDefinition()` to repoint notebooks to the correct lakehouse per environment. Environment configuration is read from a Fabric Variable Library named `Config` using `notebookutils.credentials.getSecret()`:

```python
# Common notebook pattern
DATA_ENVIRONMENT = notebookutils.credentials.getSecret("Config", "DATA_ENVIRONMENT")
DATA_WORKSPACE_ID = notebookutils.credentials.getSecret("Config", "DATA_WORKSPACE_ID")
```

Each workspace (Dev, Prod, feature workspaces) has its own `Config` Variable Library with the appropriate values. This avoids hardcoding workspace IDs in notebooks and ensures feature workspaces work without code changes.

### Shortcut Provisioning

Applies to any Fabricon pattern using cross-lakehouse shortcuts (Fabricon 2, 3, 4).

#### Key Insight

OneLake shortcuts are **pointers to storage paths**, not references to live table objects. They can be created **before source tables exist**. When notebooks later populate Bronze/Silver tables, shortcuts automatically resolve.

#### Where to Place

Shortcut provisioning belongs in **tier notebooks** (`02 - Silver.Notebook`, `03 - Gold.Notebook`), not the DevOps notebook:
- Each tier notebook has its **default lakehouse connected**, so the REST API targets the correct lakehouse automatically
- The **DevOps notebook has no lakehouse connected** (its job is to rebind other notebooks)
- Shortcuts are **idempotent** and safe to run every pipeline execution

#### Provisioning Sequence

1. Lakehouses pre-exist in Data workspace (manually or via deployment pipeline)
2. Tier notebooks create shortcuts before pipeline steps (pointing to paths that may be empty on first run)
3. Pipeline steps populate tables
4. Shortcuts automatically resolve, and tables appear via `Bronze.*` and `Silver.*` schemas

#### Implementation

Use `LakeHouseDataService.table_exists()` to check if a shortcut already exists, `sempy.fabric.list_items()` to resolve source lakehouse IDs, and the Fabric REST API to create shortcuts:

```python
import requests
import sempy.fabric as fabric
from unite_digital.lakehouse_data_service import LakeHouseDataService

DATA_ENVIRONMENT = notebookutils.credentials.getSecret("Config", "DATA_ENVIRONMENT")
DATA_WORKSPACE_ID = notebookutils.credentials.getSecret("Config", "DATA_WORKSPACE_ID")

data_service = LakeHouseDataService(spark, notebookutils, DeltaTable)
lakehouses = fabric.list_items(type="Lakehouse", workspace=DATA_WORKSPACE_ID)
bronze_lakehouse_id = lakehouses[lakehouses["Display Name"] == "CRMBronze"]["Id"].values[0]


def create_shortcut(
    shortcut_name: str,
    shortcut_path: str,
    target_lakehouse_id: str,
    target_workspace_id: str,
    target_path: str
):
    """Creates a OneLake shortcut via Fabric REST API if it doesn't already exist."""
    if data_service.table_exists(shortcut_name):
        return

    token = notebookutils.credentials.getToken("https://api.fabric.microsoft.com")
    lakehouse_id = fabric.get_lakehouse_id()
    workspace_id = fabric.get_notebook_workspace_id()
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{lakehouse_id}/shortcuts"

    payload = {
        "path": shortcut_path,
        "name": shortcut_name,
        "target": {
            "oneLake": {
                "workspaceId": target_workspace_id,
                "itemId": target_lakehouse_id,
                "path": target_path
            }
        }
    }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 409:
        return
    if not response.ok:
        raise RuntimeError(
            f"Shortcut '{shortcut_name}' creation failed ({response.status_code}): {response.text}"
        )


shortcuts = {"Customer": "/Tables/dbo/Customer"}

for name, path in shortcuts.items():
    create_shortcut(
        shortcut_name=f"Bronze.{name}",
        shortcut_path="Tables",
        target_lakehouse_id=bronze_lakehouse_id,
        target_workspace_id=DATA_WORKSPACE_ID,
        target_path=path
    )
```

Best practices:
- **Idempotent**: `table_exists()` check inside `create_shortcut()` and 409 handling make it safe to re-run every execution
- **Manifest-driven**: define all shortcuts in a dictionary/config
- **Environment-agnostic**: use `DATA_WORKSPACE_ID` from Variable Library to target the correct workspace
- **Fail fast**: `RuntimeError` raised on unexpected failures

> For environment-specific shortcut targets, use Fabric Variable Libraries. For cross-lakehouse shortcuts within the same workspace, Variable Libraries are not needed.

### Unit Testing

Each notebook with functionality should have a corresponding test notebook. Same notebook code runs in both tests and pipeline.

### Automated Documentation

- GitHub: Use nbdev to generate GitHub Pages from notebooks
- Azure DevOps: Use nbdev's `showdoc` function for in-notebook documentation

### Code Formatting

Use jupyter-black extension for automatic Python formatting in notebooks.
