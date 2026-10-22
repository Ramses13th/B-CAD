# Later 3D printing workspace

**Priority: P2, deliberately deferred until reliable mechanical CAD.** B-CAD may eventually help prepare FDM and resin jobs as well as design the parts. This direction is separate from the first CAD implementation and cannot become a prerequisite for its MVP. The [main roadmap](../ROADMAP.md#7-printing-workspace-p2-deliberately-later) defines `PRINT-01..07` and their dependencies.

Useful manufacturing export comes earlier. Users should be able to pass explicit-unit, controlled-tessellation geometry to an existing slicer without waiting for B-CAD to implement slicing, printer management, or profiles. The first prototype's STEP/STL exchange is a limited foundation; 3MF project compatibility remains separately scoped.

## Workflow lessons to study

| Reference | Useful lesson | B-CAD research question |
| --- | --- | --- |
| [Bambu Studio feature overview](https://github.com/bambulab/BambuStudio/blob/master/README.md) | Multi-plate organization, arrangement/orientation, support choices, material assignment, and inspectable setting scopes | Can users prepare several parts without confusing design geometry, plate transforms, and process settings? |
| [PrusaSlicer 3MF projects](https://help.prusa3d.com/article/saving-projects-as-3mf_1773) | Retain objects, settings, and modifiers as a reproducible preparation project | Which settings and assets must B-CAD retain, and what survives interchange with a particular slicer/version? |
| [PrusaSlicer variable layers](https://help.prusa3d.com/article/variable-layer-height-function_1750) | Combine automatic adaptation with direct editing and visual feedback | Can users inspect the resulting layer plan and understand the quality/time tradeoff? |
| [Lychee manual supports](https://docs.mango3d.io/doc/resin-documentation/resin-support/manual-supports/) and [islands](https://docs.mango3d.io/doc/resin-documentation/resin-support/island/) | Combine support editing with layer-sensitive diagnostics | How are unsupported regions reported, reviewed, and rechecked after geometry or layer-height changes? |
| [Anycubic Photon Workshop manual](https://wiki.anycubic.com/mono4/anycubic_photon_workshop-en-v0.2.0-a.pdf) | Resin preparation, hollowing, drainage, supports, and process profiles | Which analyses can be reproduced independently for a declared printer/process scope? |

These are primary references for workflow study, not affiliations or blanket compatibility claims. Implement original interaction and visuals. Reusing source code, profiles, plug-ins, or data requires an explicit license and distribution review. Bambu Studio's repository identifies AGPL licensing and an optional networking component with non-free dependencies; availability on GitHub does not make all components interchangeable with B-CAD's distribution.

## Staged work

| Task | Initial scope | Evidence before support is advertised |
| --- | --- | --- |
| `PRINT-01` Slicer handoff | STEP and manufacturing meshes, scale/orientation, approximation settings, format losses | Independent reader/slicer opens fixtures at intended dimensions; advertised 3MF metadata is checked |
| `PRINT-02` Preparation projects | Build volume, plates, orientation, copies, packing, retained settings | Save/reopen preserves setup; an upstream CAD edit invalidates stale preparation visibly |
| `PRINT-03` FDM preparation | Material/nozzle/printer profiles, supports, modifiers, variable layers, multi-material assignments | Effective settings are inspectable; fixtures produce reviewed output for each declared process |
| `PRINT-04` Resin preparation | Hollowing, wall/drain checks, trapped regions, islands/suction analysis, supports and rafts | Resolution and limitations are visible; minimized success/failure fixtures can be reproduced |
| `PRINT-05` Slicing integration | Compare external handoff, documented CLI/library, and new-engine approaches | Review licenses, packaging, profile provenance, cancellation, and deterministic golden outputs |
| `PRINT-06` Preview | Actual layers/toolpaths, material changes, support regions, estimates | Parse real output and compare it with an independent viewer; label estimation assumptions |
| `PRINT-07` Optional connection | Local file transfer, status, and monitoring through documented interfaces | Explicit machine compatibility, user-initiated send/print, recoverable connection failures, offline path |

Each row is planned work. No slicing engine, printer integration, or vendor-native print-project support is claimed for the first prototype.

## Keep design and preparation distinct

The CAD document owns mechanical intent. The printing project references a specific design revision and adds plate transforms, material assignments, supports, profiles, and process-specific preparation. A nozzle change must not silently change a modeled hole diameter; an upstream part edit must not silently reuse a stale slice.

An exact CAD shell and a sampled resin-hollowing result have different semantics. Show which representation an operation produced, what resolution was used, and whether the result remains editable as CAD. Physical design clearance, mesh approximation, layer height, and resin/FDM process compensation must remain separate values.

3MF is a container used for multiple purposes. A valid geometry export does not guarantee preservation of Prusa/Bambu/Anycubic/Lychee settings, supports, colors, thumbnails, or proprietary extensions. Publish support by format, producer/version, direction, and retained fields. See the [CAD compatibility matrix](vision.md#importing-a-cad-file-is-not-importing-its-design-history) and `IO-07`.

## Scope and priorities

The early priority remains reliable CAD: units, solver behavior, robust feature references, exact measurements, document recovery, undo, packaging, and clear diagnostics. The printing phase starts only when those foundations and its own maintainer capacity exist. Contributors can improve the research now without committing the project to a slicer engine or schedule.

Use a [design RFC](../CONTRIBUTING.md#propose-before-building-a-foundation) for a bounded proposal with one process, legal fixtures, expected output, failure behavior, and a license review. Keep direct printer actions separate from preparation and preserve a useful offline export route.
