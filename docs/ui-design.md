# Modern interface design

**Status: product design requirements, with a bounded experimental workbench and Blender adapter as the first implementation.** This page describes the intended experience and its acceptance criteria. It does not claim that every control or advanced interaction below already exists. Use the [installation guide](installation.md) for the available scope and the [roadmap](../ROADMAP.md) for `UX-01..04`.

B-CAD should be visually distinctive, easy to learn, and comfortable for precise work. Blender integration and an optional external local interface share one document/controller. A change made through either interface must have the same meaning, validation, units, and resulting geometry.

## Workspace layout

| Region | Purpose | Interaction requirement |
| --- | --- | --- |
| Compact top bar | Document identity, revision/state, units, command search, save/export | Keep the active document and pending changes visible; search should find tools by familiar CAD names |
| Left document tree | Bodies, datums, parameters, imported assets, and eventually features/components | Selection has a readable name and source type; use a tree only when real dependencies exist |
| Central viewport | Geometry, selection, grid/axes, dimensions, contextual tools | Preserve space for the model; provide discoverable orbit/pan/zoom and fit/view controls |
| Right inspector | Selected object, source expressions, evaluated dimensions, operation settings | Show units beside values; errors stay beside the relevant field; keyboard order follows the workflow |
| Contextual action area | Preview, Apply, Cancel, recovery actions | Make committed and tentative changes distinguishable; a failed operation cannot appear successfully committed |
| Status/diagnostic area | Kernel state, import losses, failed features, stale geometry | State what happened and a concrete recovery action; reserve technical details for an expandable view |

The first primitive experiment needs a small, honest document/parameter inspector. A decorative timeline of nonexistent modeling operations would misrepresent its capabilities. Add a feature timeline when the controller actually implements editable feature history.

## Visual system

Use deep neutral surfaces, crisp typography, restrained accent color, and a viewport that gives the model visual priority. Use consistent spacing and a small set of control sizes. Selected geometry, hover, pending previews, committed results, warnings, and failure must have distinct treatments that remain understandable in grayscale.

Dimensions need solid backgrounds or another legibility treatment when geometry crosses them. Small labels must scale with UI settings. Prefer tabular numerals for measurements and normal prose for explanations. Decorative motion should be brief and honor reduced-motion preferences; it must not delay modeling or hide recompute state.

Avoid filling the interface with advanced controls before they are relevant. Searchable commands and contextual inspectors can reveal depth without making a first-part workflow overwhelming. Preserve a visible route to exact numeric input even when a drag handle offers a convenient preview.

## Precision interaction

- Show the entered expression and its evaluated quantity together, such as `plate_width / 2` and `40 mm`.
- Keep displayed decimals separate from stored precision. A shortened label must not imply the value was rounded in the document.
- Show degrees/radians explicitly when angle entry is supported. Never treat an untyped length expression as an angle.
- Define what a measurement means: shortest distance, projected distance, axis distance, signed angle, or unsigned angle.
- Let users discover reference identity and selection filters; a face index in a temporary mesh is not a stable mechanical reference.
- Keep preview, Apply, Cancel, undo, and save behavior consistent across the Blender and external interfaces.
- Preserve the last committed document when an input or geometric operation fails. Mark any displayed last-good mesh as stale if it no longer represents the attempted edit.

Selected edge/face measurements, snapping, sketch constraints, and dimension dragging depend on the corresponding geometry and reference work. A visually convincing overlay is insufficient evidence of exact selection.

## Native Blender interface

Use supported [panels and UI layouts](https://docs.blender.org/api/5.1/bpy.types.UILayout.html), operators, and [gizmos](https://docs.blender.org/api/5.1/bpy.types.Gizmo.html) for a focused adapter. The first acceptance workflow is: configure the isolated worker, create a dimensioned part, change a parameter, rebuild its display, undo/redo, save/reload, and disable/re-enable without leaving duplicate resources.

Test viewport draw handlers, event handling, file handlers, and registration cleanup against the exact Blender build being advertised. The prototype targets a Blender 5.1 experiment; only recorded checks establish the tested baseline. Heavy geometry and process communication must respect Blender's execution model. Its [threading guidance](https://docs.blender.org/api/5.1/info_gotchas_threading.html) documents why background Python code cannot freely manipulate the host.

## Optional external local workbench

A browser or later desktop companion gives the interface its own layout, styling, and interaction system while Blender remains available for scene/display workflows. The initial buildless browser front end is an experiment in this direction. It calls the real local controller; the preview comes from evaluated B-Rep tessellation and measurements come from exact-body queries.

This does not require an embedded WebView inside Blender. No HTML embedding or new Blender editor type is promised. Decide desktop packaging only after the prototype answers the workflow and distribution questions.

The local workbench acceptance target includes:

- Local-only listening, per-session isolation, controlled asset access, bounded input, and a clear shutdown path.
- Revision-tagged state so old results cannot replace the current model.
- A shared validation and document format, with no independent browser geometry authority or competing undo history.
- User-visible missing-worker, invalid-input, import-loss, failed-geometry, and reconnect states.
- Locally loaded assets and an offline workflow; hosting the contributor website does not host users' CAD files.

These are acceptance targets, not an assertion that the experiment has completed the production hardening gate.

## Usability evidence

Test one measured part from creation through export; a parameter expression; a failed edit; undo/redo; save/reopen; and an imported base body. Add sketch, selection, and feature-tree scenarios as those systems become real. Capture the exact build and observed result.

Keyboard access, focus visibility, contrast, readable error messages, scalable text, and non-color state cues are part of the gate. Measure first-use friction with concrete tasks, such as finding diameter input or recovering from an oversized hole. Record the problem and the change that resolved it. A desktop screenshot alone cannot prove an intuitive interface.

The [product vision](vision.md) supplies the wider workflow map. The [prototype decision](decisions/0002-first-prototype.md) explains the current implementation boundary.
