# ADR 0002 · A bounded exact-CAD prototype with shared interfaces

- **Status:** Accepted for the first experiment; not a production architecture freeze
- **Scope:** Primitive document/controller, isolated exact-geometry worker, Blender adapter, optional local browser workbench
- **Related decisions:** [ADR 0001](0001-cad-architecture.md), [architecture proposal](../architecture.md), [roadmap](../../ROADMAP.md)
- **Evidence:** The [development guide](../development.md) records runnable checks and the [installation guide](../installation.md) records exact tested versions and limitations. This ADR does not itself assert a passing Blender or platform result.

## Context

B-CAD needs working code that tests the central boundary: a document expresses a dimensioned part; an isolated geometry process evaluates it; Blender and another interface can display the same result. Starting with a general sketch solver, complete topology naming, broad file compatibility, and desktop packaging would obscure that experiment.

The owner requested initial implementation, a more modern interface even if external, precise mechanical modeling, broader future CAD compatibility, and a much later printing workspace. This decision defines a small implementation of that direction. It does not adopt every planned subsystem in [ADR 0001](0001-cad-architecture.md).

## Decision for this experiment

1. Use a shared Python document/controller whose non-geometric behavior uses the standard library. It owns validation, typed parameter expressions, committed state, revisions, and undo/redo. JSON is data; imported expressions and documents are never executed as Python programs.
2. Evaluate exact geometry in a separate CPython process with **CadQuery 2.8.0** and **cadquery-ocp 7.9.3.1.1** pinned for the experiment. OCP provides the OCCT binding. This dependency environment is separate from Blender's embedded Python.
3. Use protocol version 1 over child-process standard input/output: newline-delimited JSON requests and responses, with protocol diagnostics kept out of the message stream. Scope the protocol to declared commands and reject malformed or unsupported input. The wire schema is experimental.
4. Begin with a parameterized box, cylinder, and rectangular plate with a centered through-hole. Produce a valid exact body, body metrics, and replaceable tessellated display geometry. This is a small family of part definitions, not a general feature dependency graph or constrained-sketch system.
5. Implement STEP import as an explicitly non-parametric exact base asset, preserving the required source data with the document. STEP export retains exact geometry; STL export is tessellated. No arbitrary CAD-project history translation is implied.
6. Provide versioned JSON document save/load and bounded undo/redo for the implemented edits. A rejected edit must preserve the committed state. Future schema compatibility and recovery guarantees require their full roadmap gates.
7. Connect a focused Blender adapter and a local buildless HTML/CSS/JavaScript workbench to the shared controller. Neither interface owns a competing CAD model or invents exact measurements from preview meshes. The external UI is optional; it is not embedded HTML inside Blender.

The Blender experiment targets a **5.1 baseline**. Targeting a version is not evidence of compatibility. Check registration, actual geometry display, a dimension edit, undo/redo, save/reload, and cleanup using an installed build before documenting the precise supported experimental combination.

## Why this choice

CadQuery exposes OCCT modeling and exchange in a form that can make a narrow vertical slice reproducible without first writing a C++ application and its full packaging toolchain. The [CadQuery format documentation](https://cadquery.readthedocs.io/en/latest/importexport.html) supports geometry interchange while distinguishing it from parametric representation. The [CadQuery 2.8.0 package](https://pypi.org/project/cadquery/2.8.0/) and [OCP 7.9.3.1.1 package](https://pypi.org/project/cadquery-ocp/7.9.3.1.1/) provide specific experiment pins; they are not claims that these are the newest releases or a completed transitive-license audit.

Standard input/output gives each host-launched worker a simple process boundary for the initial experiment. It avoids requiring a persistent shared geometry service. A future transport, asynchronous evaluation, cancellation, large geometry streaming, crash recovery, and distribution strategy still require evidence under `FND-06` and `CORE-04`.

Blender's [5.1 API](https://docs.blender.org/api/5.1/) supplies native interaction/display integration. A separate local browser interface can test a richer layout using the same commands without assuming arbitrary HTML embedding in host panels. Its isolation and hardening must be verified before wider distribution. See the [UI requirements](../ui-design.md).

## Acceptance evidence

The prototype should demonstrate the following with actual code and fixtures:

- Analytically check a box, cylinder, and plate-with-hole: valid solid count, bounds, area/volume where defined, and parameter changes.
- Reject invalid dimensions, non-finite values, dimensional-expression errors, code-like input, unsupported schema, and malformed protocol messages.
- Export STEP, import it again as base geometry, compare declared invariants, and export a mesh with documented approximation/units.
- Save/reopen a document, retain imported source data, undo/redo edits, and regenerate display geometry from committed state.
- Exercise both interfaces against real worker results; record exact toolchain and Blender builds, commands, results, and limitations.
- Run the documentation checks and ensure installation/status pages describe the actual implemented scope.

The development record is the evidence source. Do not turn the list into a success claim without those results.

## Explicitly outside this decision

A complete constraint solver, arbitrary sketch/profile extraction, general modeling history, persistent face/edge references, assemblies, source-application project migration, production binary distribution, integrated slicing, and printer control are not delivered by this primitive experiment. Native STEP input remains base geometry. Initial JSON schema and protocol versions may change as the experiment answers its questions.

This ADR does not mark the original 48 roadmap tasks complete. It provides partial evidence toward the relevant foundation, core, interaction, and interchange targets. Correctness and recovery gates take precedence over expanding the number of tools.

## Revisit after the first slice

Record what the experiment showed about process startup, dependency footprint, cross-interface document behavior, units, import/source retention, and Blender cleanup. Then choose the next bounded step: solver evaluation, general feature semantics, robust references, or packaging. Use new decision records for production commitments; preserve the [long-term capability map](../vision.md) and deferred [printing direction](../printing-roadmap.md) as goals with separate gates.
