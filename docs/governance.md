# Governance and decisions

## Current ownership

The repository owner and initial maintainer is [@Ramses13th](https://github.com/Ramses13th). There is no established steering committee or funded team. People can contribute without being granted repository write access.

The owner reviews project direction and merges. As domain maintainers emerge, responsibilities can be proposed publicly and recorded here. Being an AI agent or using a high-capability model does not grant merge authority.

## Make decisions in public

Small documentation fixes can go directly to a pull request. Use a design RFC issue for decisions that affect the CAD kernel, solver, document schema, IPC, tolerances, topology references, binary distribution, or licensing.

A useful RFC contains the concrete problem, user workflow, proposed contract, alternatives, failure behavior, migration impact, validation evidence, and unresolved questions. Discuss the proposal before implementing a large subsystem. Accepted decisions become a dated decision record under [docs/decisions](decisions/0001-cad-architecture.md).

Proposed decision records are visibly marked. Merging a research note does not mean all dependencies or architectural choices in that note have been accepted.

## Review and contribution standards

The [contributor guide](../CONTRIBUTING.md), [AI policy](ai-contributions.md), [code of conduct](../CODE_OF_CONDUCT.md), and [security policy](../SECURITY.md) apply across the project. Submitters must have the right to contribute their work and preserve source attribution.

Critical geometry changes need review from someone able to assess the relevant domain. Until such a reviewer exists, a proposal can remain experimental rather than being represented as production-ready. CI is evidence for the checks it actually runs, not proof of CAD correctness.

## Roadmap changes and releases

The [roadmap](../ROADMAP.md) is a prioritized plan with acceptance gates. It is not a service-level agreement or committed release schedule. Propose changes with a user need and a realistic validation path. Release notes must state supported platforms, known failures, schema changes, and actual feature availability.

Before distributing native dependencies, record versions, licenses, source/build instructions, and required notices. The project license is GPL-3.0-or-later; introducing a dependency does not automatically establish that its distribution is compliant.

## Community channels

Use [GitHub issues](https://github.com/Ramses13th/B-CAD/issues) for design proposals and actionable work, and [Discussions](https://github.com/Ramses13th/B-CAD/discussions) for questions and broader conversations. There is no official Discord, mailing list, sponsorship program, or support SLA at this stage.
