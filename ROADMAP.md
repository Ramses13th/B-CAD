# B-CAD roadmap

**A path from an open blueprint to trustworthy parametric CAD in Blender.**

> **Project stage: blueprint and contributor hub.** The features below are planned work. This repository does not yet contain a working Blender add-on, a CAD kernel bridge, a supported installation package, or a release. No milestone has an implementation completion claim or promised delivery date.

The goal is a mechanical CAD environment that feels at home in Blender: constrained sketches, dimensions and expressions, editable feature history, exact boundary representation (B-Rep) geometry, and useful engineering exchange. Blender provides interaction and visualization; the CAD document and geometry core preserve design intent. See the [architecture proposal](docs/architecture.md) and [initial architecture record](docs/decisions/0001-cad-architecture.md).

## How to use this roadmap

- **P0** means required to prove the architecture or make an MVP trustworthy. It does not mean every task can run immediately.
- **P1** means valuable follow-on work. It starts when its prerequisites and review capacity are available.
- Every task below is **proposed / not implemented**. IDs are planning references, not existing GitHub issue numbers. An issue should link the ID, narrow the scope, name a reviewer, and include its acceptance criteria before implementation starts.
- Dependencies identify the main technical prerequisites. A phase can overlap another when those prerequisites are met. Dependency completion must include review and evidence, not just merged code.
- Completing a task means its documented acceptance criteria pass and relevant documentation is updated. Completing a phase requires its exit gate as well.

Start with a bounded research task, a test fixture, a documentation improvement, or a reviewed vertical slice. Follow [CONTRIBUTING.md](CONTRIBUTING.md) before claiming a task. Human and AI-assisted work follows the same evidence and review requirements.

## Milestone map

| Milestone | Outcome | Exit gate |
| --- | --- | --- |
| 0 · Validate the foundation | Evidence for the kernel, solver, persistence, and packaging choices | Reproducible spikes and decision records; unresolved risks have owners |
| 1 · Build a recoverable core | Versioned document, native process, deterministic recompute, display cache | Restart, undo, save/reload, and stale-result cases cannot diverge silently |
| 2 · Constrain a sketch | Geometry, typed dimensions, constraints, exact interaction | A constrained profile remains editable and reports failure clearly |
| 3 · Model a part | Solid features and references that survive edits | Golden parts recompute correctly after upstream changes |
| 4 · Exchange and inspect | Engineering measurements and honest interchange | Units and geometry survive documented round trips |
| 5 · Earn an MVP release | Supported packages and repeatable user workflows | Release checklist passes on every advertised platform |
| 6 · Grow into engineering workflows | Advanced features, assemblies, drawings, and migration | Each subsystem has its own design review and regression gate |

There is intentionally no calendar schedule. Contributor availability, geometric edge cases, and reference reliability determine the pace. A failed correctness gate should delay feature expansion.

## 0 · Validate the foundation

| ID | Priority | Deliverable and acceptance criteria | Depends on |
| --- | --- | --- | --- |
| FND-01 | P0 | **Compatibility baseline.** Compare supported Blender release candidates and target OS/CPU combinations using a minimal add-on lifecycle experiment. Record exact tested builds, API assumptions, and the first supported matrix in an ADR. | — |
| FND-02 | P0 | **Dependency and distribution review.** Inventory proposed direct/transitive dependencies, pinned source versions, licenses, notices, and redistribution requirements. Document a viable release route for native binaries and verify current distribution-channel rules before relying on them. | — |
| FND-03 | P0 | **OCCT vertical spike.** In an isolated executable, construct a dimensioned solid, validate it, query volume, tessellate it, and export/re-import STEP. A clean checkout can reproduce the result with explicit build instructions. This is an experiment, not an add-on release. | FND-02 |
| FND-04 | P0 | **Sketch-solver comparison.** Run the same fixtures through SolveSpace/libslvs and a PlaneGCS feasibility prototype. Publish constraints supported, degrees of freedom, conflicts/redundancy behavior, drag continuity, deterministic replay, extraction cost, and license/build implications. Choose a solver only in a reviewed ADR. | FND-02 |
| FND-05 | P0 | **Document and transaction RFC.** Specify stable IDs, typed quantities, dependencies, reference representation, schema versions, unsupported-feature behavior, and one edit/undo/save/reopen sequence. Include valid and intentionally invalid examples. | — |
| FND-06 | P0 | **Process and IPC spike.** Launch two independent Blender sessions against separate child processes. Exercise handshake/version mismatch, malformed input, timeout, cancellation, crash, shutdown, and restart. Demonstrate that one session cannot accidentally control the other. | FND-01, FND-03, FND-05 |
| FND-07 | P0 | **Reference feasibility corpus.** Prototype semantic feature provenance plus OCCT operation history. Test split/merged faces, changed hole positions, suppression, and pattern-count changes; record ambiguous cases as explicit failures. Compare whether OCAF/TNaming helps before freezing persistence. | FND-03, FND-05 |

**Exit gate:** publish the spike results, resolve or explicitly defer each architecture choice, and approve the smallest end-to-end implementation. A screenshot alone is insufficient evidence.

## 1 · Build a recoverable core

| ID | Priority | Deliverable and acceptance criteria | Depends on |
| --- | --- | --- | --- |
| CORE-01 | P0 | **Canonical document.** Implement the reviewed versioned schema with UUIDs, units, validation, deterministic serialization rules, and a migration fixture. Reject cycles, dangling IDs, invalid quantities, and unsupported future schemas without overwriting the source. | FND-05, FND-07 |
| CORE-02 | P0 | **Quantity and expression engine.** Parse named parameters and metric/imperial expressions into a typed expression tree. Reject dimensionally invalid expressions, cycles, non-finite values, and arbitrary code execution. Preserve the user's expression alongside evaluated values. | CORE-01 |
| CORE-03 | P0 | **Feature dependency graph.** Recompute dirty descendants in a deterministic order. Detect cycles before commit, keep unaffected branches usable, and emit structured feature diagnostics. Verify incremental and full recompute agree semantically. | CORE-01 |
| CORE-04 | P0 | **Native service lifecycle.** Implement the reviewed protocol, request IDs, document revisions, bounded messages, process cleanup, and recovery. Results for canceled or superseded revisions must never replace the current viewport. | FND-06, CORE-01 |
| CORE-05 | P0 | **Exact state and display cache.** Keep parameters, tolerances, and CAD placements in the core's precision model; generate replaceable meshes with provenance. Rebuild display after cache deletion without changing engineering measurements. | CORE-03, CORE-04 |
| CORE-06 | P0 | **Persistence and undo.** Embed the canonical snapshot in a `.blend` workflow and prototype a standalone document format. Undo/redo restores one document revision and resynchronizes the service. Save/reopen, child crash, and canceled edits preserve committed state. Container format remains an ADR choice. | CORE-01, CORE-04, CORE-05 |
| CORE-07 | P0 | **Selection/reference bridge.** Map viewport hits to candidate B-Rep entities, then resolve exact selections in the core. Reject stale cache picks and return a semantic reference or an explicit ambiguity diagnostic. | FND-07, CORE-05 |

**Exit gate:** edit a dimensioned primitive, cancel an edit, undo, redo, save, close, reopen, kill/restart the core, and regenerate all display caches. The canonical state and measured shape agree at every committed revision.

## 2 · Constrain a sketch

| ID | Priority | Deliverable and acceptance criteria | Depends on |
| --- | --- | --- | --- |
| SK-01 | P0 | **Workplanes and entities.** Add origin/datum planes, stable sketch IDs, points, lines, arcs, circles, rectangles, and construction flags. Round-trip entity identity and units through save/load. | CORE-01, CORE-02 |
| SK-02 | P0 | **Solver adapter and constraints.** Implement the solver-independent interface and a documented initial set: coincident, horizontal/vertical, parallel/perpendicular, tangent, equal, midpoint, concentric, symmetry, fix, distances, angle, radius, and diameter. Each supported constraint has valid, impossible, and degenerate fixtures. | FND-04, SK-01 |
| SK-03 | P0 | **Solve and drag diagnostics.** Distinguish under-constrained, fully constrained, conflicting, redundant, and failed states where supported; report solver limitations honestly. Dragging preserves a chosen solution branch or visibly reports failure rather than jumping silently. | SK-02 |
| SK-04 | P0 | **Profile extraction.** Recognize closed loops, holes, construction exclusions, and multiple regions. Self-intersections, tiny edges, open contours, and ambiguous nesting produce actionable diagnostics. | SK-02, CORE-03 |
| SK-05 | P0 | **Exact snapping and projection.** Snap to mathematical endpoints, centers, intersections, and supported tangent/perpendicular relationships. Associative projection records its source reference and breaks visibly when that source cannot be resolved. | CORE-07, SK-01 |
| SK-06 | P1 | **Sketch interaction and accessibility.** Build keyboard-friendly dimension editing, legible constraint glyphs, selection filtering, discoverable shortcuts, and a novice walkthrough. Feedback must remain understandable without relying only on color. | SK-03, SK-04, SK-05 |

**Exit gate:** reconstruct a measured bracket profile with named parameters, fully constrain it, deliberately create a conflict, recover, change metric/imperial presentation, and reload without losing editability.

## 3 · Model a part

| ID | Priority | Deliverable and acceptance criteria | Depends on |
| --- | --- | --- | --- |
| SOL-01 | P0 | **Extrude and revolve.** Support a scoped set of distance/angle and new-body/join/cut/intersect modes. Validate profile and result, retain semantic generated geometry, and cover nested holes plus axis-touching cases. Add advanced extent modes only with their own tests. | SK-04, CORE-03, CORE-07 |
| SOL-02 | P0 | **Boolean pipeline.** Validate inputs and outputs for union, cut, and common. Bound and record any tolerance retry/healing policy. Tangency, nearly coincident faces, and invalid arguments cannot silently become mesh results. | SOL-01 |
| SOL-03 | P0 | **Persistent references in production.** Integrate provenance/history resolution with the dependency graph. Upstream length changes, splits/merges, suppression, and pattern edits either preserve intended references or stop downstream features with a repairable diagnostic. | FND-07, SOL-02 |
| SOL-04 | P0 | **Fillet, chamfer, and holes.** Begin with constant-radius fillets, a clearly scoped chamfer mode, and simple holes. Failed previews leave committed geometry unchanged; selected edges/faces retain intent across supported upstream edits. | SOL-03 |
| SOL-05 | P0 | **Mirror and patterns.** Add body/feature mirror and linear/circular patterns in a declared initial scope. Stable occurrence identities survive count changes; zero/invalid counts and overlapping results follow documented behavior. | SOL-03 |
| SOL-06 | P1 | **Feature-tree editing.** Edit, suppress, insert, and reorder only when dependencies allow it. Explain blocked edits, preserve unaffected branches, and make preview/apply/cancel distinct transactions. | SOL-04, SOL-05, CORE-06 |

**Exit gate:** a small golden-part set survives upstream dimension edits, feature suppression/restoration, fillet changes, pattern counts `4 → 7 → 3`, undo/redo, and save/reload. Semantic reference failures are release blockers for affected workflows.

## 4 · Exchange and inspect

| ID | Priority | Deliverable and acceptance criteria | Depends on |
| --- | --- | --- | --- |
| IO-01 | P0 | **STEP import/export.** Import exact geometry as an explicitly non-parametric base feature. Document supported schema and metadata. Round trips preserve units, body count, validity, bounds, and mass properties within declared tolerances; names/colors/assemblies are tested only where claimed. | SOL-03, FND-02 |
| IO-02 | P0 | **STL and 3MF manufacturing export.** Expose chord/angular tessellation settings and units; record export provenance. Validate generated files with an independent reader and label tessellated output as mesh geometry. Scope 3MF metadata explicitly. | CORE-05, FND-02 |
| IO-03 | P0 | **Exact measurement.** Query B-Rep distance, angle, length, radius/diameter, area, and volume. Report mass only with declared density and units. Verify analytic fixtures independently of display tessellation and Blender unit presentation. | CORE-07, SOL-02 |
| IO-04 | P0 | **Document recovery and migration.** Provide atomic-save/recovery behavior and migrations for every released schema transition. Corrupt, truncated, unsupported, and cache-free files have documented outcomes and retained originals. | CORE-06 |
| IO-05 | P1 | **CAD Sketcher migration study.** Inspect a pinned upstream version and legally reusable fixtures. Publish a supported mapping and per-item report: parametric, approximate, or mesh reference. Never infer original exact B-Rep history from arbitrary edited meshes. | SK-03, IO-04, FND-02 |
| IO-06 | P1 | **Interoperability corpus.** Add legally redistributable metric/imperial parts, nontrivial assemblies, and edge cases from multiple tools. Record provenance, expected invariants, and known data loss for each fixture. | IO-01, IO-02 |

**Exit gate:** the example part can be inspected exactly, exported, independently opened, re-imported, and checked against published invariants. Imported mesh, imported B-Rep, and native parametric history are visibly distinct states.

## 5 · Earn an MVP release

| ID | Priority | Deliverable and acceptance criteria | Depends on |
| --- | --- | --- | --- |
| REL-01 | P0 | **Regression and failure corpus.** Cover units, expressions, solver degeneracy, feature validity, topology edits, stale IPC, undo, and migration. Geometry fixes include a minimized reproducer and semantic assertions, not only screenshots or raw BREP byte equality. | CORE-06, SK-03, SOL-05, IO-04 |
| REL-02 | P0 | **Build and package matrix.** Produce repeatable packages for each declared target. Run clean-install, upgrade, uninstall, and headless Blender smoke tests; publish dependency pins, notices, checksums, and build/source provenance. Do not advertise an untested platform. | FND-01, FND-02, REL-01 |
| REL-03 | P0 | **Input and process hardening.** Exercise malformed documents/imports/messages, resource limits, core timeouts, cancellation, endpoint isolation, and crash cleanup. A failure cannot overwrite a good document or run embedded expressions as code. | CORE-04, IO-04 |
| REL-04 | P0 | **Performance baselines.** Publish hardware, fixtures, and measurements for sketch solve/drag, incremental recompute, tessellation, long histories, and repeated instances. Adopt budgets from measurements; document any model-size limits. | REL-01 |
| REL-05 | P0 | **Usable installation and learning path.** Verify release instructions on fresh systems and record exact supported versions. Ship a first-part tutorial, recovery guide, diagnostics guide, and known limitations. Include keyboard and contrast/accessibility review. | REL-02, SK-06, SOL-06, IO-03 |
| REL-06 | P0 | **Public alpha gate.** Release only after foundation gates, supported-package smoke tests, golden workflows, and recovery tests pass. Clearly label experimental features and document schema compatibility and known blockers. | REL-02, REL-03, REL-04, REL-05 |
| REL-07 | P0 | **Beta and stable gates.** Define blocker policy, upgrade/rollback behavior, compatibility commitments, and reviewer ownership. Resolve data-loss, silent wrong-reference, unit-conversion, undo-divergence, and packaging blockers before calling a release stable. | REL-06 |

The MVP gate includes constrained planar sketching, expressions, trustworthy feature history, extrude/revolve/Boolean, scoped fillet/chamfer/hole, mirror/patterns, exact measurement, STEP exchange, manufacturing mesh export, persistence, and reliable undo. Deferred features must not become dependencies of that gate.

## 6 · Grow into engineering workflows

These are P1 directions after the MVP foundation. They are separate projects with RFCs, scoped initial releases, and their own correctness gates.

| ID | Direction | Acceptance gate | Prerequisites |
| --- | --- | --- | --- |
| ENG-01 | Sweep, loft, shell, draft, ribs/webs | Degenerate profiles and topology changes have a tested diagnostic policy; new operations preserve reference intent or fail explicitly. | SOL-03, REL-01 |
| ENG-02 | Threads, involute gears, standard parts | Separate cosmetic metadata from modeled geometry. Verify dimensions with independent checks and record redistribution provenance for every data table. | ENG-01, FND-02 |
| ASM-01 | Components and occurrences | Shared part definitions, exact placements, stable instance IDs, suppression, and assembly STEP round trips avoid duplicated authoritative geometry. | IO-01, SOL-03 |
| ASM-02 | Mates and motion | A reviewed rigid-body constraint model reports remaining degrees of freedom and conflicting/redundant mates; rigid/revolute/slider fixtures pass before advanced joints and drive systems. | ASM-01, FND-04 |
| INS-01 | Clearance, interference, sections, and manufacturing analysis | Label exact B-Rep results separately from sampled/mesh analyses; expose analysis resolution and reproducible fixtures. | IO-03, ASM-01 |
| DRW-01 | Associative technical drawings | Base/projected/section/detail views and dimensions update through topology edits. Hidden-line/vector exports, title blocks, BOM, and balloons have verified output fixtures. | SOL-03, ASM-01 |
| MIG-01 | Existing-project migration | Provide explicit mappings and loss reports for pinned CAD Sketcher or Seamless CAD source versions; STEP-based geometry migration precedes unsupported history translation. | IO-05, IO-06 |
| API-01 | Scripting and extension API | Version the command/document boundary, publish examples, and test compatibility without making Blender's mesh cache a geometry API. | REL-07 |
| ADV-01 | Configurations, sheet metal, advanced surfaces, direct editing, CAM/simulation bridges | Separate research RFCs establish data models, interoperability expectations, testing, and maintainers before feature commitments. | REL-07 |

## Work that welcomes new contributors now

No native implementation is needed to make these useful contributions:

- Improve the architecture questions in [research.md](docs/research.md), with primary-source evidence and clearly labeled conclusions.
- Design a small, original part that exposes one geometric edge case; supply dimensions, the intended result, and rights to redistribute it.
- Review a first-part workflow or propose accessible sketch/feature-tree interaction sketches. Mark mockups as mockups.
- Turn one roadmap item into a bounded issue with inputs, expected outputs, failure cases, and a review plan.
- Improve explanations, navigation, terminology, translations, and the difference between planned and available behavior.

## How progress will be reported

Merged implementation and reproducible checks are the evidence of progress. When implementation begins, link roadmap IDs to issues/PRs, record the exact tested versions, and change status only after acceptance criteria pass. New features and changed document semantics should update this roadmap and the relevant ADR together.

Do not equate the number of implemented buttons with CAD reliability. A model that survives a difficult edit, reloads correctly, and tells the truth about a failed reference is a more meaningful milestone.
