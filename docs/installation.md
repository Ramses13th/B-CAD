# Installing B-CAD

**Installation is not available yet.** B-CAD currently publishes a blueprint and contributor hub. This repository does not contain a working Blender add-on, an extension package, a native CAD-core executable, or a supported release. There is nothing to enable in Blender today.

GitHub's **Code → Download ZIP** downloads the repository source. It is **not** a B-CAD extension installer. Cloning this repository will not add CAD tools to Blender.

## What you can do now

- Read the [architecture](architecture.md) and [roadmap](../ROADMAP.md).
- Help with a concrete task through the [contributor guide](../CONTRIBUTING.md).
- Run the documentation checks and preview the contributor website using the [development guide](development.md).
- Watch the [repository](https://github.com/Ramses13th/B-CAD) for releases and follow implementation issues.

## Compatibility status

| Component | Current status |
| --- | --- |
| Blender | No version tested or supported by B-CAD yet. The blueprint proposes Blender 5.2 LTS as the initial target. |
| Windows / macOS / Linux | Intended platforms; no B-CAD runtime builds or compatibility results exist yet. |
| Native CAD core / OCCT | Proposed architecture; no distributed service or dependency installer exists. |
| Sketch solver | Evaluation planned; no solver is bundled. |
| Existing `.blend`, STEP, or mesh files | No B-CAD import, migration, export, or file compatibility support exists yet. |

A planning target is not a compatibility promise. The first release must publish its exact Blender versions, operating systems, CPU architectures, native dependencies, and known limitations.

## Planned installation flow for a future release

The following is a **conditional guide**, ready to be replaced by tested instructions when a release exists. Package names, binary distribution, and platform support remain undecided.

1. Open the repository's [Releases page](https://github.com/Ramses13th/B-CAD/releases). Continue only when a release explicitly includes an installable B-CAD extension and states your supported Blender version and platform.
2. Read the release notes, known limitations, and dependency instructions. Download the **release extension asset**, rather than GitHub's automatically generated source archive. Verify published checksums if the release provides them.
3. Open the supported Blender version. In **Preferences → Get Extensions**, open the menu at the top right and select **Install from Disk**. Choose the extension `.zip` supplied by that release. Blender documents this general flow in its [official extension installation guide](https://docs.blender.org/manual/en/4.2/editors/preferences/extensions.html).
4. Follow the release-specific instructions to enable the add-on and, if required, install or locate its matching native CAD core. Do not assume the extension ZIP will include every native dependency.
5. Run the release's documented smoke test on a new, disposable file. The release must explain the expected UI, core connection status, model operation, and save/reopen result.

The exact UI may differ by Blender version; release-specific, tested steps will take precedence. A future listing on the [Blender Extensions Platform](https://extensions.blender.org/about/) would be another possible distribution route, but no B-CAD listing or approval is claimed.

## Before a first release can be called installable

Contributors must provide a valid extension manifest, reproducible packages, compatible core binaries or explicit dependency setup, license notices, platform checks, uninstall instructions, and a documented smoke test. The [roadmap](../ROADMAP.md) tracks this work. Until those gates are met, development artifacts should be labeled experimental and must not be presented as supported installers.

## Getting help

Today, report documentation or website problems through [GitHub Issues](https://github.com/Ramses13th/B-CAD/issues/new/choose). When runtime builds become available, include the exact B-CAD release, Blender version, OS, architecture, steps to reproduce, and redacted logs. Never upload private customer models or credentials.
