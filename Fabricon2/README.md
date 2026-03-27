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

- `CRMBronze` lakehouse
- `CRMSilver` lakehouse
- `CRMGold` (or simply `CRM`) lakehouse/warehouse
- Data pipelines, if any
- Notebooks, if any

> Lakehouse names do not support dashes. Use PascalCase (e.g., CRMBronze). For the Gold layer, both CRM and CRMGold are valid since Gold is the externally facing layer.

This approach allows teams to run their entire Medallion architecture workflows in lower environments without impacting production environment.

## Lakehouse vs Warehouse

Another common question teams face is whether to use a lakehouse or a warehouse for the Medallion gold layer. Based on guidance from [Microsoft Fabric decision guide: Choose between Warehouse and Lakehouse](https://learn.microsoft.com/en-us/fabric/get-started/decision-guide-lakehouse-warehouse), we opted to use a lakehouse for the flexibility it offers over a warehouse. Here are some key considerations:

1. A warehouse requires upfront schema and table creation.
2. Maintaining a warehouse involves using a [Visual Studio database project](https://learn.microsoft.com/en-us/fabric/data-warehouse/source-control), which adds complexity to automated deployments.
3. The query performance of lakehouse tables is comparable to warehouse tables.
4. [Entity Framework Core](https://learn.microsoft.com/en-us/ef/core/) works well with both warehouses and lakehouses.

As a result, we opted to use lakehouse for the flexibility if offers over the warehouse.
> Fabricon recommends that if you do not have an explicit need to use warehouse then use lakehouse instead.

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

- **Archive**: Folder to keep archived items before they are deleted.
- **Configuration**: Folder to keep shared configuration notebooks (e.g., Common.Notebook, DevOps.Notebook).
- **Exploration**: Folder to keep items used for research purposes.
- **Pipeline**: Folder to keep items related to the main workflow. See [Fabricon N](../FabriconN/README.md) for recommended pipeline orchestration and code organization.
- **Reports**: Folder to keep Power BI reports. See [Fabricon R](../FabriconR/README.md) for guidance on promoting reports across environments. Fabricon R recommends placing reports in Data workspaces instead.
- **Tests**: Folder to keep items that test pipelines.

A readme notebook should be placed at the root of each workspace, containing necessary information.

```text
CRM-Dev / CRM-Prod
├── 📁 Archive
├── 📁 Configuration
├── 📁 Exploration
├── 📁 Pipeline
├── 📁 Reports
├── 📁 Tests
└── 📓 Readme
```

> When using [Fabricon R](../FabriconR/README.md), the Reports folder moves to the Data workspace:

```text
Code Workspace (CRM-Dev / CRM-Prod)
├── 📁 Archive
├── 📁 Configuration
├── 📁 Exploration
├── 📁 Pipeline
├── 📁 Tests
└── 📓 Readme

Data Workspace (CRM-Data-Dev / CRM-Data-Prod)
├── 📁 Reports
├── 🗄️ CRMBronze Lakehouse
├── 🗄️ CRMSilver Lakehouse
└── 🗄️ CRMGold Lakehouse
```

## Pipeline Notifications

> Fabricon recommends sending email notifications on pipeline completion with detailed execution results.

Production pipelines should notify stakeholders of execution outcomes. A common pattern is to generate an HTML email with per-step results including step name, start/end times, duration, success/failure status, and notes.

Teams can use the [Office 365 Connector](https://learn.microsoft.com/en-us/connectors/office365/) or similar service to send these notifications. For a structured approach to capturing per-step results, see [Fabricon N - Pipeline Result Tracking](../FabriconN/README.md#1-pipeline-result-tracking).

## What Fabricon 2 Solves

| Problem | Solution |
| --- | --- |
| Microsoft recommends 9 workspaces for 2 environments, which is overkill for most projects | 2 workspaces with multiple lakehouses per workspace |
| Lakehouse vs warehouse decision | Lakehouse recommended for flexibility, comparable performance, no upfront schema |
| Notebooks can only connect to one lakehouse at a time | Shortcuts + named schemas (`Bronze.*`, `Silver.*`) for cross-layer access |
| No structured data organization across medallion layers | `dbo` schema for current layer, named schemas for other layers |
| No branching strategy for Fabric | `main` ↔ Prod, `develop` ↔ Dev, feature branches via "Branch out to new workspace" |
| No visibility into pipeline execution outcomes | HTML email notifications with per-step results |

## References

- [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)
- [OneLake Medallion Lakehouse Architecture](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture)
- [Decision Guide: Choose Between Warehouse and Lakehouse](https://learn.microsoft.com/en-us/fabric/get-started/decision-guide-lakehouse-warehouse)
- [Lakehouse Schemas](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-schemas)
- [Lakehouse Shortcuts](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-shortcuts)
- [Git Integration in Fabric](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/intro-to-git-integration)
- [Office 365 Connector](https://learn.microsoft.com/en-us/connectors/office365/)
