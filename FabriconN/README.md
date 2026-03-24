# Fabricon N: Code Organization Using Notebooks

> Fabricon N is an extension that can used with either [Fabricon 1](../Fabricon1/README.md), [Fabricon 2](../Fabricon2/README.md) or [Fabricon 3](../Fabricon3/README.md). Use of Fabricon 1 with Fabricon N extension may be referred to as Fabricon 1N and so on.

Traditionally, notebooks are used to different steps in a ETL pipeline where generally a notebook cell represents a step in the pipeline. These notebooks run top to bottom like a script.

> Fabricon recommends using classes to organize the code and abstract classes to enforce contract.

Fabricon recommends using classes to organize the code in a way that ensure consistency and enhances testability of the code. Use of abstract class is encouraged to establish a contract for all pipeline steps. In most cases, pipeline steps read data from a source, perform transformation and save to a lakehouse. A sample abstract is listed below that can be used to enforce common contract on all pipeline steps.

## 1. Pipeline Result Tracking

Fabricon recommends defining a `PipelineResult` class that captures execution details for each step. A sample is listed below:

```python
# PipelineStepBase

from datetime import datetime

class PipelineResult:
    def __init__(self, step_name: str):
        self.step_name:str = step_name
        self.is_success:bool = False
        self.message:str = None
        self.start_time:datetime = None
        self.end_time:datetime = None
        self.exception:Exception = None

    def __str__(self):
        return f"step_name: {self.step_name}, is_success: {self.is_success}, message: {self.message}, execution_time: {self.end_time - self.start_time}"

    def start(self):
        self.start_time = datetime.now()

    def complete(self, success: bool, message: str, exception: Exception = None):
        self.end_time = datetime.now()
        self.message = message
        self.is_success = success
        self.exception = exception
```

A `PipelineResultList` class can be used to aggregate results across pipeline steps:

```python
class PipelineResultList:
    def __init__(self):
        self._results = []

    def add(self, result):
        if not isinstance(result, PipelineResult):
            raise TypeError("Only PipelineResult objects can be added.")
        self._results.append(result)

    def __iter__(self):
        return iter(self._results)

    def __len__(self):
        return len(self._results)
```

## 2. Pipeline Step Contract

With `PipelineResult` in place, the abstract class can be updated to use it as the return type for `run()`. A sample abstract class is listed below that can be used to enforce common contract on all pipeline steps.

```python
from abc import ABC, abstractmethod
from pyspark.sql import DataFrame


class PipelineStepBase(ABC):
    """Abstract Base class for all pipeline classes"""

    @abstractmethod
    def _get_data(self) -> DataFrame:  # A `DataFrame` containing the query results
        """Method to get data needed to run this pipeline step"""
        pass

    @abstractmethod
    def _write_to_lakehouse(
        self, df: DataFrame  # A `DataFrame` containing the query results
    ):
        """Method to write data from this pipeline step to lakehouse"""
        pass

    @abstractmethod
    def run(self) -> PipelineResult:
        """Method to run the pipeline step"""
        pass

```

Simple implementation of a pipeline step may look like below:

```python
# CrmCustomerPipelineStep

class CrmCustomerPipelineStep(PipelineStepBase):
    def __init__(self, spark):
        self.spark = spark

    def _get_data(self) -> DataFrame:
        # Code to fetch customer data.
        return data_df

    def _write_to_lakehouse(self, df):
        # Code to write dataframe to lakehouse as delta table.
        pass

    def run(self) -> PipelineResult:
        result = PipelineResult("CrmCustomerPipelineStep")
        result.start()
        try:
            df = self._get_data()
            self._write_to_lakehouse(df)
            result.complete(True, f"Processed {df.count()} records")
        except Exception as ex:
            result.complete(False, str(ex), ex)
            raise ex
        finally:
            return result
```

### Development Mode

> Fabricon recommends using an environment variable to distinguish between pipeline execution and individual notebook development/testing.

Each pipeline step notebook should include a test block at the bottom that only runs when the notebook is executed directly (not as part of a pipeline):

```python
if __name__ == "__main__" and os.getenv("PIPELINE_RUN") != "True":
    step = CrmCustomerPipelineStep(spark)
    result = step.run()
    print(result)
```

The orchestrator notebooks set this flag before running steps:

```python
os.environ["PIPELINE_RUN"] = "True"
```

## 3. Tiered Orchestration

> Fabricon recommends using a `00 - Main` Data Pipeline to orchestrate Medallion tier notebooks in order.

The `00 - Main` is a Fabric Data Pipeline that runs Bronze, Silver, and Gold tier notebooks sequentially:

- `00 - Main` - Fabric Data Pipeline that orchestrates the tier notebooks
- `01 - Bronze.Notebook` - Runs all bronze (ingestion) steps
- `02 - Silver.Notebook` - Runs all silver (transformation) steps
- `03 - Gold.Notebook` - Runs all gold (aggregation/metric) steps

This separation allows each tier to:

- Have its own timeout and retry settings
- Report success/failure independently
- Be re-run individually without re-running the entire pipeline

> Fabric has a limit on notebook reference chain depth. When `00 - Main` calls a tier notebook (e.g., `01 - Bronze`), which uses `%run` to import `PipelineStepBase`, which in turn uses `%run Common`, the chain can exceed the allowed depth - especially when pipeline steps import additional notebooks. If you hit this limit, a practical workaround is to schedule each tier notebook (`01 - Bronze`, `02 - Silver`, `03 - Gold`) independently instead of chaining them through `00 - Main`.

Each tier notebook follows this pattern:

```python
# Setup
%run Common
```

```python
os.environ["PIPELINE_RUN"] = "True"
```

```python
from datetime import datetime

start_time = datetime.now()
```

```python
# Import pipeline steps
%run CrmCustomerPipelineStep
%run CrmProductPipelineStep
```

```python
try:
    result_list = PipelineResultList()
    status = "Success"

    pipeline_steps = [
        CrmCustomerPipelineStep(spark),
        CrmProductPipelineStep(spark),
    ]

    for step in pipeline_steps:
        result = step.run()
        result_list.add(result)

        if not result.is_success:
            raise result.exception

except Exception as ex:
    status = "Error"
    # Handle error (send notification, log, etc.)
finally:
    # Send email notification with result_list
    pass
```

> With this approach, adding numeric prefix to each pipeline step is not needed and the order of execution of steps can be easily changed within the orchestrator.

## 4. Data Access Abstraction

> Fabricon recommends abstracting data access into a shared service to ensure consistency across pipeline steps.

Instead of each pipeline step writing its own data access logic, Fabricon recommends creating a shared data access service (via a [Python wheel package](#6-code-reusability-using-python-wheel-packages)) with common operations. A sample is listed below:

```python
class LakeHouseDataService:
    def __init__(self, spark, notebookutils, delta_table):
        self.spark = spark
        self.notebookutils = notebookutils
        self.delta_table = delta_table

    def execute_query(self, sql: str) -> DataFrame:
        # Execute a SQL query and return results as DataFrame.
        return self.spark.sql(sql)

    def execute_scalar(self, sql: str, column: str, default=None):
        # Execute a SQL query and return a single scalar value.
        result = self.spark.sql(sql).collect()
        if result and result[0][column] is not None:
            return result[0][column]
        return default

    def upsert(self, df: DataFrame, table: str, merge_condition: str, update_columns: list = None):
        # Perform a Delta Lake MERGE (upsert) operation.
        pass

    def replace(self, df: DataFrame, table: str):
        # Replace all data in a table.
        df.write.mode("overwrite").format("delta").saveAsTable(table)

    def read_json_file(self, path: str, schema) -> DataFrame:
        # Read a JSON file from lakehouse Files.
        return self.spark.read.schema(schema).json(path)

    def read_csv_file(self, path: str, schema) -> DataFrame:
        # Read a CSV file from lakehouse Files.
        return self.spark.read.schema(schema).csv(path, header=True)
```

Usage in a pipeline step may look like below:

```python
class CrmCustomerPipelineStep(PipelineStepBase):
    def __init__(self, spark):
        self.spark = spark
        self.data_service = LakeHouseDataService(spark, notebookutils, DeltaTable)

    def _get_data(self):
        return self.data_service.execute_query("SELECT * FROM Bronze.Customer")

    def _write_to_lakehouse(self, df):
        self.data_service.upsert(df, "dbo.Customer", "existing.Id = updates.Id")
```

## 5. Incremental Processing

Full reprocessing of data is impractical for growing datasets. Fabricon recommends incremental processing where each pipeline step tracks the maximum date already processed and only fetches new data. A sample is listed below:

```python
def _get_data(self):
    max_date = self.data_service.execute_scalar(
        "SELECT MAX(Date) AS MaxDate FROM dbo.CustomerMetric",
        "MaxDate",
        CRM_START_DATE  # Fallback for first run
    )

    return self.data_service.execute_query(f"""
        SELECT * FROM Bronze.CustomerEvent
        WHERE Date >= '{max_date}'
    """)

def _write_to_lakehouse(self, df):
    self.data_service.upsert(
        df, "dbo.CustomerMetric",
        "existing.CustomerId = updates.CustomerId AND existing.Date = updates.Date"
    )
```

Use `upsert` (Delta MERGE) for incremental updates and `replace` (overwrite) for reference data that should be fully refreshed.

## 6. Code Reusability Using Python Wheel Packages

Magic command `run` is limited to running notebooks in current workspace. `notebookutils` has a function that can [run a notebook from any workspace](https://learn.microsoft.com/en-us/fabric/data-engineering/notebook-utilities#reference-a-notebook), but the content of notebook are not brought into the current context.

Using [Python Binary Distribution Format](https://packaging.python.org/en/latest/specifications/binary-distribution-format/) teams can easily package shared code that can easily consumed in any notebook.

> Fabricon recommends using inline package install instead of creating custom Spark environment. Custom Spark environment take longer to start and harder to maintain.

Creating custom Spark environment with all custom libraries is a good way to hide complexity from the users, but it increases session start time from 3-10 seconds to 50-120 seconds.

An alternate approach is to publish your wheel package to a blob store and use `%pip install https://yourblobstore.com/youpythonpackage.whl?accesstoken` to load the package where needed.

Good candidates for packaging as a wheel include data access service (e.g., `LakeHouseDataService`), logger and email sender.

## 7. Unit Testing

There are many good unit testing strategies and frameworks available for Python. Fabricon recommends that each notebook containing functionality is also used in a test notebook that verifies quality. The same notebook code that runs in tests is then run during use in the pipeline.

![Diagram showing unit testing strategy](../Images/unit-testing.png)

Fabricon distinguishes between two categories of test notebooks, both housed in the `Tests/` folder:

### Integration Tests (LakeHouseDataServiceTests)

`LakeHouseDataServiceTests` exercises real lakehouse operations against an actual lakehouse. These tests verify that `LakeHouseDataService` methods such as `upsert`, `replace`, `execute_query`, and `execute_scalar` work correctly end-to-end with live Delta tables. Because they require a connected lakehouse, they are run in the Fabric workspace rather than locally.

### Logic Tests (BronzeTests, SilverTests, GoldTests)

Per-tier test notebooks (`BronzeTests`, `SilverTests`, `GoldTests`) validate transformation logic using mocked data. The data service is replaced with a mock or an in-memory Spark DataFrame so that tests do not depend on a live lakehouse. This allows the full pipeline step logic including `_get_data()`, `_write_to_lakehouse()`, and `run()` to be exercised in isolation.

Example pattern for a mocked pipeline step test:

```python
# BronzeTests

%run ../Pipeline/CrmCustomerPipelineStep

class MockDataService:
    def execute_query(self, sql):
        return spark.createDataFrame([{"Id": 1, "Name": "Test"}])

    def upsert(self, df, table, condition):
        self._last_written = df

mock_service = MockDataService()
step = CrmCustomerPipelineStep(spark)
step.data_service = mock_service

result = step.run()
assert result.is_success, f"Step failed: {result.message}"
assert mock_service._last_written.count() == 1
print("BronzeTests passed")
```

## 8. Automated Documentation

Teams using [GitHub](https://github.com) can make use of [nbdev](https://nbdev.fast.ai) to automatically generate documentation from code as [GitHub Pages](https://pages.github.com).

Teams using [Azure DevOps](https://dev.azure.com) can use `showdoc` function from [nbdev](https://nbdev.fast.ai) to automatically generate documentation in notebooks like shown below:

![Sample automatically generated documentation](../Images/automated-documentation.png)

## 9. Code Formatting

Fabricon recommends using [jupyter-black](https://pypi.org/project/jupyter-black) extension to automatically format Python code in notebooks.

## 10. Deployment

Microsoft Fabric offers two ways to promote code from one environment to another.

1. [Fabric Deployment Pipelines](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/intro-to-deployment-pipelines?tabs=new)
2. [Fabric Git Integration](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/intro-to-git-integration?tabs=azure-devops)

> See [Fabricon 2 - Source Control](../Fabricon2/README.md#source-control) for recommendations on Git integration.

In context of Fabricon N, the main challenge is how to change default lakehouse for notebooks so they are linked to correct lakehouse when code is promoted to one environment to another.

At the time of writing, Fabric deployment pipelines support this via [Deployment Rules](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/create-rules?tabs=new), but it is manual and impractical for bigger projects.

At the time of writing, Fabric Git integration does not support updating default lakehouse on notebooks. Fabricon recommends using a post deployment notebook that programmatically updates default lakehouse on notebooks with code.

[`notebookutils`](https://learn.microsoft.com/en-us/fabric/data-engineering/notebook-utilities#updating-a-notebook) can be used to change default lakehouse on notebooks.

```python
notebookutils.notebook.updateDefinition(
        name=notebook_name,
        defaultLakehouse=lakehouse_name,
        defaultLakehouseWorkspace=workspace_id
    )
```

> Remember, the notebook running `updateDefinition` function cannot update itself.

Fabricon recommends having a notebook for environment variables and another notebook to run post deployment updates to point the notebooks containing code to correct lakehouse.

Following code shows contents of `PostDeployment` notebook:

```python
# Environment variables are defined in Common.
%run Common
```

```python
from notebookutils import notebook
from concurrent.futures import ThreadPoolExecutor
import os
import json

if os.getenv("DATA_WORKSPACE_ID") == None:
    notebookutils.notebook.exit("`DATA_WORKSPACE_ID` is not defined")

# Function to update notebook definition
def update_notebook(notebook_item):
    notebook_name = notebook_item['displayName']
    notebook_lakehouse_name = json.loads(notebookutils.notebook.getDefinition(nb["displayName"]))["metadata"]["dependencies"]["lakehouse"]["default_lakehouse_name"]

    # Skip if the notebook name is "DevOps"
    if notebook_name == "DevOps":
        print(f"Skipping notebook '{notebook_name}'")
        return

    notebook.updateDefinition(
        name=notebook_name,
        defaultLakehouse=notebook_lakehouse_name,
        defaultLakehouseWorkspace=os.getenv("DATA_WORKSPACE_ID")
    )
    print(f"Updated notebook definition for '{notebook_name}'")

# Get the list of notebooks
notebook_list = notebookutils.notebook.list()

# Run updates in parallel
with ThreadPoolExecutor() as executor:
    executor.map(update_notebook, notebook_list)
```

Following code shows contents of `Common` notebook:

> **Setup prerequisite:** Before running pipelines, create a Config Variable Library in both Dev and Prod workspaces with `DATA_ENVIRONMENT` and `DATA_WORKSPACE_ID` keys.

```python
import os

# Read environment configuration from Variable Library
DATA_ENVIRONMENT = notebookutils.credentials.getSecret("Config", "DATA_ENVIRONMENT")
DATA_WORKSPACE_ID = notebookutils.credentials.getSecret("Config", "DATA_WORKSPACE_ID")

os.environ["DATA_ENVIRONMENT"] = DATA_ENVIRONMENT
os.environ["DATA_WORKSPACE_ID"] = DATA_WORKSPACE_ID
```

> [Fabricon 3](../Fabricon3/README.md) explains the reason for having code and data in separate workspaces.

The current workspace will have uncommitted changes that one may or may not want to push back to Git.

- Pushing the changes back to Git has the risk of conflicts next time a PR is completed into the branch associated with the current workspace.
- Otherwise there will be uncommitted changes left on your workspace which isn't optimal either.

## 11. Shortcut Provisioning

> Fabricon recommends automating shortcut creation in each tier notebook rather than creating shortcuts manually.

In [Fabricon 2](../Fabricon2/README.md#lakehouse-schema) and [Fabricon 3](../Fabricon3/README.md), cross-lakehouse shortcuts are used to enable multi-layer access within the one-lakehouse-per-session constraint. For example, the Gold lakehouse uses `Bronze.*` and `Silver.*` schemas that are shortcuts to tables in the Bronze and Silver lakehouses.

Manually creating and maintaining these shortcuts across environments is error-prone and does not scale.

### Key Insight

OneLake shortcuts are pointers to storage paths, not references to live table objects. **Shortcuts can be created before the source tables exist.** When notebooks later populate Bronze and Silver tables, shortcuts automatically resolve.

### Where to Place Shortcut Provisioning

Shortcut provisioning belongs in the **tier notebooks** (`02 - Silver.Notebook`, `03 - Gold.Notebook`), not the DevOps notebook. This is because:

1. **Each tier notebook has its default lakehouse connected**, so shortcuts are created in the correct lakehouse. Silver's notebook creates shortcuts in CRMSilver, and Gold's notebook creates shortcuts in CRMGold.
2. **The DevOps notebook has no lakehouse connected** and cannot create shortcuts since it has no default lakehouse (its job is to rebind other notebooks' lakehouses).
3. **Shortcuts are idempotent** and safe to run every pipeline execution, not just during deployment.

### Provisioning Sequence

1. Lakehouses pre-exist in the Data workspace (created manually or via deployment pipeline)
2. Tier notebooks create shortcuts before running pipeline steps (pointing to paths that may be empty on first run)
3. Pipeline steps populate tables
4. Shortcuts automatically resolve, and tables appear via `Bronze.*` and `Silver.*` schemas

### Implementation

Each tier notebook adds a "Shortcut Provisioning" section after setup and before pipeline steps. Use [`LakeHouseDataService.table_exists()`](../Basics/README.md) to check if a shortcut already exists, the Fabric REST API to create shortcuts, and [`sempy.fabric`](https://learn.microsoft.com/en-us/python/api/semantic-link-sempy/sempy.fabric) to resolve source lakehouse IDs by name.

> **Note:** `notebookutils.lakehouse.createShortcut()` is broken. Use the shared `create_shortcut()` function below, which is defined in `Common.Notebook` and calls the Fabric REST API directly.

The following `create_shortcut()` function lives in `Common.Notebook` and is available to all tier notebooks via `%run Common`:

```python
import requests

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

    # 409 Conflict means the shortcut already exists; treat as success
    if response.status_code == 409:
        return

    if not response.ok:
        raise RuntimeError(
            f"Shortcut '{shortcut_name}' creation failed ({response.status_code}): {response.text}"
        )
```

**Silver notebook** creates Bronze schema shortcuts:

```python
import os
import sempy.fabric as fabric
from unite_digital.lakehouse_data_service import LakeHouseDataService

data_workspace_id = os.getenv("DATA_WORKSPACE_ID")
if data_workspace_id is None:
    raise ValueError("`DATA_WORKSPACE_ID` environment variable is not defined")

data_service = LakeHouseDataService(spark, notebookutils, DeltaTable)

lakehouses = fabric.list_items(type="Lakehouse", workspace=data_workspace_id)
bronze_lakehouse_id = lakehouses[lakehouses["Display Name"] == "CRMBronze"]["Id"].values[0]

bronze_shortcuts = {
    "Customer": "/Tables/dbo/Customer",
    "Product":  "/Tables/dbo/Product",
    "Order":    "/Tables/dbo/Order",
}

for name, path in bronze_shortcuts.items():
    create_shortcut(
        shortcut_name=f"Bronze.{name}",
        shortcut_path="/Tables/Bronze",
        target_lakehouse_id=bronze_lakehouse_id,
        target_workspace_id=data_workspace_id,
        target_path=path
    )
    print(f"Provisioned shortcut Bronze.{name}")
```

**Gold notebook** creates both Bronze and Silver schema shortcuts:

```python
import os
import sempy.fabric as fabric
from unite_digital.lakehouse_data_service import LakeHouseDataService

data_workspace_id = os.getenv("DATA_WORKSPACE_ID")
if data_workspace_id is None:
    raise ValueError("`DATA_WORKSPACE_ID` environment variable is not defined")

data_service = LakeHouseDataService(spark, notebookutils, DeltaTable)

lakehouses = fabric.list_items(type="Lakehouse", workspace=data_workspace_id)
bronze_lakehouse_id = lakehouses[lakehouses["Display Name"] == "CRMBronze"]["Id"].values[0]
silver_lakehouse_id = lakehouses[lakehouses["Display Name"] == "CRMSilver"]["Id"].values[0]

bronze_shortcuts = {
    "Customer": "/Tables/dbo/Customer",
    "Product":  "/Tables/dbo/Product",
}

silver_shortcuts = {
    "CustomerOrder": "/Tables/dbo/CustomerOrder",
}

for name, path in bronze_shortcuts.items():
    create_shortcut(
        shortcut_name=f"Bronze.{name}",
        shortcut_path="/Tables/Bronze",
        target_lakehouse_id=bronze_lakehouse_id,
        target_workspace_id=data_workspace_id,
        target_path=path
    )
    print(f"Provisioned shortcut Bronze.{name}")

for name, path in silver_shortcuts.items():
    create_shortcut(
        shortcut_name=f"Silver.{name}",
        shortcut_path="/Tables/Silver",
        target_lakehouse_id=silver_lakehouse_id,
        target_workspace_id=data_workspace_id,
        target_path=path
    )
    print(f"Provisioned shortcut Silver.{name}")
```

### Best Practices

- **Idempotent**: Use `LakeHouseDataService.table_exists()` to check before creating. Safe to re-run every pipeline execution.
- **Manifest-driven**: Define all shortcuts in a dictionary. Easy to review and update when new tables are added.
- **Environment-agnostic**: Use `DATA_WORKSPACE_ID` to target the correct workspace. The same code works in Dev and Prod.
- **Fail fast**: Raise `ValueError` if `DATA_WORKSPACE_ID` is not defined.

### Environment-Specific Shortcut Targets

For shortcuts that need to point to different external sources per environment (e.g., an Amazon S3 folder in development vs. Azure Data Lake Storage in production), use [Fabric Variable Libraries](https://learn.microsoft.com/en-us/fabric/cicd/variable-library/variable-library-overview).

> Variable Libraries are supported in Lakehouse shortcuts, Data Pipelines, and Notebooks. For cross-lakehouse shortcuts within the same workspace, Variable Libraries are not needed.

### Shortcut Structure in Gold Lakehouse

> Lakehouse names do not support dashes. Use PascalCase (e.g., CRMBronze). For the Gold layer, both `CRM` and `CRMGold` are valid since Gold is the externally facing layer.

```text
Gold Lakehouse (e.g., CRMGold)
├── Tables/
│   ├── dbo.*          (native Gold layer tables)
│   ├── Bronze.*       (shortcuts to CRMBronze lakehouse dbo.* tables)
│   └── Silver.*       (shortcuts to CRMSilver lakehouse dbo.* tables)
└── Files/
```

## 12. Folder Structure

Fabricon recommends organizing workspace items into folders using a standard layout. This makes it easy to navigate workspaces of any size.

```text
Archive/          - Retired or deprecated items kept for reference
Configuration/    - Variable Libraries and environment configuration items
Exploration/      - Ad-hoc analysis and investigative notebooks
Pipeline/         - Orchestration notebooks (Main, Bronze, Silver, Gold) and pipeline step notebooks
Reports/          - Power BI reports and semantic models
Tests/            - Test notebooks (LakeHouseDataServiceTests, BronzeTests, SilverTests, GoldTests)
Readme            - The workspace readme notebook
```

> The folder name `Pipeline` is singular. Avoid `Pipelines` (plural).

## What Fabricon N Solves

| Problem | Solution |
| --- | --- |
| Notebooks run as unstructured scripts with no consistency | Abstract base class enforces `_get_data` / `_write_to_lakehouse` / `run` contract |
| No visibility into which pipeline steps succeeded or failed | `PipelineResult` and `PipelineResultList` capture per-step execution details |
| Flat notebook execution with no tier isolation | Tiered orchestration: Main → Bronze → Silver → Gold with independent timeout/retry |
| Duplicated data access code across notebooks | `LakeHouseDataService` wheel package shared across all steps |
| Full data reload on every pipeline run | Incremental processing via max-date tracking + Delta MERGE upsert |
| Custom Spark environments slow session startup to 50-120s | Python wheel packages keep session start at 3-10s |
| Manual notebook lakehouse rebinding after promotion | DevOps notebook automates rebinding via `notebookutils.notebook.updateDefinition()` |
| Manual shortcut creation across environments | Tier notebooks auto-provision shortcuts using `table_exists()` check |
| No automated testing of notebook code | Unit test notebooks run same code as pipeline steps |

## References

- [Fabric Notebook Utilities](https://learn.microsoft.com/en-us/fabric/data-engineering/notebook-utilities)
- [Semantic Link (sempy)](https://learn.microsoft.com/en-us/python/api/semantic-link-sempy/sempy.fabric)
- [Delta Lake MERGE](https://docs.delta.io/latest/delta-update.html#upsert-into-a-table-using-merge)
- [Lakehouse Shortcuts](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-shortcuts)
- [OneLake Shortcuts REST API](https://learn.microsoft.com/en-us/rest/api/fabric/core/onelake-shortcuts/create-shortcut)
- [Fabric Variable Libraries](https://learn.microsoft.com/en-us/fabric/cicd/variable-library/variable-library-overview)
- [nbdev - Notebook Documentation](https://nbdev.fast.ai/)
- [jupyter-black - Code Formatting](https://github.com/n8henrie/jupyter-black)
