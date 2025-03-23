# Contributing

The FabriconDev Engineering Architecture is a living, evolving resource. It may change based on new requirements, industry shifts, or lessons learned. All technologists are encouraged to participate in the conversation around the Architecture. The Architecture is [Open Source][open source], and we welcome feedback and contributions from the community.

## Contributing Directly to the Architecture

### Issue Creation

The [Issues tab of the Architecture’s Repository][issues] is where we track the backlog of work needed for the Architecture. If something appears to be missing, unclear, or incorrect, please create an issue to bring it to the team’s attention. The more detail you can provide, the easier it will be to address the issue effectively.

Examples of great issues:

* Malformed content
* Missing supporting documentation
* Content to be added from the [RFC Process](#requests-for-comments-rfc)
* Process changes to how we handle contributions

Examples of less helpful issues:

* Non-actionable feedback (e.g., “This might be improved somehow” without suggestions)
* Recommendations for entirely new topics without any context or solution proposal
* Simple spelling and grammar mistakes (these can be submitted directly as a [pull request][pulls] rather than creating an issue)

We want all issues to be actionable. Questions are acceptable as long as they lead to an actionable step. For recommendations on new topics, please consider using the [RFP (Request for Proposal) process](#request-for-proposals-rfp) outlined below. For minor text corrections like spelling errors, submit a quick pull request instead of opening a new issue.

## Pull Requests

Community members are encouraged to take on issues, submit changes, and improve the Architecture through [pull requests][pulls]. Feedback on pull requests is also immensely valuable—reviewing and commenting helps ensure that proposed changes align with the broader goals of the Architecture. All constructive feedback is welcome, as it helps maintain the Architecture as an open, collaborative project.

## Contributing to the Architecture Process

Beyond fixing issues or adding incremental improvements, community members can shape the Architecture’s future direction by proposing new standards, processes, or guidelines. We use two key mechanisms for this: **RFP (Request for Proposal)** and **RFC (Request for Comments)**.

### Request for Proposals (RFP)

**What is an RFP?**  
An RFP is the starting point for discussing a new problem or challenge that the Architecture should address. Contributors use an RFP to clearly frame an issue or opportunity that needs a solution, without initially providing that solution themselves.

**How to Submit an RFP:**  

1. **Create an Issue:** In the [Issues tab][issues], open a new issue that explicitly states the problem. Define the scope clearly. Do not include your own solutions or opinions in the initial issue body—just the facts and the core problem that needs to be solved.  
2. **No Initial Solutions:** Keep the initial issue statement solution-free. Your goal is to set the stage for discussion. If you have solutions in mind, you can propose them in comments on the same issue after it is created.  
3. **Core Contributor Assignment:** Once your RFP is created, a core contributor will be assigned to help guide the discussion. The core contributor ensures that all necessary details are captured and that the conversation remains constructive and solution-focused.  
4. **Community Discussion:** Other contributors and community members can respond to the RFP issue with their own ideas and proposals. This collaborative discussion should refine the problem statement and move towards consensus on a potential solution.

### Requests for Comments (RFC)

**What is an RFC?**  
An RFC is used to propose a well-defined solution or standard to be integrated into the Architecture. After an RFP leads the community to identify a viable approach, the next step is to formalize that approach through an RFC.

**How to Submit an RFC:**  

1. **Align with an Existing RFP:** Before creating an RFC, ensure there’s a corresponding RFP issue that defines the problem. The RFC is where you present your formalized solution to that problem.  
2. **Use the RFC Template:** Follow the [Standard RFC Template][template] and recommended RFC workflow. Create a new RFC file in your fork of the repository and describe the solution in detail, including rationale, examples, and expected impact.  
3. **Open a Pull Request:** Once your RFC is drafted, open a pull request to the Architecture’s RFCs directory. The community will be invited to review, comment, and suggest improvements.  
4. **Core Contributor Review & Discussion:** A core contributor will be assigned to your RFC. This person will help incorporate feedback, ensure all questions are addressed, and guide the proposal through the review process.  
5. **Comment Period & Approval:** Once the solution has been refined, we will announce a comment period. Community members have a set timeframe to review and provide feedback. Silence from the community during the defined timeframe will be considered approval. If all comments are addressed and the community reaches consensus, the RFC will be marked as approved.  
6. **Integration:** After approval, the RFC’s solution will be integrated into the Architecture. Issues may be created to reflect the next steps—documentation updates, implementation guidelines, or any other necessary follow-up.

---

[open source]: https://en.wikipedia.org/wiki/Open-source_software  
[issues]: https://github.com/FabriconDev/FabriconArchitecutre/issues  
[pulls]: https://github.com/FabriconDev/FabriconArchitecutre/pulls  
[template]: https://github.com/FabriconDev/FabriconArchitecutre/blob/main/standard-template.md
