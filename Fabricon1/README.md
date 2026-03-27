# Fabricon 1: Basic Environment Segregation

Microsoft Fabric provides common tools for data manipulation, such as data pipelines and notebooks (referred to as code). When your proof of concept (POC) is ready for production, you will likely need to separate non-production environments (e.g., DEV, TEST) from the production environment.

> Fabricon recommends creating a dedicated Fabric workspace for each environment.

For example, if you are building a CRM data product and decide that DEV and PROD environments are sufficient, we recommend creating a domain named `CRM` with the following workspaces:

- `CRM-Dev`
- `CRM-Prod`

Each workspace should contain all the items required for the data product, such as lakehouses, data pipelines, notebooks, etc.

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

## What Fabricon 1 Solves

| Problem | Solution |
| --- | --- |
| Non-production and production code mixed together | Separate Fabric workspace per environment |
| No consistent project structure | Standardized folder structure (Archive, Configuration, Exploration, Pipeline, Reports, Tests) |
| Unclear promotion path for code changes | Environment-per-workspace enables clear promotion flow |

## References

- [Microsoft Fabric Workspaces](https://learn.microsoft.com/en-us/fabric/get-started/workspaces)
- [Fabric Domains](https://learn.microsoft.com/en-us/fabric/governance/domains)
