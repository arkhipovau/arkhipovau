#!/usr/bin/env python3
"""Download Readymag page images from arkhipovau.xyz into assets/images/."""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

SITE_URL = "https://arkhipovau.xyz/"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "images"
IMAGE_RE = re.compile(
    r"https://i-p\.rmcdn\.net/63faf138af6989002f8ba446/4565454/image-[a-f0-9-]+\.(?:jpg|webp)"
)
SKIP_SLUGS = {"u1602287286", "arkhipovau", "main"}


def fetch(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_pages(html: str) -> dict[str, dict[str, str | None]]:
    html = html.replace("&quot;", '"')
    pages: dict[str, dict[str, str | None]] = {}
    for part in re.split(r'\{"_id":"', html)[1:]:
        uri_m = re.search(r'"uri":"([^"]+)"', part)
        ss_m = re.search(r'"screenshot":"(https://c-p[^"]+\.jpg)"', part)
        hu_m = re.search(r'"htmlUrl":"(https://c-p[^"]+\.html)"', part)
        if not uri_m or uri_m.group(1) in pages:
            continue
        pages[uri_m.group(1)] = {
            "screenshot": ss_m.group(1) if ss_m else None,
            "htmlUrl": hu_m.group(1) if hu_m else None,
        }
    return pages


def download_slug(slug: str, meta: dict[str, str | None]) -> int:
    dest = OUT / slug
    dest.mkdir(parents=True, exist_ok=True)
    count = 0

    if meta.get("htmlUrl"):
        snippet = fetch(meta["htmlUrl"]).decode("utf-8", "replace")
        urls = sorted(set(IMAGE_RE.findall(snippet)))
        for url in urls:
            fname = url.rsplit("/", 1)[-1]
            out = dest / fname
            if out.exists():
                continue
            out.write_bytes(fetch(f"{url}?w=1600"))
            count += 1
            print(f"  {fname}")

    if meta.get("screenshot"):
        cover = dest / "cover.jpg"
        try:
            data = fetch(meta["screenshot"])
            if len(data) > 1000:
                cover.write_bytes(data)
                print("  cover.jpg")
        except Exception as exc:
            print(f"  cover skipped ({exc})")

    return count


def write_manifest(pages: dict[str, dict[str, str | None]]) -> None:
    manifest: dict[str, dict] = {}
    for slug in sorted(pages):
        if slug in SKIP_SLUGS:
            continue
        dest = OUT / slug
        if not dest.exists():
            continue
        imgs = sorted(
            f"assets/images/{slug}/{p.name}"
            for p in dest.glob("image-*.*")
            if p.suffix.lower() in {".jpg", ".webp", ".png"}
        )
        cover_path = dest / "cover.jpg"
        cover = (
            f"assets/images/{slug}/cover.jpg"
            if cover_path.exists() and cover_path.stat().st_size > 1000
            else None
        )
        if imgs or cover:
            manifest[slug] = {"cover": cover, "images": imgs}

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def main() -> int:
    print(f"Fetching {SITE_URL}")
    html = fetch(SITE_URL).decode("utf-8", "replace")
    pages = parse_pages(html)
    print(f"Found {len(pages)} pages")

    favicon = OUT / "favicon.png"
    if not favicon.exists():
        try:
            favicon.write_bytes(
                fetch(
                    "https://c-p.rmcdn.net/63faf138af6989002f8ba446/"
                    "Favicon-d24c0334-4dec-45a1-8f59-3b17323c93b7_144.png"
                )
            )
            print("Saved favicon.png")
        except Exception as exc:
            print(f"favicon skipped ({exc})")

    total = 0
    for slug, meta in sorted(pages.items()):
        if slug in SKIP_SLUGS:
            continue
        print(slug)
        total += download_slug(slug, meta)

    # Homepage widget images live on the main page snippet.
    if "main" in pages:
        print("main (homepage heroes)")
        total += download_slug("main", pages["main"])

    write_manifest(pages)
    print(f"Done — {total} new images, manifest at assets/images/manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
