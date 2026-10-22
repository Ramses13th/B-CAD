# CAD and project glossary

| Term | Meaning in B-CAD's proposed design |
| --- | --- |
| B-Rep | Boundary representation: a solid described by geometric surfaces and topological faces, edges, and vertices. |
| CAD core | The proposed external process that evaluates exact geometry and returns results and diagnostics. |
| Constraint | A relationship such as coincidence, tangency, a distance, or an angle that restricts sketch geometry. |
| DAG | Directed acyclic graph. Features depend on upstream inputs, with no circular dependency. |
| Degree of freedom (DOF) | An independent motion or variable still available to a sketch or assembly. |
| Feature | A modeling operation with persistent identity, inputs, parameters, and outputs. |
| Feature history | The design operations and dependencies stored in a CAD document; separate from the UI undo stack. |
| Kernel | The geometry engine that computes and validates shapes. OCCT is the proposed exact geometry kernel. |
| MVP | Minimum viable product: a useful, validated workflow that meets the roadmap's release gates. |
| OCCT | Open CASCADE Technology, the proposed open-source geometry engine. |
| Parametric | Geometry driven by dimensions, relationships, expressions, and editable design operations. |
| Persistent reference / TopoRef | A semantic reference to geometry intended to survive valid upstream edits, or fail visibly if ambiguous. |
| Recompute | Evaluate affected features after a parameter or input changes. |
| RFC | Request for comments: a public design proposal with alternatives, risks, and acceptance criteria. |
| STEP | A CAD exchange format; importing a solid does not automatically recover its original feature history. |
| Tessellation | A polygonal approximation of exact geometry for display or downstream mesh workflows. |
| Tolerance | An explicit bound used in geometric computations; it must not be confused with display precision. |
| Transaction | A complete, reversible document edit with a defined success or failure boundary. |

Read [architecture](architecture.md) for relationships between these concepts and the [roadmap](../ROADMAP.md) for planned implementation.
