# Run the experimental B-CAD prototype

B-CAD now has a **source-built experimental prototype**: a modern local workbench and a Blender adapter backed by exact OCCT geometry. It can create a parameterized box, cylinder, or plate with a centered through-hole. This is an early development build, with no stable release or Fusion feature-parity claim. A constrained-sketch solver, general editable feature history, persistent face/edge references, assemblies, and integrated slicing remain [roadmap](../ROADMAP.md) work.

The setup uses a separate Python environment for the CAD worker. **Do not install CadQuery or OCP into Blender's Python.** The Blender adapter launches the configured external interpreter and receives a display mesh. See the [first prototype decision](decisions/0002-first-prototype.md) and [development guide](development.md).

## What is available

| Interface | Current scope |
| --- | --- |
| Local browser workbench | Primitive parameters and previews, exact body metrics, undo/redo, `.bcad` save/open, STEP import, STEP/STL export |
| Blender adapter | Primitive creation/recompute, CAD parameter controls, generated display mesh, `.bcad` project import/export |
| STEP in Blender | Use the local workbench for STEP import/export; the first Blender panel has no STEP exchange buttons |
| Imported STEP | Non-parametric base geometry with its source embedded in the `.bcad` document; no original sketch/history editing |
| Precision | Length expressions and B-Rep body metrics; selected edge/face distances, angular measurement, snapping, and sketch constraints are future work |
| Distribution | Build from this repository; no production package or marketplace listing is claimed |

The initial Blender experiment targets **Blender 5.1**. The worker setup uses **CPython 3.13**, **CadQuery 2.8.0**, and **cadquery-ocp 7.9.3.1.1**. Each advertised OS/CPU/Blender combination needs its own checks. See the [dependency and native-check record](dependencies.md) and [verification limits](development.md#verification-and-known-limits).

## 1. Get the source and external worker

On Windows, install Git and ordinary CPython 3.13, then open PowerShell where you keep source projects:

```powershell
git clone https://github.com/Ramses13th/B-CAD.git
cd B-CAD
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-core.txt
```

`requirements-core.txt` pins the CadQuery/OCP pair. Keep the environment and repository available while using the Blender adapter. If `python` points to a different interpreter, select your installed CPython 3.13 executable when creating the environment.

The equivalent environment layout on macOS/Linux is `.venv/bin/python`:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-core.txt
```

These commands describe the source workflow, not a verified cross-platform support matrix. Native wheel availability and the exact Blender build still need checks on the target machine.

## 2. Open the local workbench

From the repository root on Windows:

```powershell
.\.venv\Scripts\python.exe -m bcad.server
```

On macOS/Linux:

```sh
.venv/bin/python -m bcad.server
```

The server opens the workbench at `http://127.0.0.1:8765` by default and prints the actual URL. Keep that terminal running; stop it with `Ctrl+C` when finished. Use `--no-browser` to suppress automatic opening or `--port 8766` if the default port is occupied. The application listens locally. GitHub Pages hosts the contributor hub, not this geometry service or your open CAD document.

Choose **Drilled plate**, edit its dimensions, use **Preview** and **Apply**, and inspect the body metrics. **Save project** downloads a `.bcad` file; **Open** loads it again. **Export → STEP (exact)** or **STL (mm mesh)** creates exchange files. **Import STEP** opens `.step`/`.stp` as exact base geometry. Its source is embedded in the saved project, so regeneration does not require the original external path. Imported geometry has no editable primitive parameters or recovered source feature history.

Each geometry request starts a one-shot worker process. Loading native libraries can take several seconds, and this implementation is synchronous. This is a development tradeoff, not a real-time performance promise.

## 3. Build and install the Blender adapter

Generate the archive from the source checkout:

```powershell
python tools/package_addon.py --output work/bcad-addon.zip
```

The generated `work/bcad-addon.zip` is the adapter package. GitHub's **Code → Download ZIP** is a source archive, not the installer. The adapter archive does not bundle the external native CAD environment.

In Blender 5.1:

1. Open **Edit → Preferences → Add-ons**, use **Install from Disk** in its menu to select `bcad-addon.zip`, and enable B-CAD. Blender documents [add-on installation](https://docs.blender.org/manual/en/5.1/editors/preferences/addons.html) and [extensions from disk](https://docs.blender.org/manual/en/5.1/editors/preferences/extensions.html).
2. In B-CAD's preferences, set **External Python** to the absolute path of the environment above, for example `C:\path\to\B-CAD\.venv\Scripts\python.exe`. On macOS/Linux it ends in `.venv/bin/python`.
3. Open the **3D Viewport**, press **N** for the sidebar, and select **B-CAD**.
4. Choose a box, **Drilled plate**, or cylinder, set dimensions, and press **Build / Recompute**. **New Part** creates a separate object/document. The mesh is a generated display of the exact part.
5. Use **Open** / **Save** to load or save `.bcad` documents. Use the local workbench for STEP exchange in this first slice.

Use a new file for the first workflow. Editing the generated mesh with Blender mesh tools does not change the canonical CAD dimensions; recomputing regenerates the display. Change mechanical dimensions through B-CAD parameters.

Parts use millimeter dimensions and may look tiny beside Blender's default cube. Select the generated object and press **Numpad .** to frame it, or use **View → Frame Selected**.

## Length expressions

The first implementation accepts `mm`, `cm`, `m`, `in`, `inch`, `ft`, and `um`, plus numbers, existing parameter names, `pi`, parentheses, and `+ - * /`.

| Input | Meaning |
| --- | --- |
| `80 mm` | Explicit metric length |
| `2 in` | Converted to 50.8 mm |
| `width / 2` | Half the existing width parameter |
| `width + 2 mm` | Add an explicit length |
| `8` | A final bare number is interpreted as millimeters |

Inside an expression a bare number is a scalar, so use `width + 2 mm`, rather than `width + 2`. Parameters must resolve to positive lengths within the prototype's declared range. A plate's hole must fit inside width and depth. Unknown names, cycles, non-finite values, function calls, and dimensionally inconsistent expressions are rejected. General angle expressions and sketch constraints are not implemented.

## Files and limits

`.bcad` is versioned JSON for this experimental part document. It preserves source expressions and embeds imported STEP data. It is not a stable production format or a way to recover another CAD program's history. Save retained copies before trying later experimental versions.

STEP exchange covers solid base geometry. Names, colors, assembly structure, PMI, arbitrary surfaces, and source feature history are not claimed. STEP inputs are limited to 10 MiB; documents to 15 MiB. Requests and generated output also have bounds.

STL is a triangle mesh export using millimeter coordinates. STL itself has no standard unit declaration: select millimeters in the receiving slicer and check dimensions. Mesh output has no editable CAD history. 3MF and full slicer projects are planned; the [integrated printing workspace](printing-roadmap.md) is deferred P2 work.

## Troubleshooting and removal

If the worker cannot start, check **External Python** points to the correct environment and install `requirements-core.txt` with that interpreter. Run the workbench from the checkout to see startup output. A Python executable without CadQuery/OCP is insufficient.

If an expression or operation fails, correct the reported field and recompute; a rejected edit retains the committed document. Startup latency can resemble a pause because the worker launches per operation. Crash recovery and production-scale performance remain roadmap work.

Remove the adapter through Blender Preferences. Stop the local server separately. The checkout, external environment, and saved projects are separate files; keep projects you want to retain.

Report a reproducible issue with the B-CAD commit, Blender/Python versions, OS/CPU, steps, expected result, and redacted logs through [GitHub Issues](https://github.com/Ramses13th/B-CAD/issues/new/choose). Include a small original fixture when possible.
