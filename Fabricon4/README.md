# Fabricon 4: Seamless Reporting with Database Mirroring

> Fabricon 4 builds on the CRM example from [Fabricon 1](../Fabricon1/README.md), [Fabricon 2](../Fabricon2/README.md) and [Fabricon 3](../Fabricon3/README.md).

## What is Database Mirroring?

Database mirroring is a feature of Microsoft Fabric to continuously replicate data from your operational database into Fabric OneLake.

> Read more about [mirroring on Microsoft Learn](https://learn.microsoft.com/en-us/fabric/database/mirrored-database/overview).

## Power BI Reports with Mirrored Databases

Fabricon 4 provides a strategy of how to setup near real-time reporting that can be applied to most mirrored databases.

We are going to build a Power BI report powered by SQL Server and Cosmos mirrored databases.

Let's assume a SQL database with following tables is mirrored into Fabric:

1. `dbo.Customer`
2. `dbo.Product`
3. `dbo.Order`

Let's assume a Cosmos DB with following tables is mirrored into Fabric:

1. `ProductOffers`

The goal is to combine data from all above 4 tables to generate reports that do not depend on a traditional ETL cycle.

> Fabricon 4 recommends to connect Power BI reports with an intermediatory lakehouse instead of the mirrored database.

### Combining Various Data Sources into a Lakehouse

Fabricon 4 recommends creating a lakehouse for reporting where mirrored tables are brought in via [shortcuts](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-shortcuts).

> At the time of writing, all of the mirrored database offerings are in preview. They are read-only and do not natively support data transformations.

The tables (shortcuts or otherwise) in the reporting lakehouse then can be added to a [Default Power BI semantic model](https://learn.microsoft.com/en-us/fabric/data-warehouse/semantic-models). This approach enables a Power BI report to seamlessly connect to data from multiple sources (mirrored or otherwise).

In our example, Power BI report can to connect to data from all four mirrored tables that will always be in-sync thus eliminating the need of traditional ETL cycle.

### Transforming Data From Mirrored Tables

There are situations that require transformation of data from it's state in the mirrored table. It may include:

* Change data type to a [Delta Lake](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-and-delta-tables) type.
* Selecting relevant columns in a multi-model Cosmos DB container.

> Cosmos DB mirror table mirrors all columns/properties as string. Intelligent date based grouping (2024-11-01 to Nov 2024) on Power BI only work if the date column is of date type.

There are two ways to handle data transformations:

#### 1. Use SQL Views

SQL view can be created on a lakehouse table to transform data as needed, but at a significant performance cost due to fallback to [DirectQuery mode](https://learn.microsoft.com/en-us/fabric/data-warehouse/semantic-models#direct-lake-mode). In some cases the slow down may be acceptable.

#### 2. Implement traditional ETL

Implementing a traditional ETL goes against the idea of mirroring, but may be the only option if the performance of SQL views is not acceptable. With this approach new tables are created in the reporting lakehouse that are included into default Power BI semantic model.

[Fabricon 5: Realtime Reporting with EventHouse](../Fabricon5/README.md) may be an alternative option.