# A first measured bracket

**Proposed workflow / mockup.** This story is desk research based on the [roadmap](../ROADMAP.md), [architecture](architecture.md), and [glossary](glossary.md). It describes a future experience for SK-06 and REL-05. No add-on or usability session was used. Adopting this workflow is a Design RFC decision.

A beginner wants a flat mounting bracket with one hole. The bracket should fit a longer mounting surface after an edit, with its thickness, hole diameter, and midpoint alignment preserved.

| Dimension | Initial | After edit |
| --- | --- | --- |
| Length | 60 mm | 70 mm |
| Width | 30 mm | 30 mm |
| Thickness parameter | 5 mm | 5 mm |
| Through-hole diameter | 8 mm | 8 mm |
| Hole center from the fixed corner | 30 mm along length, 15 mm along width | 35 mm along length, 15 mm along width |

| Step | What the beginner does | Expected feedback or question | Proposed roadmap work |
| --- | --- | --- | --- |
| Start the document | Choose millimeters and an XY sketch plane. | Show mm next to inputs and readouts. Confirm that the rectangle starts on the selected plane. | CORE-01, SK-01 |
| Sketch the outline | Anchor one corner at the origin and enter 60 mm by 30 mm. | Label both dimensions and say whether the outline is closed and fixed by its dimensions. If it can still move, name what is free. | SK-02, SK-03, SK-04, SK-06 |
| Set thickness | Create a length parameter called **thickness** with a value of 5 mm. | Show the name, value, and units together. | CORE-02 |
| Extrude | Select the closed outline and use **thickness** as the distance for a new solid. | Preview a single flat solid with an evaluated distance of 5 mm. Applying creates an editable step. Cancel leaves the sketch intact. | SOL-01, SOL-06 |
| Make a through-hole | On the top face, locate the hole at half the rectangle length and half its width, then choose an 8 mm diameter and **Through all**. | Show both openings in the preview and identify the solid being cut. If the face reference is ambiguous, tell the user which selection to repair. | CORE-02, SK-05, SOL-03, SOL-04 |
| Change one dimension | Reopen the outline and change the length to 70 mm. | Preview the longer bracket with the hole still centered and the thickness unchanged. If the edit fails, keep the last committed shape and identify the failed step. | CORE-03, SOL-03, SOL-06 |
| Inspect a measurement | Measure from the fixed end face to the parallel far end face. | Show 70 mm with both faces highlighted and label the readout as a measurement. Changing the length still happens in the sketch. | CORE-07, IO-03 |
| Save and reopen | Save the editable document and reopen it. | Show the same solid, the 70 mm sketch dimension, and the named 5 mm thickness. If reopen fails, preserve the saved original and explain what can be recovered. | CORE-06, IO-04 |
| Export | Export the committed solid to STEP. | Confirm one solid and millimeters. Explain that the STEP file carries the solid geometry and the editable operation history stays in the saved document. | IO-01, REL-05 |

## Wording to try

| Likely sticking point | Proposed wording |
| --- | --- |
| Constraint | **Keep this relationship**. For the hole, **Keep the center halfway along the length and width**. |
| Extrude | **Give the outline thickness**. Show the direction and distance in the preview. |
| Through all | **Cut through the entire part**. Show the entrance and exit in the preview. |

Show feedback as text as well as on the geometry. Let the beginner tab to dimensions and confirm or cancel edits from the keyboard. The finished part should be explainable in one sentence: a 70 by 30 by 5 mm flat bracket with one centered 8 mm through-hole.
