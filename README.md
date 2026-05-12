# Fabricon: Architecture for Microsoft Fabric

## What is Fabricon?

Fabricon is an architectural framework for managing software projects on [Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/get-started/microsoft-fabric-overview) using data engineering and software engineering best practices. It is written by engineering team at [Unite Digital LLC](https://unitedigital.com).

## What does it offer?

Fabricon provides guidance on how to manage software projects of varying complexities. It offers guidance on:

1. Environment separation
2. Medallion architecture
3. Code organization using notebooks
4. Source control
5. Unit testing
6. Automated documentation
7. Branching strategy
8. Notebook deployment to production
9. Report deployment to production

## Who is it for?

Fabricon is designed for data engineering teams to learn software engineering best practices, and for software engineering teams to learn data engineering best practices, all under one framework.

## What is the goal?

Our goal is to win community contributions and adoption to an extent that when someone say "we use Fabricon 1", people know exactly what it means.

## The back story?

The engineering team at [Unite Digital LLC](https://unitedigital.com) was tasked with building a new product that required processing of large volumes of data. The engineering team, with no prior experience in data engineering / big data, did not find comprehensive guidance on how to build reliable products on big data platforms. The team spent countless hours gathering information from blogs, documentation sites and video series from the internet. We would like to share our findings with the community to enable faster and easier adoption of [Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/get-started/microsoft-fabric-overview).

## Fabricon Architecture

- [The Basics](./Basics/README.md)
- [Fabricon 1: Basic Environment Segregation](./Fabricon1/README.md)
- [Fabricon 2: Medallion-Based Environment Architecture](./Fabricon2/README.md)
- [Fabricon 3: Medallion-Based Environment Architecture for Large Data Volumes](./Fabricon3/README.md)
- [Fabricon 4: Seamless Reporting with Database Mirroring](./Fabricon4/README.md)
- Fabricon 5: Realtime Reporting with EventHouse (Coming soon)
- [Fabricon N: Code Organization Using Notebooks](./FabriconN/README.md)
- [Fabricon R: Report Promotion Across Environments](./FabriconR/README.md)

> Any Fabricon pattern ending in a letter instead of a number indicates that it is an extension that can be applied to any numbered Fabricon pattern.

## Using with Claude Code

This repository includes a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that provides context-aware guidance on Fabricon patterns. When you use Claude Code in this repository, it automatically understands Fabricon's workspace conventions, medallion architecture, shortcut provisioning, deployment strategies, and report promotion patterns.

**Getting started:**

1. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code) if you have not already.
2. Open a terminal in this repository and run `claude`.
3. Ask any question about Fabricon patterns. For example: "What workspace structure should I use for a new CRM project?" or "How do I set up shortcut provisioning in my Gold notebook?"

Claude Code will use the `fabricon-architecture` skill located in `.claude/skills/fabricon-architecture/SKILL.md` to provide answers grounded in Fabricon's conventions.

> You can also reference patterns directly by saying "Fabricon 2", "Fabricon 3R", "Fabricon N", etc.

## Recognition

- Author: Shahid Syed [![LinkedIn](./Images/linkedin.png)](https://www.linkedin.com/in/smsyed)
- Co-author: George Matus
- Advisor: Fadi Aoude [![LinkedIn](./Images/linkedin.png)](https://www.linkedin.com/in/fadiaoude)

Core Contributors:

- Michael Cavanaugh [![LinkedIn](./Images/linkedin.png)](https://www.linkedin.com/in/michael-cavanaugh-3920337a)
- Bill McGough [![LinkedIn](./Images/linkedin.png)](https://www.linkedin.com/in/williamamcgough)
- [YOUR NAME HERE]

Contributors:

- [YOUR NAME HERE]

## Contributing

Microsoft Fabric is growing rapidly, and we need your assistance to ensure that Fabricon remains up-to-date.
We welcome your contributions and suggestions. Contributors must ensure they have the right to, and actually grant us the rights to use their contributions.


Please see [our process on contributing to the Fabricon Architecture](./CONTRIBUTING.md).

## Social

Reddit: https://www.reddit.com/r/FabriconDev  
> Have questions, comments, or suggestions? Join our community on Reddit and reach out to us directly!
  
## Inspirations

- [Guy in a cube](https://www.youtube.com/@GuyInACube)
- [endjin](https://www.youtube.com/@endjin)
- [nbdev](https://nbdev.fast.ai)
- [jupyter-black](https://pypi.org/project/jupyter-black)
- [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/get-started/microsoft-fabric-overview)

## License

[MIT plus some](https://github.com/FabriconDev/FabriconArchitecutre/blob/main/LICENSE)

## Sponsors

[![Unite Digital logo](./Images/unite_digital_logo.png)](https://unitedigital.com)
