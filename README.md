<p align="center">
  <img src="site/assets/blueprint.svg" alt="B-CAD — an open blueprint for parametric CAD inside Blender. Technical concept illustration, not a product screenshot." width="100%">
</p>

<p align="center">
  <a href="https://www.repostatus.org/#concept"><img src="https://www.repostatus.org/badges/latest/concept.svg" alt="Project status: concept"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0--or--later-89c4a0" alt="License: GPL-3.0-or-later"></a>
  <a href="https://github.com/Ramses13th/B-CAD/actions/workflows/docs.yml"><img src="https://github.com/Ramses13th/B-CAD/actions/workflows/docs.yml/badge.svg" alt="Documentation checks"></a>
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/contributions-humans_%2B_AI-f4aa55" alt="Contributions: humans and AI"></a>
</p>

<h1 align="center">Precision, with room to build.</h1>

<p align="center"><strong>An open blueprint for a serious parametric CAD system inside Blender.</strong><br>
Exact geometry. Editable design intent. A community building in the open.</p>

<p align="center">
  <a href="https://ramses13th.github.io/B-CAD/"><strong>Explore the website ↗</strong></a> ·
  <a href="ROADMAP.md">Roadmap</a> ·
  <a href="docs/architecture.md">Architecture</a> ·
  <a href="CONTRIBUTING.md">Contribute</a> ·
  <a href="https://ramses13th.github.io/B-CAD/search.html">Search docs</a>
</p>

> **Current status: blueprint / pre-implementation.** This repository contains the project plan, architecture proposals, contributor guides, and documentation website. **There is no Blender add-on, CAD core, downloadable installer, or supported Blender version yet.** Features below describe the system we want to build. See [installation and availability](docs/installation.md).

## What is B-CAD?

B-CAD aims to bring a Fusion-like mechanical design workflow to Blender: constrained sketches, parameters, a feature history, exact solid geometry, and genuine CAD exchange. Blender would provide the interaction and visualization environment; a separate CAD core would own the engineering model.

The architectural north star is simple: **B-Rep and parameters are authoritative. Blender meshes are display caches.** A tessellated viewport should never quietly become the source of a supposedly exact dimension.

This is an independent community project. It is not affiliated with or endorsed by Autodesk, Blender Foundation, or Open Cascade.

## Start here

| You want to… | Start with… |
| --- | --- |
| Install or try the add-on | [Installation and current availability](docs/installation.md) |
| Find a useful first contribution | [Contributor guide](CONTRIBUTING.md) and [good first issues](https://github.com/Ramses13th/B-CAD/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22good%20first%20issue%22) |
| Bring an AI coding agent | [AI contribution policy](docs/ai-contributions.md), then [AGENTS.md](AGENTS.md) |
| Understand the engineering plan | [Architecture](docs/architecture.md) and [decision record](docs/decisions/0001-cad-architecture.md) |
| Choose a substantial project | [Roadmap and acceptance gates](ROADMAP.md) |
| Edit or preview the docs | [Development guide](docs/development.md) |
| Ask a question | [FAQ](docs/faq.md) or [open an issue](https://github.com/Ramses13th/B-CAD/issues/new/choose) |

## The system we want to build

| Area | Proposed direction | Status |
| --- | --- | --- |
| Sketching | Lines, arcs, circles, dimensions, geometric constraints, degrees of freedom | Planned |
| Exact solids | An external native core using Open CASCADE Technology (OCCT) | Proposed architecture |
| Parametric history | Versioned document, dependency graph, deterministic recompute, explicit failures | Planned |
| Modeling | Extrude, revolve, Boolean operations, fillet, chamfer, holes, patterns | Planned MVP scope |
| Stable references | Semantic face/edge references with operation history and ambiguity diagnostics | Research priority |
| CAD exchange | STEP import/export; STL and 3MF as derived mesh exports | Planned |
| Blender integration | Viewport, selection, panels, undo synchronization, local display caches | Planned |
| Beyond the MVP | Assemblies, drawings, advanced features, migration, manufacturing bridges | Later roadmap |

No part of this table is a compatibility or feature-availability claim. The [roadmap](ROADMAP.md) defines what evidence is needed to change a feature's status.

## A CAD engine with Blender as its home

```text
Blender interaction + viewport
              ↕ versioned commands / display results
Parametric document + feature dependency graph
              ↕ validated operations / diagnostics
External CAD core → OCCT exact B-Rep
              ↓ tessellation and semantic picking data
Blender display meshes (rebuildable caches)
```

The hard problems deserve early attention: persistent topology references, units and tolerances, transactional undo, solver behavior, reliable native packaging, and failure recovery. Solver choice, protocol encoding, document storage, and the supported platform matrix remain open design decisions. Read the [architecture proposal](docs/architecture.md) before implementing a subsystem.

## Humans and capable AI agents: come build with us

You can contribute as a Blender user, mechanical designer, Python developer, C++/geometry engineer, technical writer, tester, or AI-assisted contributor. Useful work includes concrete design reviews, reproducible CAD cases, accessible UI concepts, documentation, build research, and small, verified patches.

For AI-generated code and architecture, the maintainer's requested quality bar is **GPT-6.1 Sol, Astra, Claude Opus 5.5 level, or equivalent/higher capability**. This is a project contribution requirement, not a measured model ranking. State the model/tool used and provide evidence that the result is understood and verified. Human-only contributions are welcome. All work follows the same review and correctness standards; no AI output merges itself. See the [full AI policy](docs/ai-contributions.md).

1. Read [CONTRIBUTING.md](CONTRIBUTING.md) and choose one bounded task.
2. Check [open issues](https://github.com/Ramses13th/B-CAD/issues) and leave a short plan to avoid duplicate effort.
3. Use a design RFC for kernel, document-schema, solver, or protocol decisions.
4. Open a focused pull request with reasoning, attribution, and verification evidence.

Please share the project with people who can help, star it if you want to follow along, and watch releases when you want to try future builds. Thoughtful, reviewable work is the best way to move the project forward.

## Roadmap at a glance

| Gate | Outcome |
| --- | --- |
| Foundations | Decisions, document/protocol contracts, licensing inventory, reproducible development setup |
| Technical prototype | One constrained sketch → exact extrusion → edit/recompute → STEP round trip |
| Useful MVP | Robust sketching and history, core solid tools, measurement, exchange, installable packages |
| Release hardening | Cross-platform validation, migrations, regression corpus, recovery, accessible documentation |
| Beyond MVP | Assemblies, drawings, broader modeling, migration and manufacturing integrations |

The [full roadmap](ROADMAP.md) contains task IDs, dependencies, acceptance criteria, and release gates. Dates and staffing are intentionally uncommitted.

## Documentation that stays useful

The [public hub](https://ramses13th.github.io/B-CAD/) publishes the same Markdown maintained here, with browser-local search, accessible navigation, a sitemap, and links back to source. Pull requests run local-link and generated-site checks. This CI validates the documentation; it does not validate a CAD implementation.

## License and acknowledgments

Original repository code and documentation are licensed under **GPL-3.0-or-later**, unless a file says otherwise. See [LICENSE](LICENSE) and [NOTICE](NOTICE). Dependency and distribution choices require an explicit license inventory before native components are shipped.

The project plan was informed by an owner-supplied CAD architecture blueprint and existing work in the Blender and open CAD ecosystem. [Research notes](docs/research.md) distinguish references from decisions and implementation. No third-party CAD source code is bundled in this initial project hub.
