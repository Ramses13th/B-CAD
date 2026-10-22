# Help build B-CAD

B-CAD is an open-source parametric CAD project inside Blender. We have an **experimental first slice**: exact primitives, a local browser workbench and a Blender display adapter. Most modeling capabilities remain on the roadmap; there is no production release. Help turn a small, tested foundation into software people can trust. Read [installation](docs/installation.md), [development](docs/development.md) and [ADR 0002](docs/decisions/0002-first-prototype.md) before extending the experiment.

Humans, people working with AI, and AI agents are welcome. You do not need to be a CAD-kernel expert to make a useful contribution. Good documentation, concrete modeling workflows, accessibility feedback, and small reproducible examples matter.

## Start with one useful contribution

| Your interest | A good first contribution |
| --- | --- |
| Mechanical design | Describe a real part, the edits you expect, and where a CAD workflow breaks. |
| Blender / Python | Propose an interaction or undo experiment with a small acceptance test. |
| Geometry / C++ | Review the proposed kernel boundary, tolerances, or persistent references. |
| Testing | Design a small, shareable regression fixture and state what it proves. |
| Writing / UX | Fix a confusing page, add a glossary explanation, or improve keyboard access. |
| AI agents | Read [AGENTS.md](AGENTS.md), choose a bounded issue, and supply evidence for every claim. |

Read the [roadmap](ROADMAP.md), [architecture](docs/architecture.md), and [development guide](docs/development.md). Then browse [open issues](https://github.com/Ramses13th/B-CAD/issues) or [propose one](https://github.com/Ramses13th/B-CAD/issues/new/choose). Search first so related work stays together. If an issue looks unclaimed, describe your intended scope in a comment; maintainers can help narrow it. Small documentation fixes can go straight to a pull request.

## Propose before building a foundation

Use a **Design RFC** issue before introducing a new dependency, document format, process boundary, solver, licensing arrangement, or major user workflow. Describe the problem, alternatives, tradeoffs, failure behavior, and a small experiment that could disprove the proposal. A blueprint recommendation is a starting point for review, not a finished implementation contract.

For a feature request, tell us what you are trying to model and how you would judge success. For a bug, identify what actually exists today: a documentation error, site problem, or implemented behavior. Mark future behavior as a proposal.

## Make a pull request

1. Fork the repository and create a descriptive branch, such as `docs/clarify-units`.
2. Keep the change focused. Link its issue when there is one, and explain the user-visible result.
3. Follow the [local workflow](docs/development.md). Run the documentation checker and build the site. For future implementation changes, add meaningful tests for the behavior being changed and report the exact commands and results.
4. Cite technical sources and acknowledge borrowed material. Check that dependencies and examples can be distributed under [GPL-3.0-or-later](LICENSE).
5. Complete the pull request template, including AI disclosure when applicable. Include screenshots for visual changes and reproduction steps for behavior changes.
6. Respond to review. A human maintainer must review and approve a merge. Agents must not approve or merge their own work.

Do not report an unrun check as passing. If you cannot run a check, explain the limitation and what evidence you do have. Do not add placeholder tests that only repeat the implementation, fabricated screenshots, or benchmarks without reproducible inputs.

## AI contribution policy

The project owner's requested quality bar for AI-authored code and architecture is **GPT-6.1 Sol, Astra, Claude Opus 5.5 level, or an equivalent or more capable model**. These are the owner's capability references, not a claim that B-CAD has independently measured or certified model equivalence. Read the [full AI contribution policy](docs/ai-contributions.md) for model attestation, review, and accountability requirements. Human contributions without AI are fully welcome.

## Engineering habits we want to establish

- Keep exact CAD state separate from Blender display meshes. Explicitly distinguish planned architecture from current code.
- Prefer visible, recoverable failures to silently altered geometry. Define units, tolerances, and reference behavior.
- Make substantial changes reviewable through fixtures, diagnostics, and reproducible evidence.
- Keep dependencies and licenses explicit. Do not copy code, screenshots, models, or text without the right to contribute them.
- Protect contributors' data. Remove credentials, private paths, customer designs, and personal information from examples and logs.

By contributing, you agree to the [Code of Conduct](CODE_OF_CONDUCT.md). Contributions are submitted under the repository's [GPL-3.0-or-later license](LICENSE); you retain copyright in your work. Contribute only material you are authorized to license. Attribution and third-party license notices must be preserved.

For security-sensitive reports, follow [SECURITY.md](SECURITY.md). For ordinary questions and collaboration, use [GitHub Issues](https://github.com/Ramses13th/B-CAD/issues).
