# Experimental CAD dependencies

B-CAD's first implementation evaluates exact solids in a separate Python process using CadQuery and its OCP bindings to Open CASCADE Technology (OCCT). Blender and the browser receive replaceable triangle meshes for display. CAD measurements and STEP exchange use the exact B-Rep.

## Tested environment and pins

The initial native geometry checks ran on **Windows x64, CPython 3.13.5**, on 2026-10-22. [requirements-core.txt](../requirements-core.txt) pins the complete resolved Python package set from that experiment, including transitive dependencies. The packages were installed from official PyPI wheels into an isolated `.venv`; third-party binaries are not committed to the repository. Linux, macOS, different Python versions, clean-user deployment, and redistributable native packages remain unverified.

| Component | Tested version | Role | Upstream license information |
| --- | --- | --- | --- |
| CadQuery | 2.8.0 | Modeling, exact queries, tessellation, STEP/STL exchange | [Apache-2.0](https://github.com/CadQuery/cadquery/blob/master/LICENSE) |
| cadquery-ocp | 7.9.3.1.1 | Native OCCT bindings | [Apache-2.0](https://github.com/CadQuery/OCP/blob/master/LICENSE) for the bindings; underlying OCCT has separate terms |
| cadquery-ocp-proxy | 7.9.3.1.1 | OCP module proxy | Apache-2.0 in installed package metadata |
| OCCT | 7.9.3 build family | Exact geometry kernel | [LGPL-2.1](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_9_3/LICENSE_LGPL_21.txt) with [Open CASCADE exception](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_9_3/OCCT_LGPL_EXCEPTION.txt) |
| VTK | 9.6.2 | Dependency of the OCP wheel | BSD in installed package metadata |

The worker reports CadQuery's runtime version, the installed OCP distribution version, and `OCP.__version__`. Its OCCT version field is the first three components of the OCP runtime build version and includes `version_source` to make that provenance explicit; it is not an independent binary ABI certification.

CadQuery 2.8 declares `cadquery-ocp>=7.9.3.1,<8.0`. Installing the latest OCP independently would violate that bound. Its package also declares numerical, visualization, and web dependencies that are not B-CAD's own solver/UI selections. CasADi's presence in the environment does not mean B-CAD has implemented a sketch solver. VTK/trame's presence does not mean the B-CAD interface uses their servers.

The [CadQuery package metadata](https://pypi.org/pypi/cadquery/2.8.0/json) and [OCP package metadata](https://pypi.org/pypi/cadquery-ocp/7.9.3.1.1/json) identify the actual requirements. The resolved environment also contains NumPy 2.5.4, SciPy 1.18.1, Numba 0.68.0, CasADi 3.8.1, NLopt 2.11.0, ezdxf 1.4.5, multimethod 1.12, and the trame 4.0.0 family; every version is pinned in the requirements file. Some native wheels bundle additional libraries. A source/license/notice inventory for redistributing those binaries is still a release prerequisite; this experiment does not satisfy the entire roadmap distribution gate.

## Reproduce the native checks

From the repository root on the tested Windows/Python combination:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-core.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_kernel.py -v
```

The kernel tests verify analytic volume, surface area, bounds, center of mass, and solid validity; changed tessellation with unchanged exact properties; native STEP export/reimport and imported-source reexport; declared centimeter-to-millimeter conversion and multiple solid preservation; binary STL coordinates; invalid inputs; and actual persistent/one-shot subprocess JSON behavior. The STEP round trip uses the same OCCT implementation on both ends. Cross-application exchange validation remains future work. STL coordinates use millimeters by convention; STL itself does not carry a unit declaration.

## Worker boundary and scope

`python -m bcad.kernel_worker` reads one JSON object per line and writes one JSON reply per line. `--once` exits after its first request. The process redirects native OCCT diagnostics away from protocol stdout. Protocol version, request ID, and revision travel with the result. It accepts evaluated numeric dimensions in millimeters; the document layer owns expressions and unit conversion.

Implemented geometry consists of a rectangular box, a cylinder, and a rectangular plate with a centered cylindrical through-hole. All begin at Z=0 and are centered on X/Y. STEP import accepts exact solid bodies as an imported base with no recovered feature history, converting declared STEP units to millimeters. It preserves all transferred roots and rejects loose surfaces, wires, and points rather than silently discarding them. Names, colors, assembly hierarchy, parametric history, and proprietary CAD-project translation are not part of this first exchange contract.

The worker accepts no client filesystem paths. STEP bytes travel as bounded base64 and are read from an internally managed temporary directory. Current experiment limits are 10 MiB for imported/exported files, 14 MiB per request, 2,000 imported faces, 200,000 preview triangles, and dimensions from 0.01 to 100,000 mm. Linear display/export tolerance ranges from 0.01 to 5 mm; angular tolerance ranges from 0.02 to 1 radian. A plate hole must leave at least 0.005 mm of material on each side. Native import/tessellation work still needs host-side deadlines and process termination: byte limits do not bound geometry computation time or native memory use.

An independent process keeps the CAD kernel away from Blender's embedded Python ABI. Blender's official [threading guidance](https://docs.blender.org/api/5.0/info_gotchas_threading.html) explains why long-lived Python threads are unsuitable inside its interpreter. Host adapters must apply results through Blender's main-thread API and verify document revisions before replacing a display cache.

## Initial timing observation

On an Intel Core i5-1135G7 at 2.40 GHz, Windows x64, CPython 3.13.5, one persistent worker evaluated the 80 × 50 × 8 mm plate with a Ø12 mm hole six times at linear tolerance 0.2 mm and angular tolerance 0.2 radians. The first request, including process startup/imports, took 2.151 seconds. The following five took 0.0263, 0.0255, 0.0254, 0.0253, and 0.0267 seconds (median 0.0255 seconds), producing 268 preview triangles. These are one local observation, without warm-up normalization or a performance guarantee. The one-shot client intentionally pays startup cost for each request; persistent client lifecycle, cancellation, and recovery are later work.

## Primary implementation references

- [CadQuery installation](https://cadquery.readthedocs.io/en/latest/installation.html): isolated environments and Windows pip support.
- [CadQuery import/export](https://cadquery.readthedocs.io/en/latest/importexport.html): STEP units, supported exchange formats, and loss of original parametric history.
- [CadQuery geometry API](https://cadquery.readthedocs.io/en/latest/classreference.html): shape validity, mass properties, bounds, and topology.
- [CadQuery tessellation source](https://cadquery.readthedocs.io/en/latest/_modules/cadquery/occ_impl/shapes.html): generated mesh behavior; B-CAD explicitly requests absolute linear deflection in the native mesher.
- [Blender LTS releases](https://www.blender.org/download/lts/): release-policy reference. The installed Blender 5.1.0 is an experiment target, not a claim that the current LTS builds have passed B-CAD checks.
