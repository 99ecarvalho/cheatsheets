#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Eduardo Correia
"""Build the cheat sheets into site/: src/<slug>.txt -> site/<slug>.html,
plus site/index.html (the index) and a copy of assets/.

Source format (one file per sheet):

    title: Git Keys                 <title> of the page
    prompt: $                       coloured character in front of the heading
    name: git                       the big heading
    sub: One-line description.      subtitle under the heading (HTML allowed)
    aside: ...                      lines in the box at the top right (repeatable)
    placeholder: filter: ...        hint text in the filter box
    legend: ...                     legend items next to the filter box (repeatable)
    category: Developer tools       group on the index page
    order: 10                       position inside its group
    color: green                    accent of the index card
    card: Git                       name on the index card (defaults to name)
    blurb: ...                      description on the index card
    sample: ...                     example keys on the index card (repeatable)

    ## Section title ¦ small grey note ¦ colour
    keys ¦ description
    > a note under the table

Colours: green cyan pink orange yellow purple red.
Shorthand anywhere in cells and notes: ⟨Ctrl⟩ is a key, ⟪prefix⟫ a highlighted key,
`code` is code. Everything else is HTML.

Run:  python3 build.py            (writes site/)
       python3 build.py -o DIR     (writes DIR/)
"""
import argparse
import html
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parent
YEAR = 2026
STACK_AT = 24  # sections with a longer key column put each description under its key

CATEGORIES = ["Editors", "Terminal & shell", "Developer tools", "Debugging & reverse engineering", "Networking"]

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800'
         '&family=Source+Sans+3:wght@400;600&display=swap">')

ICON_LINKEDIN = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M20.447 20.452h-3.554v-5.569'
                 'c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.948 '
                 '1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 1 1 0-4.125 2.062 '
                 '2.062 0 0 1 0 4.125zM7.119 20.452H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542'
                 'C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>')
ICON_GITHUB = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 .297c-6.63 0-12 5.373-12 12 '
               '0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61'
               '-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 '
               '1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466'
               '-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 '
               '1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 '
               '3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 '
               '2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg>')
ICON_PERSON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="7.5" r="4.5" fill="currentColor"/>'
               '<path fill="currentColor" d="M2.5 22.5c0-5.2 4.3-8.5 9.5-8.5s9.5 3.3 9.5 8.5z"/></svg>')

FOOTER = f"""<footer class="site">
  <ul class="credits">
    <li><a href="https://www.linkedin.com/in/c99-eduardo/">{ICON_LINKEDIN}<span>Eduardo Correia</span></a></li>
    <li><a href="https://www.apliant.com.br/eduardo/">{ICON_PERSON}<span>About me</span></a></li>
    <li><a href="https://github.com/99ecarvalho">{ICON_GITHUB}<span>github.com/99ecarvalho</span></a></li>
    <li><a href="https://www.apliant.com.br"><img src="img/apliant.png" alt="" width="18" height="18"><span>Sponsored by Apliant</span></a></li>
  </ul>
  <p class="copy">© {YEAR} Eduardo Correia</p>
</footer>"""


def inline(text):
    """Expand the ⟨key⟩, ⟪key⟫ and `code` shorthand."""
    key = lambda s: html.escape(s, quote=False).replace("`", "&#96;")
    text = re.sub(r"⟪(.+?)⟫", lambda m: f'<kbd class="p">{key(m.group(1))}</kbd>', text)
    text = re.sub(r"⟨(.+?)⟩", lambda m: f"<kbd>{key(m.group(1))}</kbd>", text)
    text = re.sub(r"`(.+?)`", lambda m: f"<code>{html.escape(m.group(1), quote=False)}</code>", text)
    return text


def parse(path):
    meta = {"aside": [], "legend": [], "sample": []}
    sections = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#!"):
            continue
        if line.startswith("## "):
            parts = [p.strip() for p in line[3:].split("¦")] + ["", ""]
            sections.append({"title": parts[0], "where": parts[1], "color": parts[2] or "purple", "rows": [], "notes": []})
        elif line.startswith("> ") and sections:
            sections[-1]["notes"].append(line[2:])
        elif " ¦ " in line and sections:
            k, d = line.split(" ¦ ", 1)
            sections[-1]["rows"].append((k.strip(), d.strip()))
        else:
            m = re.match(r"(\w+):\s?(.*)$", line)
            if not m:
                raise SystemExit(f"{path.name}: cannot read line: {raw}")
            key, value = m.groups()
            if key in ("aside", "legend", "sample"):
                meta[key].append(value)
            else:
                meta[key] = value
    meta["slug"] = path.stem
    meta["sections"] = sections
    return meta


def head(title):
    return (f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>{html.escape(title)}</title>\n{FONTS}\n"
            f'<link rel="icon" href="img/apliant.png">\n<link rel="stylesheet" href="style.css">\n</head>\n<body>\n')


def sheet(meta):
    out = [head(meta["title"]), '<div class="wrap">\n<nav class="top"><a class="home" href="index.html">← All cheat sheets</a></nav>\n<header>\n  <div>\n',
           f'    <h1><span class="dollar">{html.escape(meta.get("prompt", "$"))}</span> {html.escape(meta["name"])}<span class="cur">▍</span></h1>\n']
    if meta.get("sub"):
        out.append(f'    <p class="sub">{inline(meta["sub"])}</p>\n')
    out.append("  </div>\n")
    if meta["aside"]:
        out.append('  <div class="prefix-card">\n')
        out += [f'    <div class="row">{inline(a)}</div>\n' for a in meta["aside"]]
        out.append("  </div>\n")
    out.append("</header>\n\n<div class=\"tools\">\n")
    out.append(f'  <label class="search" for="q"><input id="q" type="search" placeholder="{html.escape(meta.get("placeholder", "filter…"))}" autocomplete="off"></label>\n')
    if meta["legend"]:
        out.append('  <div class="legend">\n' + "".join(f"    <span>{inline(x)}</span>\n" for x in meta["legend"]) + "  </div>\n")
    out.append('</div>\n\n<div class="grid" id="grid">\n')
    for s in meta["sections"]:
        where = f' <span class="where">{inline(s["where"])}</span>' if s["where"] else ""
        widest = max((len(html.unescape(re.sub(r"<[^>]+>", "", inline(k)))) for k, _ in s["rows"]), default=0)
        stack = " stack" if widest > STACK_AT else ""
        out.append(f'\n<section class="c-{s["color"]}{stack}"><h2>{inline(s["title"])}{where}</h2><table>\n')
        out += [f'<tr><td class="k">{inline(k)}</td><td class="d">{inline(d)}</td></tr>\n' for k, d in s["rows"]]
        out.append("</table>")
        out += [f'\n<div class="note">{inline(n)}</div>' for n in s["notes"]]
        out.append("</section>\n")
    out.append('\n</div>\n<p class="none" id="none">No key matches that filter.</p>\n\n')
    out.append(FOOTER + '\n</div>\n<script src="filter.js"></script>\n</body>\n</html>\n')
    return "".join(out)


def index(sheets):
    out = [head("Cheat Sheets"), '<div class="wrap">\n<header>\n  <div>\n',
           '    <h1><span class="dollar">~</span>/cheatsheets<span class="cur">▍</span></h1>\n',
           '    <p class="sub">Keyboard shortcuts and commands for everyday developer tools. '
           'Every sheet has a filter box: press <kbd>/</kbd> and type.</p>\n  </div>\n</header>\n']
    cats = CATEGORIES + sorted({m.get("category", "Other") for m in sheets} - set(CATEGORIES))
    for cat in cats:
        group = sorted((m for m in sheets if m.get("category", "Other") == cat), key=lambda m: (int(m.get("order", 100)), m["name"]))
        if not group:
            continue
        out.append(f'\n<h2 class="cat">{html.escape(cat)}</h2>\n<div class="cards">\n')
        for m in group:
            samples = "".join(f"<span>{inline(x)}</span>" for x in m["sample"])
            out.append(f'  <a class="card t-{m.get("color", "purple")}" href="{m["slug"]}.html">\n'
                       f'    <h3>{html.escape(m.get("card", m["name"]))}</h3>\n'
                       f'    <p>{inline(m.get("blurb", ""))}</p>\n'
                       f'    <div class="keys">{samples}</div>\n'
                       f'    <span class="go">Open →</span>\n  </a>\n')
        out.append("</div>\n")
    out.append("\n" + FOOTER + "\n</div>\n</body>\n</html>\n")
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(description="Build the cheat sheets.")
    ap.add_argument("-o", "--out", type=pathlib.Path, default=ROOT / "site", help="output folder (default: site/)")
    out = ap.parse_args().out.resolve()
    if out in (ROOT, ROOT / "src", ROOT / "assets") or out in ROOT.parents:
        raise SystemExit(f"refusing to build into {out}")

    sheets = [parse(p) for p in sorted((ROOT / "src").glob("*.txt"))]
    if out.exists():
        shutil.rmtree(out)  # the output folder only ever holds generated files
    shutil.copytree(ROOT / "assets", out)
    for m in sheets:
        (out / f'{m["slug"]}.html').write_text(sheet(m), encoding="utf-8")
    (out / "index.html").write_text(index(sheets), encoding="utf-8")
    print(f"built {len(sheets)} sheets + index.html in {out}")


if __name__ == "__main__":
    main()
