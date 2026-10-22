# Development setup

The current development workflow is for **documentation and the contributor website**. B-CAD has no add-on source, native CAD-core implementation, geometry test suite, or runtime build system yet. Blender, OCCT, and solver dependencies are not needed to edit this hub.

## Get the repository

You need Git and Python 3.11 or newer. Fork the repository on GitHub if you plan to submit a pull request, then clone your fork. To inspect the upstream repository directly:

```sh
git clone https://github.com/Ramses13th/B-CAD.git
cd B-CAD
```

Create a branch before editing:

```sh
git switch -c docs/your-change
```

On systems where the Python executable is named `python3`, substitute `python3` in the commands below. A virtual environment is recommended for the pinned Markdown dependency:

```sh
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or in a macOS / Linux shell:

```sh
source .venv/bin/activate
```

Install the documentation dependency:

```sh
python -m pip install -r requirements.txt
```

This sets up the documentation tools, not a B-CAD add-on. Blender and native CAD dependencies are not required.

## Check and build

Run from the repository root:

```sh
python tools/check_docs.py
python tools/build_site.py --output work/site
python tools/check_docs.py --site work/site
```

The first command validates the repository's documentation constraints. The second builds the static contributor website into `work/site`. These commands validate the hub; they do not establish CAD correctness, Blender compatibility, or working installation support.

For visual review, serve the generated files:

```sh
python -m http.server 8000 --directory work/site
```

Open `http://localhost:8000` in a browser. Stop the server with `Ctrl+C`. Review your change at a narrow mobile width and a desktop width, follow relevant links, use the search, and check keyboard navigation for interactive changes. Keep generated output in `work/`; change the source files rather than editing the generated site.

## Where to contribute

| File or directory | Purpose |
| --- | --- |
| `README.md` | Project introduction, honest status, and starting points. |
| `ROADMAP.md` | Proposed milestones, dependencies, and acceptance gates. |
| `docs/` | Architecture, installation status, development, and AI policies. |
| `CONTRIBUTING.md` | Human contribution workflow. |
| `AGENTS.md` | Repository instructions for AI contributors. |
| `.github/` | Issue forms, pull request template, workflows, and ownership. |
| `tools/` | Documentation validation and static-site build tools. |

Read the current files before assuming a layout for future code. Module boundaries and implementation language choices in the [architecture](architecture.md) remain proposals until their corresponding decisions and experiments are reviewed.

## Documenting technical changes

State what is implemented, what is proposed, and what remains uncertain. Cite current primary documentation for API, licensing, or platform claims. For the supplied research blueprint, retain useful design reasoning while independently checking factual and time-sensitive assertions.

Use short, descriptive page titles and descriptive link text. Define technical terms before relying on them. Keep the README approachable and place detailed design tradeoffs in `docs/`. Use diagrams as explanations of the proposed system, not as evidence that it runs.

## Future implementation work

A first code proposal should define its source layout, supported toolchain, dependency licenses, test command, representative input, and acceptance criteria. A minimal experiment is useful when it answers a specific architectural question; a large directory tree of unimplemented placeholders is not a working milestone.

Changes to the kernel boundary, document format, units, persistent references, solvers, or packaging need a [Design RFC](https://github.com/Ramses13th/B-CAD/issues/new?template=design_rfc.yml) before substantial implementation. Include expected failure behavior and recovery, not only the successful path. Later CAD checks should exercise actual geometry and document behavior with reproducible fixtures.

Complete the [pull request template](../.github/pull_request_template.md), disclose AI assistance under the [AI policy](ai-contributions.md), and report the checks you actually ran. The [contributor guide](../CONTRIBUTING.md) explains review and licensing.
