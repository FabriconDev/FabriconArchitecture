# Fabricon 2: Medallion-Based Environment Architecture

> Fabricon 2 builds on the concepts presented in [Fabricon 1](../Fabricon1/README.md).

The [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture) is a data processing framework commonly used in data engineering to structure and refine data as it progresses through various stages of quality and usability.

Microsoft [recommends creating each lakehouse in its own, separate Fabric workspace](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture#deployment-model). Based on this recommendation, the workspaces might look like:

- `CRM-Dev-Bronze`
- `CRM-Dev-Silver`
- `CRM-Dev-Gold`
- `CRM-Prod-Bronze`
- `CRM-Prod-Silver`
- `CRM-Prod-Gold`

However, nine workspaces for just two environments may be excessive for most projects. Therefore, Fabricon recommends the following workspaces:

- `CRM-Dev`
- `CRM-Prod`

Each workspace includes:

- `CRM-Bronze` lakehouse
- `CRM-Silver` lakehouse
- `CRM-Gold` (or simply `CRM`) lakehouse/warehouse
- Data pipelines, if any
- Notebooks, if any

This approach allows teams to run their entire Medallion architecture workflows in lower environments without impacting the production environment.

## Lakehouse vs Warehouse

Another common question teams face is whether to use a lakehouse or a warehouse for the Medallion gold layer. Based on guidance from [Microsoft Fabric decision guide: Choose between Warehouse and Lakehouse](https://learn.microsoft.com/en-us/fabric/get-started/decision-guide-lakehouse-warehouse), we opted to use a lakehouse for the flexibility it offers over a warehouse. Here are some key considerations:

1. A warehouse requires upfront schema and table creation.
2. Maintaining a warehouse involves using a [Visual Studio database project](https://learn.microsoft.com/en-us/fabric/data-warehouse/source-control), which adds complexity to automated deployments.
3. The query performance of lakehouse tables is comparable to warehouse tables.
4. [Entity Framework Core](https://learn.microsoft.com/en-us/ef/core/) works well with both warehouses and lakehouses.

> Fabricon recommends using a lakehouse unless there is an explicit need for a warehouse.

## Lakehouse Schema

The introduction of [lakehouse schemas](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-schemas) can simplify Medallion architecture implementation.

For example, assume the bronze layer lakehouse has the following tables:

1. `dbo.Customer`
2. `dbo.Product`
3. `dbo.Order`

> A notebook can only connect to one lakehouse at a time, referred to as the default lakehouse.

If the silver layer requires a flat table containing elements from all three tables above, [shortcuts](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-shortcuts) can be used in the silver lakehouse to access the bronze tables:

1. `Bronze.Customer` shortcut points to `dbo.Customer`
2. `Bronze.Product` shortcut points to `dbo.Product`
3. `Bronze.Order` shortcut points to `dbo.Order`

These shortcuts can be used in a Spark notebook to read data from the bronze layer and write to the `dbo.CustomerOrder` table in the silver layer.

> Fabricon recommends using the `dbo` schema to represent the current Medallion layer and named schemas (e.g., `Bronze`, `Silver`) to represent other layers.

Similarly, in the gold Medallion layer, the lakehouse can have the following schemas:

1. `dbo` to represent the gold layer
2. `Silver` to represent the silver layer

This approach enables access to multiple Medallion layers within the constraint of having only one lakehouse available in the session context, with a clear distinction of layers via schemas.

## Source Control

For the CRM example, Fabricon suggests the following branching strategy:

- The `main` branch is linked to the `CRM-Prod` workspace.
- The `develop` branch is linked to the `CRM-Dev` workspace.
- Use the `Branch out to new workspace` feature to create a new workspace from `CRM-Dev`. This will create a new workspace linked to a new feature branch.
- Use a pull request to merge the feature branch into the `develop` branch. This promotes code to the `CRM-Dev` workspace.
- Use a pull request to merge the `develop` branch into the `main` branch. This promotes code to the `CRM-Prod` workspace.

![Fabric - Branch out to new workspace](../Images/git-branch-to-new-workspace.png)

## Folder Structure

Fabricon recommends the following folder structure:

- **Archive**: Folder to store archived items before deletion.
- **Exploration**: Folder to store items used for research purposes.
- **Pipelines**: Folder to store items related to the main workflow. The pipeline orchestrator (data pipeline or notebook) should be named `00 - Main`. You may choose to use a numeric prefix for each pipeline step or adopt the [Fabricon N](../FabriconN/README.md) approach.
- **Reports**: Folder to store Power BI reports.
- **Tests**: Folder to store items that test pipelines.

A readme notebook should be placed at the root of each workspace, containing necessary information.

![Recommended folder structure](../Images/folder-structure-simple.png)