# arkhipovau

Portfolio of [Julie Arkhipova](https://github.com/arkhipovau) — identity, digital product, and research.

**Status:** work in progress. See [MANUAL.md](./MANUAL.md) for local setup, structure, and WIP checklist.

## Local preview

```bash
python3 -m http.server 8080
```

Open [http://localhost:8080](http://localhost:8080).

## GitHub Pages

**Project URL (after Pages is enabled):**  
https://arkhipovau.github.io/arkhipovau/

`https://arkhipovau.github.io/` alone will 404 — that root is only for a separate `arkhipovau.github.io` repository.

### Enable hosting

1. Repo → **Settings** → **Pages**
2. **Build and deployment** → Source: **GitHub Actions**
3. Push to `main` runs `.github/workflows/pages.yml` automatically

First deploy may take 1–3 minutes.

## Stack

Static HTML, CSS, and JavaScript — no build step required to view the site.

Content scripts (optional): `scripts/download-readymag-images.py`, `scripts/build-project-pages.py`.
