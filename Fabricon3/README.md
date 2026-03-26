# Fabricon 3: Medallion-Based Environment Architecture for Large Data Volumes

> Fabricon 3 builds on concepts introduced in [Fabricon 1](../Fabricon1/README.md) and [Fabricon 2](../Fabricon2/README.md).

Projects dealing with large volumes of data require strategies to minimize data duplication. Fabricon 3 recommends separating code (e.g., notebooks, data pipelines) and data (e.g., lakehouses, warehouses) into distinct workspaces.

Using the CRM example, the recommended workspaces are:

- `CRM-Shared`
- `CRM-Dev`
- `CRM-Prod`
- `CRM-Data-Dev`
- `CRM-Data-Prod`

> Refer to [Fabricon 2 - Source Control](../Fabricon2/README.md#source-control) for Git integration recommendations.

## CRM-Shared Workspace

This workspace contains all shared items including a shared bronze lakehouse `CRMBronzeShared` with large volume of data. Source control is not required in most case.

> Lakehouse names do not support dashes. Use PascalCase (e.g., CRMBronze). For the Gold layer, both CRM and CRMGold are valid since Gold is the externally facing layer.

## CRM-Dev Workspace

This workspace contains all code-related items, such as notebooks and data pipelines. It is linked to the `develop` branch.

## CRM-Prod Workspace

This workspace contains all code-related items, such as notebooks and data pipelines. It is linked to the `main` branch.

## CRM-Data-Dev & CRM-Data-Prod Workspaces

These workspaces contain all data-related items, such as lakehouses, warehouses, and eventhouses. Source control is generally not required.

Each workspace includes:

- `CRMBronze` lakehouse
- `CRMSilver` lakehouse
- `CRMGold` (or simply `CRM`) lakehouse/warehouse

Each `CRMBronze` lakehouse uses [shortcuts](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-shortcuts) to link to large tables/files from `CRMBronzeShared` in `CRM-Shared` workspace.

This approach enables full environment segregation without having to duplicate large volume of data.

## What Fabricon 3 Solves

| Problem | Solution |
| --- | --- |
| Large bronze datasets duplicated across Dev and Prod | Shared workspace (`CRM-Shared`) with shortcuts to `CRMBronzeShared` data |
| Source control mixed with data items | Separate code workspaces (Git-controlled) from data workspaces |
| Code changes risk impacting production data | Code and data workspaces are independent, so code promotion does not touch data |
| Feature branches create full copies of large datasets | Feature workspaces link to same data workspace via `DATA_WORKSPACE_ID` |

## References

- [Lakehouse Shortcuts](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-shortcuts)
- [OneLake Shortcuts](https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts)
- [Git Integration in Fabric](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/intro-to-git-integration)
- [Best Practices for Lifecycle Management in Fabric](https://learn.microsoft.com/en-us/fabric/cicd/best-practices-cicd)
