#!/usr/bin/env python3
"""Convert portfolio images to AVIF or WebP for smaller downloads without visible quality loss.

Uses ffmpeg (libaom-av1) for AVIF and cwebp for WebP. No Python dependencies required.

Examples:
  python3 scripts/convert-images.py
  python3 scripts/convert-images.py --format webp
  python3 scripts/convert-images.py --format avif --crf 18 --quality 92
  python3 scripts/convert-images.py --max-width 1600 --update-manifest
  python3 scripts/convert-images.py --lossless --dry-run
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "assets" / "images"
MANIFEST = DEFAULT_INPUT / "manifest.json"
CARD_HEROES = DEFAULT_INPUT / "card-heroes.json"

SOURCE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
OUTPUT_SUFFIXES = {".avif", ".webp"}


@dataclass
class ConvertResult:
    source: Path
    output: Path
    skipped: bool
    reason: str = ""
    src_bytes: int = 0
    out_bytes: int = 0


def find_tool(name: str) -> str | None:
    return shutil.which(name)


def human_size(num: int) -> str:
    if num < 1024:
        return f"{num} B"
    if num < 1024 * 1024:
        return f"{num / 1024:.1f} KB"
    return f"{num / (1024 * 1024):.1f} MB"


def iter_sources(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if path.name in {"favicon.png"}:
            continue
        files.append(path)
    return files


def output_path(source: Path, fmt: str, out_dir: Path | None) -> Path:
    base = source.with_suffix(f".{fmt}")
    if out_dir is None:
        return base
    rel = source.relative_to(DEFAULT_INPUT)
    return out_dir / rel.with_suffix(f".{fmt}")


def should_skip(source: Path, dest: Path, force: bool) -> bool:
    if force or not dest.exists():
        return False
    return dest.stat().st_mtime >= source.stat().st_mtime


def run_checked(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "unknown error").strip()
        raise RuntimeError(detail)


def convert_avif(
    source: Path,
    dest: Path,
    *,
    crf: int,
    lossless: bool,
    max_width: int | None,
    ffmpeg: str,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
    ]
    if max_width:
        cmd += ["-vf", f"scale='min({max_width},iw)':-2"]
    cmd += ["-c:v", "libaom-av1", "-cpu-used", "4", "-row-mt", "1"]
    if lossless:
        cmd += ["-lossless", "1"]
    else:
        cmd += ["-crf", str(crf)]
    cmd.append(str(dest))
    run_checked(cmd)


def convert_webp(
    source: Path,
    dest: Path,
    *,
    quality: int,
    lossless: bool,
    max_width: int | None,
    cwebp: str,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [cwebp, "-mt"]
    if lossless:
        cmd.append("-lossless")
    else:
        cmd += ["-q", str(quality)]
    if max_width:
        cmd += ["-resize", str(max_width), "0"]
    cmd += [str(source), "-o", str(dest)]
    run_checked(cmd)


def convert_one(
    source: Path,
    fmt: str,
    *,
    out_dir: Path | None,
    crf: int,
    quality: int,
    lossless: bool,
    max_width: int | None,
    force: bool,
    ffmpeg: str | None,
    cwebp: str | None,
) -> ConvertResult:
    dest = output_path(source, fmt, out_dir)
    src_bytes = source.stat().st_size

    if should_skip(source, dest, force):
        out_bytes = dest.stat().st_size if dest.exists() else 0
        return ConvertResult(source, dest, True, "up to date", src_bytes, out_bytes)

    if fmt == "avif":
        if not ffmpeg:
            raise RuntimeError("ffmpeg with libaom-av1 is required for AVIF")
        convert_avif(
            source,
            dest,
            crf=crf,
            lossless=lossless,
            max_width=max_width,
            ffmpeg=ffmpeg,
        )
    elif fmt == "webp":
        if not cwebp:
            raise RuntimeError("cwebp is required for WebP")
        convert_webp(
            source,
            dest,
            quality=quality,
            lossless=lossless,
            max_width=max_width,
            cwebp=cwebp,
        )
    else:
        raise ValueError(f"unsupported format: {fmt}")

    out_bytes = dest.stat().st_size
    return ConvertResult(source, dest, False, "", src_bytes, out_bytes)


def rel_asset(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def update_manifest(paths: dict[Path, Path]) -> int:
    changed = 0
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text())
        for slug, entry in manifest.items():
            images = entry.get("images") or []
            new_images: list[str] = []
            touched = False
            for item in images:
                src = ROOT / item
                dst = paths.get(src)
                if dst and dst.exists():
                    new_images.append(rel_asset(dst))
                    touched = True
                else:
                    new_images.append(item)
            cover = entry.get("cover")
            if cover:
                cover_src = ROOT / cover
                cover_dst = paths.get(cover_src)
                if cover_dst and cover_dst.exists():
                    entry["cover"] = rel_asset(cover_dst)
                    touched = True
            if touched:
                entry["images"] = new_images
                changed += 1
        MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")

    if CARD_HEROES.exists():
        heroes = json.loads(CARD_HEROES.read_text())
        touched = False
        for title, item in list(heroes.items()):
            src = ROOT / item
            dst = paths.get(src)
            if dst and dst.exists():
                heroes[title] = rel_asset(dst)
                touched = True
        if touched:
            CARD_HEROES.write_text(json.dumps(heroes, indent=2) + "\n")
            changed += 1

    return changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert images to AVIF or WebP with high visual quality."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=str(DEFAULT_INPUT),
        help="Input file or directory (default: assets/images)",
    )
    parser.add_argument(
        "--format",
        choices=("avif", "webp", "both"),
        default="avif",
        help="Output format (default: avif — smallest at high quality)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Write converted files here, preserving subfolders. "
        "Default: next to each source file.",
    )
    parser.add_argument(
        "--crf",
        type=int,
        default=20,
        help="AVIF quality via CRF; lower is better (default: 20, visually lossless)",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=90,
        help="WebP quality 0-100 (default: 90)",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        help="Resize so width never exceeds this value (keeps aspect ratio)",
    )
    parser.add_argument(
        "--lossless",
        action="store_true",
        help="Lossless encode (larger files, exact pixels)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reconvert even if output already exists",
    )
    parser.add_argument(
        "--update-manifest",
        action="store_true",
        help="Rewrite manifest.json and card-heroes.json to point at converted files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be converted",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    out_dir = args.output_dir.resolve() if args.output_dir else None
    formats = ["avif", "webp"] if args.format == "both" else [args.format]

    ffmpeg = find_tool("ffmpeg")
    cwebp = find_tool("cwebp")

    if "avif" in formats and not ffmpeg:
        print("error: ffmpeg not found (needed for AVIF)", file=sys.stderr)
        return 1
    if "webp" in formats and not cwebp:
        print("error: cwebp not found (needed for WebP)", file=sys.stderr)
        return 1

    if input_path.is_file():
        sources = [input_path]
    elif input_path.is_dir():
        sources = iter_sources(input_path)
    else:
        print(f"error: path not found: {input_path}", file=sys.stderr)
        return 1

    if not sources:
        print("No images found.")
        return 0

    print(
        f"Converting {len(sources)} file(s) → {', '.join(formats)} "
        f"({'lossless' if args.lossless else 'high quality'})"
    )

    results: list[ConvertResult] = []
    mapping: dict[Path, Path] = {}

    for source in sources:
        for fmt in formats:
            dest = output_path(source, fmt, out_dir)
            if args.dry_run:
                print(f"  would convert: {source.name} → {dest.name}")
                continue
            try:
                result = convert_one(
                    source,
                    fmt,
                    out_dir=out_dir,
                    crf=args.crf,
                    quality=args.quality,
                    lossless=args.lossless,
                    max_width=args.max_width,
                    force=args.force,
                    ffmpeg=ffmpeg,
                    cwebp=cwebp,
                )
            except RuntimeError as exc:
                print(f"  failed: {source.name} ({exc})", file=sys.stderr)
                return 1
            results.append(result)
            mapping[source] = result.output
            if result.skipped:
                print(f"  skip: {source.name} ({result.reason})")
            else:
                saved = result.src_bytes - result.out_bytes
                pct = (saved / result.src_bytes * 100) if result.src_bytes else 0
                print(
                    f"  ok: {source.name} → {result.output.name} "
                    f"({human_size(result.src_bytes)} → {human_size(result.out_bytes)}, "
                    f"-{pct:.0f}%)"
                )

    if args.dry_run:
        return 0

    converted = [r for r in results if not r.skipped]
    if converted:
        total_src = sum(r.src_bytes for r in converted)
        total_out = sum(r.out_bytes for r in converted)
        saved = total_src - total_out
        pct = (saved / total_src * 100) if total_src else 0
        print(
            f"\nDone — {len(converted)} converted, "
            f"{human_size(total_src)} → {human_size(total_out)} "
            f"({pct:.0f}% smaller)"
        )
    else:
        print("\nDone — nothing new to convert.")

    if args.update_manifest and mapping:
        changed = update_manifest(mapping)
        print(f"Updated {changed} manifest file(s).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
