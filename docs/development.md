# Development setup

B-CAD has an **experimental exact-CAD slice** alongside the contributor website. A shared Python document/controller calls a separate CadQuery/OCP worker. The local browser workbench and Blender adapter consume actual geometry and document state. The scope and remaining gaps are defined in [ADR 0002](decisions/0002-first-prototype.md), the [installation guide](installation.md), and the [roadmap](../ROADMAP.md).

## Get the repository

Fork on GitHub if you plan to submit a pull request, then clone your fork. To inspect upstream:

```sh
git clone https://github.com/Ramses13th/B-CAD.git
cd B-CAD
git switch -c feature/your-change
```

Read [CONTRIBUTING.md](../CONTRIBUTING.md), [AGENTS.md](../AGENTS.md), and the affected design documents before changing the model or process boundary. Define one user-visible behavior and how it can fail. Keep experimental behavior distinct from the full roadmap target.

## Exact-CAD environment

Use ordinary **CPython 3.13** for the current experiment. Keep native geometry dependencies outside Blender's Python. From Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-core.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On macOS/Linux use `.venv/bin/python`:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-core.txt
.venv/bin/python -m unittest discover -s tests -v
```

The pair is `cadquery==2.8.0` and `cadquery-ocp==7.9.3.1.1`. Do not independently upgrade OCP across CadQuery's supported range. Keep package/license provenance in review; a working wheel does not complete binary redistribution checks. This is a source workflow, not a cross-platform support claim.

Tests exercise implemented behavior: analytic solids, tessellation versus exact metrics, STEP round trips and units, binary STL, invalid inputs, and actual worker protocol output. Read the test files before adding assertions. Test geometry and document semantics rather than screenshots, byte-identical BREP, or a second copy of the implementation.

## Run the workbench

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m bcad.server
```

The service opens `http://127.0.0.1:8765` by default; use the printed URL if you change its port. Add `--no-browser` for automated checks or `--port 8766` to select another local port. No front-end package manager or build step is required. Stop with `Ctrl+C`. The workbench uses shared document validation and the same worker boundary as the Blender adapter. Its preview is evaluated B-Rep tessellation. Do not derive engineering measurements from preview coordinates or create a second browser-only CAD authority.

The external interpreter defaults to the service interpreter. `--core-python` or `BCAD_CORE_PYTHON` can select another one; Blender uses its add-on preference. The selected worker environment needs the pinned native dependencies.

## Worker protocol

For an interactive protocol experiment:

```powershell
.\.venv\Scripts\python.exe -m bcad.kernel_worker
```

The worker reads newline-delimited JSON on standard input and emits one JSON response per request. Add `--once` for one request. This PowerShell example queries its runtime capabilities:

```powershell
'{"protocol":1,"id":"development-ping","revision":0,"op":"ping"}' | .\.venv\Scripts\python.exe -m bcad.kernel_worker --once
```

Native diagnostics go to standard error. Requests carry a protocol version, ID, revision, operation, and operation-specific payload. Operations are `ping`, `evaluate`, `import_step`, `export_step`, and `export_stl`. Inspect the worker/tests for the wire schema and bounds; it is experimental, not a stable extension API.

The controller client starts a one-shot child per geometry request with a timeout. Native library loading takes several seconds and requests are synchronous. Persistent/asynchronous lifecycle, cancellation, richer recovery, and production performance remain open. A subprocess boundary does not authorize background code to change Blender data.

## Build and check the Blender adapter

Generate the archive:

```sh
python tools/package_addon.py --output work/bcad-addon.zip
```

It contains adapter/shared Python code and expects the external worker environment. It is a development artifact, not a stable binary release. Follow the [Blender setup](installation.md#3-build-and-install-the-blender-adapter) and select the absolute external Python path.

The first baseline targets Blender 5.1. A host smoke test must install/register, create supported parts, change a dimension, regenerate display, undo/redo, import/export `.bcad`, save/reopen, and cleanly unregister. Record the exact build and which portions were actually run. The first panel has no STEP exchange buttons; use the workbench. Millimeter parts may look tiny beside the default cube: select the generated object and use **Numpad .** or **View → Frame Selected**.

### Reproduce the Blender smoke check

From the repository root in PowerShell, build and extract the actual archive, then point Blender to the extracted package and external interpreter:

```powershell
python tools/package_addon.py --output work/bcad-addon.zip
Expand-Archive -LiteralPath work/bcad-addon.zip -DestinationPath work/addon-test -Force
$env:BCAD_ADDON_DIR = (Resolve-Path -LiteralPath work/addon-test).Path
$env:BCAD_CORE_PYTHON = (Resolve-Path -LiteralPath .venv/Scripts/python.exe).Path
& 'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe' --background --factory-startup --python-exit-code 1 --python tests/blender_smoke.py
```

Adjust the Blender executable path for your installation. `BCAD_ADDON_DIR` is the extracted archive's parent containing `b_cad`, not the source adapter directory. A passing script prints `BCAD_BLENDER_SMOKE_PASS` followed by the Blender version. It writes fixtures under ignored `work/blender-smoke/`.

On **2026-10-22**, this archive-based check passed on **Windows x64, external CPython 3.13.5, Blender 5.1.0**, Blender build hash **`adfe2921d5f3`**, build date **2026-03-17**. It checked registration, an 80 × 50 × 8 mm plate with a Ø12 mm hole against analytic volume and a 0.08 m Blender X dimension; a width change to `100 mm` with depth `width / 2` updating the same object; invalid `300 mm` hole rejection preserving both committed document and mesh; `.bcad` export/import; `.blend` save/reopen followed by recompute; and clean unregistration. A simulated file-replacement failure also preserved the previous `.bcad` bytes and left no temporary file; project saving uses a flushed sibling temporary file and atomic replacement.

Blender operators declare undo support, but this background script does **not** verify interactive Blender undo/redo or sidebar usability. Those remain manual checks. The browser controller has its own transaction tests; passing them does not establish Blender's interactive undo behavior.

## Documentation-only environment

Documentation contributors do not need Blender/CadQuery. Python 3.11 or newer and the pinned Markdown package suffice. An external environment keeps workflows separate:

```powershell
python -m venv ..\docs-venv
..\docs-venv\Scripts\python.exe -m pip install -r requirements.txt
..\docs-venv\Scripts\python.exe tools/check_docs.py
..\docs-venv\Scripts\python.exe tools/build_site.py --output work/site
..\docs-venv\Scripts\python.exe tools/check_docs.py --site work/site
```

On macOS/Linux substitute `../docs-venv/bin/python`. The checker validates links, anchors, and generated search coverage. The builder indexes Markdown under `docs/` automatically. These checks establish documentation consistency, not geometry/Blender correctness.

Preview the generated hub:

```sh
python -m http.server 8000 --bind 127.0.0.1 --directory work/site
```

Open `http://127.0.0.1:8000`, then review desktop/narrow widths, links, search, and keyboard access. Keep generated output under `work/`; edit source documents/assets.

## Where to contribute

| Path | Responsibility |
| --- | --- |
| `bcad/quantities.py` | Restricted length expressions and unit conversion |
| `bcad/model.py` | Document validation, committed transactions, embedded sources, undo/redo |
| `bcad/core_client.py` | Bounded external Python subprocess requests |
| `bcad/kernel_worker.py` | Actual geometry, validation, metrics, tessellation, exchange |
| `bcad/server.py` | Local workbench service; inspect its API before changing requests |
| `blender_addon/b_cad/` | Native Blender panels/operators, preferences, persisted CAD state, display adapter |
| `workbench/` | Buildless local UI using actual controller/worker results |
| `tests/` | Reproducible behavior/failure tests |
| `tools/` | Documentation checks/build and add-on packaging |
| `docs/decisions/` | Choices, scope, tradeoffs, evidence, remaining questions |
| `ROADMAP.md` | Acceptance targets; partial experiments do not complete broader gates |
| `.github/` | Contribution forms, automation, review ownership |

## Verification and known limits

The first implementation was also exercised in Edge against the actual local service: edit `width` and `depth = width / 2`, preview without committing, apply, undo, redo, reject an oversized hole while retaining the last valid geometry, save a `.bcad` download, open the example project, export STEP and import that file as a base solid, search the command palette, and switch standard views/projection. The README screenshot is the running workbench, not a concept rendering. Narrow/mobile behavior and interactive Blender undo still need dedicated manual evidence.

Report exact commands/results for the commit under review. The recorded experiment uses Windows x64, CPython 3.13.5, and Blender 5.1.0; the smoke-check section above states its actual scope. The [dependency record](dependencies.md) documents native geometry checks and package versions. macOS/Linux, clean-machine installs, and interactive Blender undo/redo need separate evidence. The source setup implies no production certification.

Three primitive definitions and non-parametric solid STEP input do not establish a solver, general feature DAG, persistent topology selection, arbitrary native project/history migration, assemblies, advanced surfacing, selected-entity angle/distance tools, or slicing. Schema, protocol, packaging, and performance remain experimental.

Body metrics come from exact geometry; preview/STL triangles are approximations. STEP tests cover declared geometry/units, not universal metadata/assembly fidelity. STL coordinates use millimeters; receiving software needs the intended units. Embedded STEP source survives in the project, while original feature history remains unavailable. Document/STEP sizes and bounded undo history are explicit limits.

Changes to units, assets, schema, references, solver, process boundaries, dependencies, or packaging need a focused design record/RFC and actual regression fixtures. Explain failure/recovery. Update the [vision](vision.md), [UI requirements](ui-design.md), and roadmap when behavior changes.

Complete the [pull request template](../.github/pull_request_template.md), disclose AI assistance under the [AI policy](ai-contributions.md), and report unrun checks honestly. The [contributor guide](../CONTRIBUTING.md) covers licensing/review.
