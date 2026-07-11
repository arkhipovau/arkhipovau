#!/usr/bin/env python3
"""Build local project case-study pages from Readymag snippets + image manifest."""

from __future__ import annotations

import html
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "assets" / "images" / "manifest.json"
SITE_URL = "https://arkhipovau.xyz/"
SKIP_SLUGS = {"playground", "main", "about", "research", "cover-letter", "arkhipovau", "u1602287286"}

IMAGE_RE = re.compile(r"image-[a-f0-9-]+\.(?:jpg|webp|png)")
NAV_SKIP = {
    "Julie Arkhipova",
    "Work",
    "Index",
    "Research",
    "Playground",
    "About",
    "Portfolio Research Playground About",
    "PortfolioResearchPlaygroundAbout",
    "This is a celebration, not a tournament",
}
RESEARCH_SLUGS = {
    "perception-of-beauty-in-the-installations-of-olafur-eliasson",
    "the-eyes-of-the-middle-ages-expressing-spiritual-dynamics-in-sculpture",
}

YEAR_BY_SLUG = {
    "moretime": "2024",
    "run-ops": "2024",
    "tokensfarm": "2023",
    "burger-records": "2023",
    "geoprotech": "2023",
    "white-secret-mouthfresher": "2023",
    "artdom": "2023",
    "magic-mirror": "2022",
    "illustrations-pack": "2021",
    "perception-of-beauty-in-the-installations-of-olafur-eliasson": "2023",
    "the-eyes-of-the-middle-ages-expressing-spiritual-dynamics-in-sculpture": "2023",
}


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": SITE_URL,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def parse_pages(site_html: str) -> dict[str, dict[str, str | None]]:
    site_html = site_html.replace("&quot;", '"')
    pages: dict[str, dict[str, str | None]] = {}
    for part in re.split(r'\{"_id":"', site_html)[1:]:
        uri_m = re.search(r'"uri":"([^"]+)"', part)
        title_m = re.search(r'"title":"([^"]*)"', part)
        hu_m = re.search(r'"htmlUrl":"(https://c-p[^"]+\.html)"', part)
        if not uri_m or uri_m.group(1) in pages:
            continue
        pages[uri_m.group(1)] = {
            "title": title_m.group(1) if title_m else uri_m.group(1),
            "htmlUrl": hu_m.group(1) if hu_m else None,
        }
    return pages


def clean_text(raw: str) -> str:
    text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw)).strip())
    return text


def should_skip_text(text: str) -> bool:
    if not text or text in NAV_SKIP:
        return True
    lower = text.lower()
    if "@" in text or "instagram" in lower or "linkedin" in lower or "behance" in lower:
        return True
    if text.startswith("Julie Arkhipova"):
        return True
    return False


def parse_snippet(snip: str) -> list[dict]:
    blocks: list[dict] = []
    for m in re.finditer(r'<div class="rmwidget ([^"]+)"[^>]*style="([^"]*)"', snip):
        classes, style = m.group(1), m.group(2)
        chunk = snip[m.end() : m.end() + 4000]
        top_m = re.search(r"top:\s*([\d.]+)px", style)
        if not top_m:
            continue
        top = float(top_m.group(1))
        if "widget-picture" in classes:
            im = IMAGE_RE.search(chunk)
            if im:
                blocks.append({"top": top, "type": "img", "id": im.group(0)})
        elif "widget-text-v3" in classes:
            tm = re.search(r'<div class="text-viewer">(.*?)</div></div></div>', chunk, re.S)
            if not tm:
                continue
            text = clean_text(tm.group(1))
            if should_skip_text(text):
                continue
            blocks.append({"top": top, "type": "text", "content": text})
    blocks.sort(key=lambda b: b["top"])
    return blocks


def parse_meta_line(text: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    if "My Role:" in text:
        role = re.search(r"My Role:\s*(.+?)(?:Discipline:|Team:|$)", text)
        if role:
            meta["role"] = role.group(1).strip()
    if "Discipline:" in text and "My Role:" in text:
        disc = re.search(r"Discipline:\s*(.+?)(?:Team:|$)", text)
        if disc:
            meta["discipline"] = disc.group(1).strip()
    if "Team:" in text and "My Role:" in text:
        team = re.search(r"Team:\s*(.+)$", text)
        if team:
            meta["team"] = team.group(1).strip()
    return meta


def is_title_text(text: str, title: str) -> bool:
    norm = re.sub(r"[^\w]", "", text.lower())
    title_norm = re.sub(r"[^\w]", "", title.lower())
    return norm == title_norm or (len(text) < 48 and title.lower() in text.lower())


def is_meta_line(text: str) -> bool:
    return "My Role:" in text and "Discipline:" in text


def is_structure_line(text: str) -> bool:
    return bool(re.match(r"^\d{4}\s*Structure:", text))


def is_section_heading(text: str) -> bool:
    if len(text) > 80:
        return False
    if text.endswith(".") and len(text.split()) > 6:
        return False
    if re.match(r"^(Introduction|Concept|Conclusion|Bibliography|France|Flanders|Germany|Italy|Space, Time)", text):
        return True
    if re.match(r"^[A-Z][^.!?]{0,60}$", text) and len(text.split()) <= 8:
        return True
    return False


def image_path_map(slug: str, manifest: dict) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for path in manifest.get(slug, {}).get("images", []):
        fname = Path(path).name
        mapping[fname] = path
    return mapping


def build_project_content(slug: str, title: str, blocks: list[dict], img_map: dict[str, str]) -> dict:
    header_meta: dict[str, str] = {}
    lede = ""
    body: list[dict] = []
    seen_texts: set[str] = set()

    for block in blocks:
        if block["type"] == "text":
            text = block["content"]
            if text in seen_texts:
                continue
            if is_title_text(text, title):
                seen_texts.add(text)
                continue
            if is_meta_line(text):
                header_meta.update(parse_meta_line(text))
                seen_texts.add(text)
                continue
            if is_structure_line(text):
                body.append({"type": "meta", "content": text})
                seen_texts.add(text)
                continue
            if not lede and len(text) > 60 and slug not in RESEARCH_SLUGS and not text.startswith(("Purpose:", "Mission:", "Challenge:")):
                lede = text
                seen_texts.add(text)
                continue
            if slug in RESEARCH_SLUGS and not lede and len(text) > 40:
                if is_title_text(text, title):
                    continue
                lede = text
                seen_texts.add(text)
                continue
            seen_texts.add(text)
            if slug in RESEARCH_SLUGS and is_section_heading(text):
                body.append({"type": "heading", "content": text})
            elif text.startswith(("Purpose:", "Mission:", "Challenge:")):
                body.append({"type": "prose", "content": text})
            elif len(text) < 72 and slug == "illustrations-pack":
                body.append({"type": "caption", "content": text})
            else:
                body.append({"type": "prose", "content": text})
        else:
            fname = block["id"]
            rel = img_map.get(fname)
            if rel:
                body.append({"type": "img", "src": f"../{rel}"})
            else:
                body.append({"type": "img", "src": f"../assets/images/{slug}/{fname}"})

    # Append any manifest images missing from snippet order
    used = {b["src"] for b in body if b["type"] == "img"}
    for path in img_map.values():
        src = f"../{path}"
        if src not in used:
            body.append({"type": "img", "src": src})

    return {
        "title": title,
        "year": YEAR_BY_SLUG.get(slug, ""),
        "lede": lede,
        "meta": header_meta,
        "body": body,
        "essay": slug in RESEARCH_SLUGS,
    }


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def render_meta_dl(meta: dict[str, str]) -> str:
    rows = []
    labels = {"role": "Role", "discipline": "Discipline", "team": "Team"}
    for key, label in labels.items():
        if meta.get(key):
            rows.append(f"      <div class=\"project-meta__row\"><dt>{label}</dt><dd>{esc(meta[key])}</dd></div>")
    if not rows:
        return ""
    return "    <dl class=\"project-meta type-meta\">\n" + "\n".join(rows) + "\n    </dl>\n"


def render_body(body: list[dict], essay: bool) -> str:
    parts: list[str] = []
    for block in body:
        if block["type"] == "img":
            parts.append(
                f'      <figure class="project-figure">'
                f'<img src="{esc(block["src"])}" alt="" loading="lazy" decoding="async"></figure>'
            )
        elif block["type"] == "heading":
            parts.append(f'      <h2 class="project-section__title">{esc(block["content"])}</h2>')
        elif block["type"] == "caption":
            parts.append(f'      <p class="project-caption type-meta">{esc(block["content"])}</p>')
        elif block["type"] == "meta":
            parts.append(f'      <p class="project-structure type-meta">{esc(block["content"])}</p>')
        else:
            cls = "project-prose type-serif" if essay else "project-prose"
            parts.append(f'      <p class="{cls}">{esc(block["content"])}</p>')
    return "\n".join(parts)


def render_page(slug: str, content: dict) -> str:
    title = content["title"]
    year = content["year"]
    essay = content["essay"]
    main_class = "page-main page-main--project"
    if essay:
        main_class += " page-main--essay"

    year_html = f'      <p class="project-header__year type-meta">{esc(year)}</p>\n' if year else ""
    lede_html = f'      <p class="project-lead type-serif">{esc(content["lede"])}</p>\n' if content["lede"] else ""
    meta_html = render_meta_dl(content["meta"])
    body_html = render_body(content["body"], essay)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Julie Arkhipova — {esc(title)}">
  <title>{esc(title)} — Julie Arkhipova</title>
  <link rel="icon" href="../assets/images/favicon.png" type="image/png">
  <link rel="stylesheet" href="../site.css">
</head>
<body data-page="project">

  <main class="{main_class}">
    <header class="project-header">
      <p class="project-header__back type-menu"><a href="../" class="link">Work</a></p>
      <h1 class="project-header__title">{esc(title)}</h1>
{year_html}{meta_html}{lede_html}    </header>

    <div class="project-body">
{body_html}
    </div>
  </main>

  <div class="toast" id="toast" aria-live="polite"></div>
  <script src="../site.js"></script>
</body>
</html>
"""


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text())
    site_html = fetch(SITE_URL)
    pages = parse_pages(site_html)

    built = 0
    for slug in sorted(manifest):
        if slug in SKIP_SLUGS:
            continue
        if slug not in pages or not pages[slug].get("htmlUrl"):
            print(f"skip {slug}: no live snippet")
            continue

        snip = fetch(pages[slug]["htmlUrl"])
        blocks = parse_snippet(snip)
        img_map = image_path_map(slug, manifest)
        content = build_project_content(slug, pages[slug]["title"], blocks, img_map)

        out_dir = ROOT / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "index.html"
        out_path.write_text(render_page(slug, content), encoding="utf-8")
        print(f"built {out_path.relative_to(ROOT)} ({len(content['body'])} blocks)")
        built += 1

    print(f"\nDone — {built} project pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
