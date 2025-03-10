# Fabricon 2: Medallion-Based Environment Architecture

> Fabricon 2 builds on what is presented in [Fabricon 1](../Fabricon1/README.md).

The [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture) is a data processing architecture commonly used in data engineering to structure and refine data as it progresses through various stages of quality and usability.

Microsoft [recommends that you create each lakehouse in its own, separate Fabric workspace](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture#deployment-model). Based on this recommendation that workspaces may look like:

- `CRM-Dev-Bronze`
- `CRM-Dev-Silver`
- `CRM-Dev-Gold`
- `CRM-Prod-Bronze`
- `CRM-Prod-Silver`
- `CRM-Prod-Gold`

Nine workspaces for just two environments may be an overkill for most projects, therefore Fabricon recommends following workspaces:

- `CRM-Dev`
- `CRM-Prod`

Each workspace has

- `CRM-Bronze` lakehouse
- `CRM-Silver` lakehouse
- `CRM-Gold` (or simply `CRM`) lakehouse/warehouse
- Data pipelines, if any
- Notebooks, if any

This approach allows teams to run their entire Medallion architecture workflows in lower environments without impacting production environment.

## Lakehouse vs Warehouse

Another questions that teams run into is whether to choose a lakehouse or a warehouse for Medallion gold layer. Based on guidance from [Microsoft Fabric decision guide: Choose between Warehouse and Lakehouse](https://learn.microsoft.com/en-us/fabric/get-started/decision-guide-lakehouse-warehouse) we opted to use warehouse for gold layer and learned few things:

1. Warehouse requires upfront schema and table creation.
2. To maintain warehouse, teams need to use [Visual Studio database project](https://learn.microsoft.com/en-us/fabric/data-warehouse/source-control) that adds complexity to automated deployments.
3. Query performance of lakehouse table is comparable to warehouse table.
4. [Entity Framework Core](https://learn.microsoft.com/en-us/ef/core/) works well with both the warehouse and the lakehouse.

As a result, we opted to use lakehouse for the flexibility if offers over the warehouse. 
> Fabricon recommends that if you do not have an explicit need to use warehouse then use lakehouse instead.

## Lakehouse Schema

Introduction of [lakehouse schema](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-schemas) can help simplify the Medallion architecture implementation.

Let's assume bronze layer lakehouse has following tables:

1. `dbo.Customer`
2. `dbo.Product`
3. `dbo.Order`

> Notebook can only connect to one lakehouse at a time referred to as default lakehouse.

Let's assume that on silver layer you need to create a flat table that contains elements from all 3 tables above. On silver lakehouse, [shortcuts](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-shortcuts) can used to get access to bronze tables:

1. `Bronze.Customer` shortcut points to `dbo.Customer`
2. `Bronze.Product` shortcut points to `dbo.Product`
3. `Bronze.Order` shortcut points to `dbo.Order`

The above tables can be easily used in a Spark notebook to read data from bronze layer and write to `dbo.CustomerOrder` table on silver layer.

> Fabricon recommends that `dbo` schema is used represent current Medallion layer and named schema (`Bronze` and `Silver`) are used to represent bronze and silver layer.

Similarly, on gold Medallion layer the lakehouse can have following schema:

1. `dbo` to represent gold layer
2. `Silver` to represent silver layer

This approach enables access to multiple Medallion layers within the constraint of having only one lakehouse available in session context, with clear distinction of layer via schema.

## Source Control

For the CRM example, Fabricon suggest following branching strategy:

- `main` branch linked with `CRM-Prod` workspace
- `develop` branch linked with `CRM-Dev` workspace
- `Branch out to new workspace` feature is used to create a new workspace from `CRM-Dev`. This will create new workspace linked to new feature branch.
- Use pull request to merge feature branch in `develop` branch. This will promote code to `CRM-Dev` workspace.
- Use pull request to merge `develop` branch in `main` branch. This will promote code to `CRM-Prod` workspace.

![Fabric - Branch out to new workspace](../Images/git-branch-to-new-workspace.png)

## Folder Structure

Fabricon recommends following folder structure:

- **Archive**: Folder to keep archived items before they are deleted.
- **Exploration**: Folder to keep items used for research purposes.
- **Pipelines**: Folder to keep items related to the main workflow. Pipeline orchestrator (data pipeline or notebook) should be named `00 - Main`. You may choose to have numeric prefix for each pipeline step or use [Fabricon N](../FabriconN/README.md) approach.
- **Reports**: Folder to keep Power BI reports.
- **Tests**: Folder to keep items that test pipelines.

Readme notebook should be on the root of each workspace that has necessary information.

![Recommended folder structure](../Images/folder-structure-simple.png)