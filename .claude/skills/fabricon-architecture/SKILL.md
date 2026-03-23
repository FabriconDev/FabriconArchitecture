---
name: fabricon-architecture
description: Use when working on Microsoft Fabric projects that follow Fabricon patterns, making workspace or environment decisions, organizing notebooks or pipelines, setting up medallion architecture, planning deployment or source control strategy, writing pipeline step code, or choosing between lakehouse and warehouse. Also use when someone references a Fabricon pattern number (1-4, N).
---

# Fabricon Architecture

## Overview

Fabricon is a progressive architectural framework for managing software projects on Microsoft Fabric. It combines data engineering and software engineering best practices into numbered patterns of increasing complexity, plus lettered extensions that apply to any numbered pattern.

Created by the engineering team at Unite Digital LLC.

## When to Use

- Making workspace or environment decisions on Microsoft Fabric
- Organizing notebooks, pipelines, or lakehouses
- Setting up medallion architecture (Bronze/Silver/Gold)
- Planning deployment or source control strategy
- Writing or modifying pipeline step code
- Choosing between lakehouse and warehouse
- Someone says "Fabricon 1", "Fabricon 2N", etc.

## Pattern Progression

| Pattern | Name | When to Use |
|---------|------|-------------|
| **1** | Basic Environment Segregation | Any project needing dev/prod separation |
| **2** | Medallion-Based Environment | Projects needing structured Bronze/Silver/Gold data layers |
| **3** | Large Data Volumes | When duplicating bronze data across envs is impractical |
| **4** | Seamless Reporting | Near real-time reporting from mirrored databases |
| **5** | Realtime Reporting with EventHouse | (Coming soon) |
| **N** | Code Organization Using Notebooks | Extension for any numbered pattern (e.g., "2N") |

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
| Naming convention? | `Domain-Environment[-Layer]` (e.g., `CRM-Dev`, `CRM-Data-Prod`) |

## Fabricon 1: Basic Environment Segregation

One Fabric workspace per environment. For a CRM data product:

- `CRM-Dev` — development and testing
- `CRM-Prod` — production

Each workspace contains all items: lakehouse, data pipeline, notebooks, reports.

## Fabricon 2: Medallion-Based Environment Architecture

Adds Bronze/Silver/Gold lakehouses **within** each workspace (not separate workspaces per layer — that's overkill for most projects).

Each workspace has:
- `CRM-Bronze` lakehouse
- `CRM-Silver` lakehouse
- `CRM-Gold` (or simply `CRM`) lakehouse

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

- **Archive** — items pending deletion
- **Exploration** — research and ad-hoc analysis
- **Pipelines** — main workflow items
- **Reports** — Power BI reports
- **Tests** — pipeline and data validation tests
- Readme notebook at workspace root

### Pipeline Notifications

Send HTML email on pipeline completion with per-step results: step name, start/end times, duration, success/failure, notes. Use Office 365 Connector.

## Fabricon 3: Large Data Volumes

Separates code and data into different workspaces to avoid duplicating large datasets:

- `CRM-Shared` — shared bronze lakehouse with large data
- `CRM-Dev` — code (notebooks, pipelines), linked to `develop` branch
- `CRM-Prod` — code, linked to `main` branch
- `CRM-Data-Dev` — data lakehouses (Bronze, Silver, Gold)
- `CRM-Data-Prod` — data lakehouses

Each `CRM-Bronze` lakehouse uses shortcuts to large tables in `CRM-Bronze-Shared`.

## Fabricon 4: Seamless Reporting with Database Mirroring

Strategy for near real-time reporting from mirrored databases (SQL Server, Cosmos DB, etc.):

1. Mirror operational databases into Fabric
2. Create an intermediary **reporting lakehouse**
3. Bring mirrored tables in via **shortcuts**
4. Add tables to **Default Power BI semantic model**
5. Connect Power BI reports to the semantic model

> Connect Power BI to the intermediary lakehouse, not directly to mirrored databases.

For transformations on mirrored data:
- **SQL Views** — simple but slower (falls back to DirectQuery)
- **Traditional ETL** — when view performance is unacceptable

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

- `00 - Main` — Fabric Data Pipeline orchestrating tier notebooks
- `01 - Bronze.Notebook` — all ingestion steps
- `02 - Silver.Notebook` — all transformation steps
- `03 - Gold.Notebook` — all aggregation/metric steps

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

Post-deployment notebook uses `notebookutils.notebook.updateDefinition()` to repoint notebooks to correct lakehouse per environment. `Common` notebook detects current workspace ID and sets `DATA_WORKSPACE_ID` accordingly.

```python
# Common notebook pattern
if currentWorkspaceId == PROD_WORKSPACE_ID:
    dataWorkspaceId = DATA_PROD_WORKSPACE_ID
else:  # Fallback to DEV — enables feature workspaces without code changes
    dataWorkspaceId = DATA_DEV_WORKSPACE_ID
```

### Unit Testing

Each notebook with functionality should have a corresponding test notebook. Same notebook code runs in both tests and pipeline.

### Automated Documentation

- GitHub: Use nbdev to generate GitHub Pages from notebooks
- Azure DevOps: Use nbdev's `showdoc` function for in-notebook documentation

### Code Formatting

Use jupyter-black extension for automatic Python formatting in notebooks.
