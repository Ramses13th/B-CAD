# Maintaining the public hub

The repository's Markdown is the source of truth for documentation. The `site/` directory contains the landing page, shared styling, browser-local search behavior, and original vector illustrations. [The development guide](development.md) covers local builds.

## Publishing with GitHub Pages

The [Publish documentation workflow](../.github/workflows/pages.yml) builds and checks the site on pushes to `main` and manual dispatch. Repository **Settings → Pages → Build and deployment → Source** must be **GitHub Actions**. The deployment publishes the generated site artifact, not the source checkout.

The documentation workflow also checks pull requests. Pull requests have read-only repository permissions and do not deploy. The Pages deployment job uses the `github-pages` environment and the `pages: write` and `id-token: write` permissions required by GitHub's deployment action.

The configured project URL is [ramses13th.github.io/B-CAD](https://ramses13th.github.io/B-CAD/). If ownership, repository name, or domain changes, update `BASE_URL` in `tools/build_site.py`, canonical and social metadata in `site/index.html`, and repository metadata links. Rebuild and check both source and output links.

## Discovery and accessibility

Keep a concise About description with Blender, parametric CAD, and contribution intent. Use relevant GitHub topics rather than unrelated trending keywords. Set the website field to the Pages URL. The build emits a sitemap and robots file, canonical URLs, a search index with section anchors, and a 404 page.

Search uses only the static index in the visitor's browser. It does not send queries to a search provider. Preserve semantic headings, visible focus, keyboard access, readable contrast, responsive layouts, and reduced-motion support when changing the site.

The social preview is `site/assets/social-card.png`, generated from the original SVG. Do not present concept art as a screenshot of working software. Update project status in the README, landing page, installation guide, and roadmap together when implementation changes.

## Verification scope

Local-link checks catch missing documentation, assets, and anchors. Generated-site checks verify the built navigation and search targets. They do not guarantee that external websites remain available or that search engines index the project. Inspect the landing page and a long documentation page on desktop and mobile after visual changes.

GitHub's [custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) describes the deployment contract.
