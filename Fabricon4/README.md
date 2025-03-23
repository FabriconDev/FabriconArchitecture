# Fabricon 4: Seamless Reporting with Database Mirroring

> Fabricon 4 builds on the CRM examples from [Fabricon 1](../Fabricon1/README.md), [Fabricon 2](../Fabricon2/README.md), and [Fabricon 3](../Fabricon3/README.md).

## What is Database Mirroring?

Database mirroring is a feature of Microsoft Fabric that continuously replicates data from your operational database into Fabric OneLake.

> Read more about [mirroring on Microsoft Learn](https://learn.microsoft.com/en-us/fabric/database/mirrored-database/overview).

## Power BI Reports with Mirrored Databases

Fabricon 4 provides a strategy for setting up near real-time reporting that can be applied to most mirrored databases.

We will build a Power BI report powered by SQL Server and Cosmos mirrored databases.

Assume a SQL database with the following tables is mirrored into Fabric:

1. `dbo.Customer`
2. `dbo.Product`
3. `dbo.Order`

Assume a Cosmos DB with the following table is mirrored into Fabric:

1. `ProductOffers`

The goal is to combine data from all four tables to generate reports that do not depend on a traditional ETL cycle.

> Fabricon 4 recommends connecting Power BI reports with an intermediary lakehouse instead of the mirrored database.

### Combining Various Data Sources into a Lakehouse

Fabricon 4 recommends creating a lakehouse for reporting, where mirrored tables are brought in via [shortcuts](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-shortcuts).

> At the time of writing, all mirrored database offerings are in preview. They are read-only and do not natively support data transformations.

The tables (shortcuts or otherwise) in the reporting lakehouse can then be added to a [Default Power BI semantic model](https://learn.microsoft.com/en-us/fabric/data-warehouse/semantic-models). This approach enables a Power BI report to seamlessly connect to data from multiple sources (mirrored or otherwise).

In our example, the Power BI report can connect to data from all four mirrored tables, which will always be in sync, thus eliminating the need for a traditional ETL cycle.

### Transforming Data From Mirrored Tables

There are situations that require transforming data from its state in the mirrored table. These may include:

* Changing the data type to a [Delta Lake](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-and-delta-tables) type.
* Selecting relevant columns in a multi-model Cosmos DB container.

> Cosmos DB mirror tables mirror all columns/properties as strings. Intelligent date-based grouping (e.g., 2024-11-01 to Nov 2024) in Power BI only works if the date column is of the date type.

There are two ways to handle data transformations:

#### 1. Use SQL Views

SQL views can be created on a lakehouse table to transform data as needed, but at a significant performance cost due to fallback to [DirectQuery mode](https://learn.microsoft.com/en-us/fabric/data-warehouse/semantic-models#direct-lake-mode). In some cases, the slowdown may be acceptable.

#### 2. Implement Traditional ETL

Implementing a traditional ETL goes against the idea of mirroring but may be the only option if the performance of SQL views is not acceptable. With this approach, new tables are created in the reporting lakehouse and included in the default Power BI semantic model.

[Fabricon 5: Realtime Reporting with EventHouse](../Fabricon5/README.md) may be an alternative option.
