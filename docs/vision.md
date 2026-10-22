# Product vision and capability map

B-CAD aims to make precise, expressive mechanical design accessible inside Blender, with a modern local companion interface when that produces a better workflow. The long-term ambition is broad enough to cover the kinds of work people perform in Fusion: modeling, assemblies, drawings, inspection, and connected engineering workflows. This is a direction for development, not a claim of present feature parity.

The repository has an **experimental first prototype**. Its bounded primitive modeling, parameter editing, exact-body exchange, persistence, and display bridge are the first foundation. A general sketch solver, durable feature references, assemblies, and production release remain roadmap work. Read the [installation status](installation.md), [roadmap](../ROADMAP.md), and [first prototype decision](decisions/0002-first-prototype.md) before choosing it for a workflow.

## What the experience should feel like

Open a document, understand its units immediately, find a tool by name or purpose, and enter a dimension directly. Select a face, edge, or datum and see meaningful options beside the model. A parameter change should show what depends on it, what changed, and what needs repair. Precise work should remain comfortable at small and large scales without making users fight scene units, ambiguous selections, or hidden rounding.

The interface should have its own visual identity: a calm viewport, strong hierarchy, legible dimensions, generous controls, useful motion, and clear selection and error states. [UI design](ui-design.md) describes the interaction targets. Blender integration remains a core part of the project; a separate local workbench can share the same document/controller rather than forcing the entire product into a narrow sidebar.

## Precision is a model property

Explicit units, typed expressions, declared tolerances, and exact B-Rep queries define engineering behavior. Display meshes and rounded labels help users see the part. Changing viewport tessellation, zoom, or display units must not change a stored mechanical dimension. Geometric tolerance, manufacturing clearance, and the number of displayed decimals have different meanings.

The initial prototype's body metrics are only a first step. The measurement target also includes selected edge lengths, point/line/face distances, radii and diameters, line/plane angles, projected distances, sections, and interference. Each needs a declared selection scope, reference behavior, and analytic checks. See `CORE-02`, `CORE-07`, `IO-03`, and `INS-01` in the [roadmap](../ROADMAP.md).

## Long-term capability map

Autodesk groups Fusion into several [purpose-specific workspaces](https://help.autodesk.com/view/fusion360/ENU/?contextId=GS-WORKSPACES). That is a useful way to make the breadth of the ambition visible. The following is B-CAD's own planning map, with independent implementation and verification required for each area.

| Workflow | Target capabilities | Current boundary / roadmap |
| --- | --- | --- |
| Precise sketching | Lines, arcs, splines, constraints, dimensions, construction geometry, projections | Solver and persistent references planned: `SK-01..06` |
| Parametric solid design | Extrude/revolve, booleans, fillet/chamfer, holes, patterns, editable dependencies | Experimental primitives first; general history and robust references: `SOL-01..06` |
| Complex shapes | Sweep, loft, shell, draft, ribs, surfaces, continuity tools, direct editing | Scoped future projects: `ENG-01`, `ADV-01` |
| Mechanical generators | Involute gears, threads, fasteners, standard parts, configurable families | Spur gears first with measurable geometry; advanced families later: `ENG-02` |
| Assemblies and motion | Components, instances, mates, degrees of freedom, interference, exploded views | Independent assembly model and fixtures: `ASM-01..02`, `INS-01` |
| Technical documentation | Associative views, dimensions, sections, tolerances, BOMs, vector output | Drawing data model and output verification: `DRW-01` |
| Engineering exchange | STEP, scoped drawing/profile formats, manufacturing meshes, loss reports | STEP base geometry and STEP/STL slice first; metadata/history promises require fixtures: `IO-01..07` |
| Sheet metal and configurations | Thickness/bends, unfolding, configurable dimensions and suppression | Separate RFCs and geometric gates: `ADV-01` |
| Rendering and animation | Materials, lighting, presentation, exploded assembly animation | Build on Blender; validate the CAD-to-display and placement bridge first |
| Simulation and optimization | Analysis preparation, materials, boundary conditions, solver bridges, result provenance | Longer-term research with independent verification: `ADV-01` |
| Subtractive manufacturing | CAM bridges, setups, toolpaths, inspection, verified postprocessing | Separate research scope after reliable CAD: `ADV-01` |
| 3D printing | Slicer handoff; later plates, FDM/resin preparation, layers, optional connections | Deliberately deferred P2: [printing roadmap](printing-roadmap.md), `PRINT-01..07` |
| Electronics and generative workflows | Mechanical/electrical interchange and exploratory design integration | Aspirational research; no selected implementation or support commitment |
| Automation and collaboration | Versioned commands, reproducible documents, extensible tooling, reviewable changes | Shared controller first; supported API later: `API-01` |

## Importing a CAD file is not importing its design history

Users need a predictable way to bring in existing work. Each import/export route should state what survives and what is lost before the user depends on it. Native B-CAD documents, imported B-Rep bodies, and mesh references must remain visibly different in the interface.

| Format family | Intended treatment | Fidelity boundary |
| --- | --- | --- |
| B-CAD versioned JSON | The prototype's editable primitive document and source assets | Experimental schema; not a stable interchange standard or promised future migration path |
| STEP / STP | Exact imported base geometry; STEP export | No reconstructed original sketch/features; hierarchy, names, colors, PMI, and units require separately verified scope |
| IGES | Later geometry-exchange study | Not enabled merely because OCCT can read a format; surfaces, healing, and assembly losses need fixtures |
| DXF / SVG | Later scoped 2D profiles/drawing exchange | Supported entities, scale, text, layers, curves, and approximations need a published matrix |
| STL / OBJ / 3MF | Manufacturing/display mesh workflows; STL export first | Triangles are not exact CAD history; STL has no standard unit declaration; slicer-specific 3MF settings require separate support |
| Fusion F3D/F3Z, SolidWorks files, FreeCAD FCStd, other native projects | Dedicated feasibility and migration work per format/version | No blanket native-file or history compatibility; legal interfaces, dependencies, source assets, and unsupported features must be reported |

CadQuery's [format documentation](https://cadquery.readthedocs.io/en/latest/importexport.html) distinguishes geometry exchange from its own parametric representation. B-CAD must expose its own tested subset rather than advertise every format supported by an underlying library. Autodesk's [import lesson](https://help.autodesk.com/lessons/Fusion-Portal_NA_ENU/sim-imported-geometry/import-geometry/Imported-Geometry-Autodesk-Non-Native.pdf) also illustrates why native archives and neutral geometry have different history behavior. The `IO-07` compatibility report is the acceptance gate for wider claims.

## Priorities

First earn trust in units, parameter edits, exact results, save/reload, undo, diagnostics, and installation. Then expand constrained sketches and mechanical features. Make modern interaction part of those workflows from the beginning. Advanced engineering subsystems need their own maintainers and correctness gates. Integrated 3D printing remains a later P2 project; useful geometry export can serve existing slicers sooner.

Contributors can turn one real modeling problem into a fixture, a small feature, a UI improvement, or a documented compatibility test. Follow the [contribution guide](../CONTRIBUTING.md) and tie the change to an observable [roadmap](../ROADMAP.md) outcome.
