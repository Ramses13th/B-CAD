#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the public B-CAD hub from tracked Markdown and site assets."""
from __future__ import annotations

import argparse
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
from urllib.parse import quote, urlsplit, urlunsplit

import markdown

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://ramses13th.github.io/B-CAD/"
REPO_URL = "https://github.com/Ramses13th/B-CAD"
ROOT_DOCS = ["README.md", "ROADMAP.md", "CONTRIBUTING.md", "AGENTS.md",
             "CODE_OF_CONDUCT.md", "SECURITY.md"]


def sources():
    return [ROOT / name for name in ROOT_DOCS] + sorted((ROOT / "docs").rglob("*.md"))


class TextContent(HTMLParser):
    def __init__(self):
        super().__init__()
        self.words = []

    def handle_data(self, data):
        self.words.append(data)


def plain(value):
    parser = TextContent()
    parser.feed(value)
    return re.sub(r"\s+", " ", " ".join(parser.words)).strip()


def render(source):
    parser = markdown.Markdown(extensions=["extra", "toc", "sane_lists"])
    body = parser.convert(source)
    return body, parser.toc_tokens


def relative_root(path):
    depth = len(path.parts) - 1
    return "../" * depth or "./"


def rewrite_links(body, source):
    def replace(match):
        attr, raw = match.group(1), html.unescape(match.group(2))
        parts = urlsplit(raw)
        if parts.scheme or parts.netloc or not parts.path:
            return match.group(0)
        target = (source.parent / parts.path).resolve()
        repo_path = target.relative_to(ROOT)
        if repo_path.parts[0] == ".github" or target.suffix == ".py" or target.name in ("requirements.txt", "LICENSE", "NOTICE"):
            url = f"{REPO_URL}/blob/main/{repo_path.as_posix()}"
            if parts.fragment:
                url += "#" + parts.fragment
            return f'{attr}="{html.escape(url, quote=True)}"'
        if parts.path.endswith(".md"):
            target = target.with_suffix(".html")
        elif repo_path.parts[0] == "site":
            target = ROOT.joinpath(*repo_path.parts[1:])
        rel = os.path.relpath(target, source.parent).replace(os.sep, "/")
        value = urlunsplit(("", "", rel, parts.query, parts.fragment))
        return f'{attr}="{html.escape(value, quote=True)}"'
    return re.sub(r'(href|src)="([^"]+)"', replace, body)


def shell(title, description, body, path, toc=""):
    base = relative_root(path)
    canonical = BASE_URL + quote(path.as_posix())
    nav = [("docs/index.html", "Documentation"), ("docs/installation.html", "Installation & status"),
           ("ROADMAP.html", "Roadmap"), ("docs/architecture.html", "Architecture"),
           ("CONTRIBUTING.html", "Contribute"), ("docs/ai-contributions.html", "AI contributions"),
           ("docs/development.html", "Development"), ("docs/faq.html", "FAQ"),
           ("docs/governance.html", "Governance"), ("docs/research.html", "Research"),
           ("docs/glossary.html", "Glossary")]
    links = "".join(f'<a href="{base}{url}"' + (' aria-current="page"' if path.as_posix() == url else '') + f'>{label}</a>' for url, label in nav)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} | B-CAD</title><meta name="description" content="{html.escape(description, quote=True)}">
<link rel="canonical" href="{canonical}"><meta name="theme-color" content="#141719">
<meta property="og:title" content="{html.escape(title, quote=True)} | B-CAD"><meta property="og:description" content="{html.escape(description, quote=True)}"><meta property="og:type" content="website"><meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE_URL}assets/social-card.png"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/svg+xml" href="{base}assets/favicon.svg"><link rel="stylesheet" href="{base}style.css"><script defer src="{base}app.js"></script></head>
<body class="document-page" data-base="{base}"><a class="skip-link" href="#main-content">Skip to content</a>
<header class="site-header"><a class="brand" href="{base}index.html" aria-label="B-CAD home"><svg viewBox="0 0 32 32" width="30" height="30" aria-hidden="true"><path d="M4 8 16 1l12 7v15l-12 8L4 23V8Zm4 2v11l8 5 8-5V10l-8-5-8 5Z" fill="currentColor"/><path d="m8 10 8 5 8-5M16 15v11" fill="none" stroke="currentColor" stroke-width="2"/></svg><span>B-CAD<span class="brand-dot">.</span></span></a><button class="nav-toggle" type="button" data-nav-toggle aria-controls="main-navigation" aria-expanded="false">Menu +</button><nav class="main-navigation" id="main-navigation" data-navigation aria-label="Main navigation"><a href="{base}docs/index.html">Docs</a><a href="{base}ROADMAP.html">Roadmap</a><a href="{base}search.html">Search</a><a class="nav-github" href="{REPO_URL}">GitHub ↗</a></nav></header>
<main id="main-content" class="document-shell"><nav class="document-nav" aria-label="Documentation">{links}</nav>
<article class="document-content prose"><p class="eyebrow">PROJECT BLUEPRINT / NO ADD-ON RELEASE YET</p>{body}{toc}<p class="edit-link"><a href="{REPO_URL}/blob/main/{path.with_suffix('.md').as_posix()}">View Markdown source on GitHub ↗</a></p></article></main>
<footer class="site-footer"><a href="{base}index.html">B-CAD</a><p>Open parametric CAD for Blender. Built in the open, one verified step at a time.</p><a href="{base}CONTRIBUTING.html">Help build it ↗</a></footer></body></html>'''


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--output", default="work/site")
    options = args.parse_args()
    output = Path(options.output).resolve()
    # Rebuild only inside an explicitly designated output directory; never delete it.
    if output == ROOT or ROOT in output.parents and output.parts[len(ROOT.parts)] not in ("work", "_site"):
        raise SystemExit("Use work/site, _site, or a directory outside the checkout as output.")
    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "site", output, dirs_exist_ok=True)
    search = []
    for source in sources():
        rel = source.relative_to(ROOT).with_suffix(".html")
        raw = source.read_text(encoding="utf-8")
        body, _ = render(raw)
        title_match = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
        title = plain(title_match.group(1)) if title_match else source.stem
        description = plain(body)[:180]
        dest = output / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(shell(title, description, rewrite_links(body, source), rel), encoding="utf-8")
        search.append({"title": title, "url": rel.as_posix(), "description": description, "content": plain(body)})
        for section in re.split(r'(?=<h[23] id=")', body)[1:]:
            heading = re.match(r'<h[23] id="([^"]+)">(.*?)</h[23]>', section, re.S)
            if heading:
                search.append({"title": f"{title} / {plain(heading[2])}", "url": f"{rel.as_posix()}#{heading[1]}", "description": plain(section)[:190], "content": plain(section)})
    search_body = '''<h1>Search the blueprint</h1><p>Search the roadmap, installation status, architecture, and contributor guides. All search runs in your browser.</p>
<form data-search-form role="search"><label for="site-search">Search documentation</label><div class="search-controls"><input id="site-search" name="q" type="search" data-search-input placeholder="Try: topology, first issue, installation" autocomplete="off"><button type="submit" class="button button-primary">Search</button></div></form><p data-search-status role="status" aria-live="polite"></p><div data-search-results></div><noscript><p>Search needs JavaScript. Browse the <a href="docs/index.html">documentation index</a> instead.</p></noscript>'''
    search_html = shell("Search", "Search B-CAD's open CAD roadmap and contributor documentation.", search_body, Path("search.html"))
    search_html = re.sub(r'<p class="edit-link">.*?</p>', '', search_html)
    (output / "search.html").write_text(search_html, encoding="utf-8")
    (output / "search-index.json").write_text(json.dumps(search, ensure_ascii=False), encoding="utf-8")
    (output / ".nojekyll").write_text("", encoding="utf-8")
    (output / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n", encoding="utf-8")
    urls = [BASE_URL] + [BASE_URL + p.relative_to(output).as_posix() for p in sorted(output.rglob("*.html")) if p.name not in ("index.html", "404.html") or p.parent != output]
    (output / "sitemap.xml").write_text('<?xml version="1.0" encoding="utf-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{html.escape(u)}</loc></url>' for u in urls) + '</urlset>', encoding="utf-8")
    not_found = shell("Page not found", "Return to the B-CAD documentation.", '<h1>That page is not here.</h1><p><a href="/B-CAD/">Return home</a> or <a href="/B-CAD/search.html">search the docs</a>.</p>', Path("404.html"))
    # A 404 is served at arbitrary URLs, so its assets and links need absolute project paths.
    not_found = not_found.replace('href="./', 'href="/B-CAD/').replace('src="./', 'src="/B-CAD/')
    not_found = re.sub(r'<p class="edit-link">.*?</p>', '', not_found)
    (output / "404.html").write_text(not_found, encoding="utf-8")
    print(f"Built {len(sources())} documentation pages and {len(search)} search entries into {output}")


if __name__ == "__main__":
    main()
