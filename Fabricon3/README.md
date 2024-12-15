# Fabricon 3: Medallion-Based Environment Architecture for Large Data Volumes

> Fabricon 3 builds on what is presented in [Fabricon 1](../Fabricon1/README.md) and [Fabricon 2](../Fabricon2/README.md).

Projects dealing with large volumes of data demand a strategy that minimizes duplication of data. Fabricon 3 recommends separating code (notebook, data pipeline etc) and data (lakehouse, warehouse etc) into different workspaces.

Building on the CRM example, the workspaces should be:

- `CRM-Shared`
- `CRM-Dev`
- `CRM-Prod`
- `CRM-Data-Dev`
- `CRM-Data-Prod`

> See [Fabricon 2 - Source Control](../Fabricon2/README.md#source-control) for recommendations on Git integration.

## CRM-Shared Workspace

This workspace contains all shared items including a shared bronze lakehouse `CRM-Bronze-Shared` with large volume of data. Source control is not required in most case.

## CRM-Dev Workspace

This workspace contains all the code items that include notebooks, data pipeline etc. Workspace linked to `develop` branch.

## CRM-Prod Workspace

This workspace contains all the code items that include notebooks, data pipeline etc. Workspace linked to `main` branch.

## CRM-Data-Dev & CRM-Data-Prod

These workspaces contains all the data items that include lakehouse, warehouse, eventhouse etc. Source control is not required in most case.

Each workspace has

- `CRM-Bronze` lakehouse
- `CRM-Silver` lakehouse
- `CRM-Gold` (or simply `CRM`) lakehouse/warehouse

Each `CRM-Bronze` lakehouse uses [shortcuts](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-shortcuts) to link to large tables/files from `CRM-Bronze-Shared` in `CRM-Shared` workspace.

This approach enables full environment segregation without having to duplicate large volume of data.