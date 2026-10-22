# ADR 0001 · Separate CAD truth from Blender display

- **Status:** Proposed; not adopted as a proven implementation
- **Scope:** Initial architecture direction
- **Implementation:** None yet
- **Related work:** [Architecture](../architecture.md), [research register](../research.md), [roadmap](../../ROADMAP.md)

## Context

B-CAD begins as a blueprint for parametric mechanical CAD inside Blender. A useful system needs dimensioned sketches, editable feature dependencies, precise engineering queries, robust references, persistence, and reliable undo. A UI that resembles CAD is insufficient if changing a dimension attaches a hole to the wrong face or a crash loses the model.

The supplied project blueprint recommends a separate geometry core and a canonical parametric document. It is input to this proposal, not an executable specification, an authoritative release calendar, or a promise of current functionality. Its version, licensing, packaging, and solver claims need independent verification before adoption.

OCCT documents modeling operations and generated/modified/removed shape history. OCAF documents reference-key-driven data and topology evolution. These provide useful building blocks, but do not prove a complete persistent-reference solution for our intended edit workflows. See [OCCT modeling algorithms](https://github.com/Open-Cascade-SAS/OCCT/blob/master/dox/user_guides/modeling_algos/modeling_algos.md), [BRepTools_History](https://www.occt3d.com/dev/doc/refman/html/class_b_rep_tools___history.html), and [OCAF](https://occt3d.com/dev/doc/overview/html/occt_user_guides__ocaf.html).

## Proposal

Adopt these boundaries after the foundation experiments pass:

1. **Blender hosts interaction.** Its tools, operators, viewport, materials, scene, and downstream mesh workflows integrate with the CAD system through an adapter.
2. **A versioned document records design intent.** Stable IDs, explicit units, typed parameters, source assets, feature definitions, and dependencies survive without display caches. A DAG governs evaluation; a linear feature tree is a UI view where appropriate.
3. **An isolated native process evaluates exact geometry using OCCT.** The process exposes controlled commands, exact queries, validation, exchange, tessellation, and operation-history data through a versioned local protocol.
4. **Evaluated B-Rep is geometry truth; Blender meshes are caches.** Mesh edits do not implicitly change the CAD document, and exact operations do not silently become mesh operations.
5. **Persistent references carry semantic intent.** Use feature/entity provenance and operation history, evaluate OCAF/TNaming, and expose ambiguity as an explicit failure. Index-based or nearest-face guesses cannot silently retarget features.
6. **One canonical transaction owns every edit.** Blender undo/redo restores a document revision and resynchronizes the core. The native service cannot create a competing user-visible history.
7. **Solver semantics remain behind an adapter.** Evaluate SolveSpace/libslvs and PlaneGCS before selecting the initial backend or freezing sketch serialization.

## Why this direction

The boundary permits exact engineering queries and explicit parametric semantics while preserving Blender's strengths as an interaction and visualization host. It also makes native dependency management, process crashes, host compatibility, and schema migration visible engineering concerns from the start.

Isolating the core avoids an architectural dependence on Blender's embedded Python ABI for native CAD libraries. It creates the possibility of independent native builds and a standalone recovery/migration tool. Those advantages must be weighed against IPC, memory, latency, packaging, and lifecycle costs in real prototypes.

## Alternatives considered

| Alternative | Benefit | Reason it is not the preferred starting proposal |
| --- | --- | --- |
| Mesh/BMesh as authoritative CAD geometry | Close integration with Blender tools | Requires a separate solution for exact surfaces, engineering exchange, semantic references, and robust feature evaluation; mesh tessellation becomes entangled with design intent |
| Load a native CAD stack directly in Blender | Less IPC and simpler direct calls | Couples native library loading/crashes and packaging more closely to the host; retain as an alternative if process costs prove unacceptable |
| Embed a full existing CAD application | Reuse mature infrastructure | Imports a much larger application/runtime boundary and integration scope; research individual reusable components first |
| Use CadQuery as the complete kernel boundary | Productive scripting/prototyping | CadQuery is a higher-level framework over OCCT, not a substitute for the document, transaction, and reference semantics we must define; it remains a candidate prototyping/scripting tool |
| Build a new geometry or sketch solver immediately | Maximum internal control | High mathematical and validation cost without evidence that existing components are inadequate |

## Consequences and costs

- Contributors must keep canonical intent, evaluated exact state, and display caches distinct.
- IPC needs revision checks, cancellation, isolation, crash recovery, and bounded input handling.
- Native binaries require per-target builds, dependency provenance, notices, and verified distribution rules.
- Persistent naming, undo divergence, unit mistakes, and migration are early release gates, not cleanup tasks.
- The project must budget for diagnostics and regression models alongside feature code.
- Failure may remain explicit where topology intent is ambiguous; no universal reference-persistence guarantee is made.

## What this record does not decide

This ADR does not select exact Blender/OCCT versions, supported operating systems/architectures, solver backend, IPC transport/encoding, document container or extension, canonical length unit, numeric tolerance policy, build system, final repository layout, binary release channel, or third-party licensing outcome. It also does not adopt the source blueprint's staffing estimates or delivery dates.

The repository's own license is governed by its published license file. That choice alone does not approve a dependency, imported code, data table, model fixture, or binary distribution.

## Evidence required for adoption

| Evidence | Roadmap work |
| --- | --- |
| Build a solid, validate/query/tessellate it, and round-trip STEP from a clean native build | FND-02, FND-03 |
| Compare solver behavior and integration costs on shared fixtures | FND-04 |
| Review the document schema, revision/transaction semantics, and recovery inputs | FND-05 |
| Demonstrate two isolated sessions, stale-result rejection, cancellation, crash, restart, and shutdown | FND-01, FND-06 |
| Exercise split/merge/suppress/pattern edits without silent reference retargeting | FND-07 |
| Prove the complete edit → undo/redo → save/reopen → core restart sequence | CORE-06 |

Review should link reproducible code, pinned dependencies, environment details, results, and known failures. A maintainer can change this ADR to accepted once that evidence supports the direction; failed experiments may revise or replace the proposal. New ADRs should record specific choices instead of silently turning this proposal into a retrospective claim.
