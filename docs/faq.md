# Frequently asked questions

## Can I install B-CAD now?

No. The repository currently contains a blueprint, roadmap, contributor materials, and the documentation website. There is no add-on ZIP, CAD core, release, or working modeling UI. See [installation and availability](installation.md).

## Is this a Fusion replacement?

That is an ambition for a future mechanical design workflow, not today's product capability. B-CAD is independent and has no affiliation with Autodesk. The [roadmap](../ROADMAP.md) scopes a technical prototype and useful MVP before broader features.

## Why use Blender?

The proposed design uses Blender for interaction, visualization, and integration with its broader creative workflow. Exact geometry and parametric state would live in a dedicated CAD model and core. See [architecture](architecture.md).

## Why not just add dimensions to a mesh?

The project aims to preserve design intent, exact geometry, and stable feature references. A viewport mesh is a derived approximation in this design. Mesh edits must never silently claim to retain an exact parametric CAD model.

## Which Blender versions and operating systems work?

None have been validated for a B-CAD implementation yet. The blueprint suggests an LTS baseline, but the exact version and supported Windows, Linux, and macOS matrix must be selected and tested before a release. The docs website itself runs in a modern browser.

## Do I need to build native libraries to contribute?

No. Documentation, design cases, UI proposals, test plans, and infrastructure work are useful now. Native build instructions will arrive with the CAD core. The current [documentation build](development.md) needs Python and a Markdown dependency.

## Can an AI or AI-assisted user contribute?

Yes. Follow [the AI policy](ai-contributions.md). For AI-generated code or architecture, use the maintainer's GPT-6.1 Sol / Astra / Claude Opus 5.5-equivalent or higher quality bar and disclose the tool/model. A named model does not replace review or validation. Human-only contributions are welcome too.

## Are CAD Sketcher or Seamless CAD being copied?

This initial hub contains no third-party CAD implementation. Those projects are research references and possible interoperability collaborators. Any future reuse needs attribution and a license review of the exact code. Migration tools are future work, not existing importers.

## Will STEP, STL, 3MF, assemblies, or drawings be supported?

These appear in the [roadmap](../ROADMAP.md), with different scope and priority. No such feature is implemented here yet. Exact STEP geometry and mesh export are distinct; neither automatically preserves feature history.

## When will a release be ready?

There is no committed date. Releases will be based on demonstrated acceptance criteria and available contributors. We do not present blueprint effort estimates as a delivery promise.

## How do I help people find the project?

Link to the [public hub](https://ramses13th.github.io/B-CAD/) or [repository](https://github.com/Ramses13th/B-CAD), include a clear description, and share a specific contribution need with relevant communities under their posting rules. Accurate expectations and useful issues make sharing more effective. The project does not automate unsolicited outreach.
