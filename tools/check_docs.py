#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check local Markdown/HTML links, anchors and site search coverage."""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from build_site import ROOT, render, sources


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if "id" in attr:
            self.ids.add(attr["id"])
        for key in ("href", "src"):
            if attr.get(key):
                self.links.append(attr[key])


def check(paths, root):
    documents, failures = {}, []
    for path in paths:
        parser = Links()
        raw = path.read_text(encoding="utf-8")
        parser.feed(render(raw)[0] if path.suffix == ".md" else raw)
        documents[path.resolve()] = parser
    for path, parsed in documents.items():
        for link in parsed.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            name = unquote(url.path)
            if name.startswith("/B-CAD/"):
                target = root / name[len("/B-CAD/"):]
            elif name.startswith("/"):
                failures.append(f"{path.relative_to(root)}: unexpected root URL {link}")
                continue
            else:
                target = path.parent / name if name else path
            if target.is_dir():
                target /= "index.html"
            target = target.resolve()
            if not target.exists():
                failures.append(f"{path.relative_to(root)}: missing {link}")
            elif url.fragment and target in documents and unquote(url.fragment) not in documents[target].ids:
                failures.append(f"{path.relative_to(root)}: missing anchor {link}")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path)
    options = parser.parse_args()
    paths = sources() + sorted((ROOT / ".github").rglob("*.md"))
    failures = check(paths, ROOT)
    if options.site:
        output = options.site.resolve()
        html_paths = sorted(output.rglob("*.html"))
        failures.extend(check(html_paths, output))
        index = json.loads((output / "search-index.json").read_text(encoding="utf-8"))
        for entry in index:
            url = urlsplit(entry["url"])
            target = output / unquote(url.path)
            if not target.is_file():
                failures.append(f"Search points to missing {entry['url']}")
            elif url.fragment:
                parsed = Links()
                parsed.feed(target.read_text(encoding="utf-8"))
                if unquote(url.fragment) not in parsed.ids:
                    failures.append(f"Search points to missing anchor {entry['url']}")
        print(f"Checked {len(html_paths)} built HTML pages and {len(index)} search entries.")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Checked {len(paths)} Markdown documents. All local links and anchors resolve.")


if __name__ == "__main__":
    main()
