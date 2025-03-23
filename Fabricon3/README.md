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

This workspace contains all shared resources, including a shared bronze lakehouse `CRM-Bronze-Shared` with large volumes of data. Source control is generally not required.

## CRM-Dev Workspace

This workspace contains all code-related items, such as notebooks and data pipelines. It is linked to the `develop` branch.

## CRM-Prod Workspace

This workspace contains all code-related items, such as notebooks and data pipelines. It is linked to the `main` branch.

## CRM-Data-Dev & CRM-Data-Prod Workspaces

These workspaces contain all data-related items, such as lakehouses, warehouses, and eventhouses. Source control is generally not required.

Each workspace includes:

- `CRM-Bronze` lakehouse
- `CRM-Silver` lakehouse
- `CRM-Gold` (or simply `CRM`) lakehouse/warehouse

Each `CRM-Bronze` lakehouse uses [shortcuts](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-shortcuts) to link to large tables/files from the `CRM-Bronze-Shared` lakehouse in the `CRM-Shared` workspace.

This approach enables full environment segregation without duplicating large volumes of data.