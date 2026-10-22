# Frequently asked questions

## Can I install B-CAD now?

You can run the experimental local workbench and build a Blender add-on ZIP from source. The first slice handles exact boxes, drilled plates and cylinders; no production release is available. See [installation](installation.md).

## Is this a Fusion replacement?

That is an ambition for a future mechanical design workflow, not today's product capability. B-CAD is independent and has no affiliation with Autodesk. The [roadmap](../ROADMAP.md) scopes a technical prototype and useful MVP before broader features.

## Why use Blender?

The proposed design uses Blender for interaction, visualization, and integration with its broader creative workflow. Exact geometry and parametric state would live in a dedicated CAD model and core. See [architecture](architecture.md).

## Why not just add dimensions to a mesh?

The project aims to preserve design intent, exact geometry, and stable feature references. A viewport mesh is a derived approximation in this design. Mesh edits must never silently claim to retain an exact parametric CAD model.

## Which Blender versions and operating systems work?

The first slice has local runtime evidence on Windows, Python 3.13 and Blender 5.1.0. This is a tested development configuration, not a cross-platform support promise. See [development](development.md) for exact checks and remaining evidence gaps.

## Do I need to build native libraries to contribute?

No. Documentation, design cases and UI work remain useful. The prototype uses pinned prebuilt CAD wheels in a separate Python environment; it does not require compiling OCCT on the tested Windows configuration. See [development](development.md) and [dependencies](dependencies.md).

## Can an AI or AI-assisted user contribute?

Yes. Follow [the AI policy](ai-contributions.md). For AI-generated code or architecture, use the maintainer's GPT-6.1 Sol / Astra / Claude Opus 5.5-equivalent or higher quality bar and disclose the tool/model. A named model does not replace review or validation. Human-only contributions are welcome too.

## Are CAD Sketcher or Seamless CAD being copied?

This initial hub contains no third-party CAD implementation. Those projects are research references and possible interoperability collaborators. Any future reuse needs attribution and a license review of the exact code. Migration tools are future work, not existing importers.

## Will STEP, STL, 3MF, assemblies, or drawings be supported?

The prototype imports and exports STEP base bodies and exports STL meshes. It does not import arbitrary CAD project histories. 3MF, assemblies and drawings remain planned at different priorities. Exact STEP geometry and mesh export are distinct; neither automatically preserves feature history. See the [format matrix](vision.md) and [roadmap](../ROADMAP.md).

## When will a release be ready?

There is no committed date. Releases will be based on demonstrated acceptance criteria and available contributors. We do not present blueprint effort estimates as a delivery promise.

## How do I help people find the project?

Link to the [public hub](https://ramses13th.github.io/B-CAD/) or [repository](https://github.com/Ramses13th/B-CAD), include a clear description, and share a specific contribution need with relevant communities under their posting rules. Accurate expectations and useful issues make sharing more effective. The project does not automate unsolicited outreach.
