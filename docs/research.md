# Research register and source notes

> B-CAD is a blueprint and contributor hub. This register identifies questions to answer before implementation choices become compatibility promises. A link to a capable upstream project is evidence to investigate, not a claim that B-CAD already integrates it.

The user-supplied **Blueprint for a Fusion-like parametric CAD system inside Blender** informed the architecture and scope. It is reference material. No implementation, source-code reuse, dependency approval, version support, calendar schedule, or effort estimate is implied by using that document. The original PDF is not redistributed here because redistribution rights have not been established.

## Open decisions

All entries are open. Research can recommend a choice; a reviewed ADR records its adoption.

| Question | Evidence to collect | Decision output | Roadmap |
| --- | --- | --- | --- |
| Which Blender baseline and platforms can we actually support? | Minimal lifecycle/undo/serialization experiments on exact builds; API and packaging compatibility; CI availability | Version/OS/CPU support ADR and verified matrix | FND-01 |
| Which OCCT source version and build configuration? | Reproducible native build; shape validity; STEP/units; history behavior; runtime size and platform availability | Kernel/build pin ADR with known issues | FND-02, FND-03 |
| What can we distribute together? | Pinned dependency tree, source licenses/notices, code/data provenance, current distribution-channel rules, build/source obligations | Dependency manifest and reviewed release route | FND-02 |
| SolveSpace/libslvs or PlaneGCS for the first sketch solver? | Identical constraint/degeneracy/drag fixtures, diagnostic capabilities, extraction/build costs, source-version/license review | Solver ADR with benchmark and limitations | FND-04 |
| What is canonical, and what is a cache? | Document examples including imported exact assets; deterministic serialization/migration policy; cache deletion/rebuild | Schema/asset RFC | FND-05 |
| Which local protocol and transport? | Two-session isolation, authentication strategy, payload limits, latency, cancel/crash/restart behavior | Protocol ADR with revision and failure semantics | FND-06 |
| Can references preserve intent through relevant edits? | Split/merge, suppression, upstream dimensions, changed pattern counts, operation-history coverage, OCAF/TNaming prototype | Topology-reference RFC and failure corpus | FND-07 |
| How do host undo and a native process stay synchronized? | Commit/cancel, undo/redo, switch documents, save/reopen, child crash, stale results | Transaction and recovery ADR | CORE-06 |
| Which units, tolerance policy, and transform rules? | Mixed-unit formulas, far-origin occurrences, small features on large parts, display-unit changes, scale/parenting operations | Quantity/tolerance/placement RFC | CORE-02, CORE-05 |
| What can migrate from other projects honestly? | Pinned upstream formats, redistributable examples, per-feature mappings, lost semantics, user-readable conversion reports | Import compatibility document | IO-05, MIG-01 |
| What does a supported release promise? | Clean install/upgrade/uninstall, package reproducibility, recovery behavior, schema transitions, known model-size limits | Release checklist and support policy | REL-02–REL-07 |

## Initial evidence and primary references

The source pages below were inspected for this planning pass on **22 October 2026** where stated. Upstream `main`, `master`, and current documentation can change. An implementation proposal must record exact source commits or release tags and recheck the documentation matching those pins.

| Source | What it supports | What it does not establish |
| --- | --- | --- |
| [OCCT modeling algorithms](https://github.com/Open-Cascade-SAS/OCCT/blob/master/dox/user_guides/modeling_algos/modeling_algos.md) · inspected | Modeling primitives and history concepts worth prototyping | That every operation handles every degenerate model, or that B-CAD integration is correct |
| [OCCT BRepTools_History API](https://www.occt3d.com/dev/doc/refman/html/class_b_rep_tools___history.html) · inspected | Generated/modified/removed relationships and history composition | A complete application-level solution for persistent user intent |
| [OCCT OCAF guide](https://occt3d.com/dev/doc/overview/html/occt_user_guides__ocaf.html) · inspected | Reference-key-driven data, naming attributes, topology evolution, and document services | Whether B-CAD should serialize its canonical model directly as OCAF or use it as supporting infrastructure |
| [OCCT XDE guide](https://occt3d.com/dev/doc/overview/html/occt_user_guides__xde.html) · inspected | Assembly/metadata exchange mechanisms | Lossless preservation through every STEP schema, option, or external application |
| [SolveSpace library documentation](https://solvespace.github.io/solvespace-web/library.html) · inspected | A library interface exists; the page describes coupling to SolveSpace's implementation | Current build instructions, a chosen source pin, or superiority over other solvers; this page contains legacy examples |
| [FreeCAD PlaneGCS header](https://github.com/FreeCAD/FreeCAD/blob/main/src/Mod/Sketcher/App/planegcs/GCS.h) · inspected | Solver interfaces, solve states, and the file's SPDX declaration | Standalone extraction effort, complete transitive licensing, or the best backend for our workloads |
| [Blender LTS policy](https://www.blender.org/download/lts/) · verification required | Official place to verify candidate support lifetimes | Any Blender version/date claimed in the supplied blueprint; no B-CAD baseline is selected |
| [Blender threading guidance](https://docs.blender.org/api/current/info_gotchas_threading.html) and [application handlers](https://docs.blender.org/api/current/bpy.app.handlers.html) · verification required | Official integration references to inspect against the selected build | That a particular host integration has been implemented or tested; these pages could not be retrieved by the research tool during this pass |

Other useful starting points, to inspect and pin before relying on them:

- [OCCT source repository](https://github.com/Open-Cascade-SAS/OCCT) for build configuration, source licenses, and version-specific behavior.
- [SolveSpace source repository](https://github.com/solvespace/solvespace) for current library code, license files, and build requirements.
- [CadQuery](https://github.com/CadQuery/cadquery) for high-level OCCT-based prototypes, fixtures, and possible future scripting. Using it for a spike does not select it as the production core.
- [CAD Sketcher](https://github.com/hlorus/CAD_Sketcher) for sketch UX, migration research, and existing Blender workflows. Inspect a pinned version before describing its storage or migration coverage.
- [Blender Seamless CAD](https://github.com/hinatahugu29/Blender_Seamless_CAD) for a neighboring CAD-in-Blender architecture and exchange/migration research. Treat internal file layouts as version-specific.
- [lib3mf](https://github.com/3MFConsortium/lib3mf) for a possible 3MF implementation and independent validation strategy.
- [Ceres Solver](https://github.com/ceres-solver/ceres-solver) for later numerical assembly-solver research. A nonlinear optimizer does not supply mate semantics, degrees-of-freedom reasoning, or conflict UX by itself.

These projects are independent upstreams. B-CAD does not claim affiliation, endorsement, or incorporation of their code.

## A useful research contribution

Keep a research PR small enough to reproduce and review. Include:

1. **Question and decision it informs.** Link a roadmap ID and state the alternatives.
2. **Pinned environment.** Source commit/tag, compiler, dependencies, host version, OS/architecture, and relevant options.
3. **Reproduction.** A clean-checkout command sequence, original redistributable fixtures, and expected outputs. Separate prototypes from supported add-on code.
4. **Evidence.** Raw measurements where useful, semantic geometry checks, failed cases, and independently checked units or analytic expectations.
5. **Conclusion with limits.** Explain what the experiment establishes, what remains uncertain, and what would change the recommendation.
6. **Provenance.** Source links, authorship/rights for fixtures, adapted-code notices, and any new dependency obligations.

Use reproducible behavior to compare options. Avoid declaring a solver or kernel reliable because one attractive model or demo succeeds. Research that rejects an unsuitable choice or minimizes a difficult failing model is valuable progress.

## Initial regression questions

| Area | Case | Expected observation |
| --- | --- | --- |
| Units | `shaft_d + 0.20 mm`, mixed metric/imperial presentation | Typed evaluation preserves physical values; display changes do not alter the model |
| Solver | Impossible tangency, redundant dimension, almost-zero line | Actionable state/diagnostic, no committed invalid solution hidden behind a successful preview |
| Topology | Fillet after extrude length edit, face split/merge, hole moved | Intended reference persists or becomes explicitly unresolved |
| Patterns | Count `4 → 7 → 3`, downstream selected occurrence | Stable documented identity semantics or a visible invalidated reference |
| Geometry | Tangent cylinders, sliver faces, near-coincident Boolean arguments | Validated result or bounded, recorded failure/retry |
| Precision | Small feature on a large part; occurrence far from origin | Exact core queries are independent of viewport approximation |
| Transactions | Edit, cancel, undo, redo, save/reopen, kill/restart core | One committed canonical revision; stale results cannot overwrite it |
| Recovery | Delete display caches, truncate a file, remove required source asset | Rebuild succeeds where possible; otherwise retain source and report the specific missing/corrupt input |
| Exchange | STEP metric/imperial round trip; STL/3MF units | Geometry and units match declared invariants and documented data loss |

Keep benchmark sizes and performance budgets provisional until measured on named hardware. Preserve anonymized diagnostic packages only with permission to redistribute the included models and metadata.
