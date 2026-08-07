# DEPs static-site build

These files build a static website from the DEP source files at the repo root.
The site provides:

- **Status-independent permalinks** at `/dep/<id>/` (e.g. `/dep/0009/`) so links
  survive when a DEP moves between status folders.
- An **index page** with filter-by-status / type / author and sort-by-date.
- Auto-deploy to **GitHub Pages** via `.github/workflows/pages.yml`.

## Local build

```sh
python -m venv .venv
.venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/generate.py
.venv/bin/sphinx-build -b dirhtml _generated _site
.venv/bin/python -m http.server -d _site 8000
```

Then open <http://localhost:8000/>.

## Layout

| Path | Purpose |
|---|---|
| `tools/generate.py` | Parses every DEP, emits a flat `_generated/dep/<id>.rst` source tree plus `_generated/_data/deps.json`. |
| `tools/sphinx/conf.py` | Sphinx config (uses the `dirhtml` builder for clean URLs). |
| `tools/sphinx/_ext/dep_index.py` | Custom `.. dep-index::` directive used on the landing page. |
| `tools/sphinx/_static/dep.css` | Minimal styling with Django-green accents. |
| `tools/sphinx/_templates/page.html` | Adds an "Edit on GitHub" footer to each DEP page. |

## Permalink rules

- DEPs with a numeric filename prefix (`0009-async.rst`) → `/dep/0009/`.
- Drafts without a number (`content-negotiation.rst`) → `/dep/draft-<stem>/`,
  shown in the index under the "Draft (unnumbered)" status filter.
- If two files claim the same numeric ID, the one in the most-advanced status
  folder keeps `/dep/<id>/`; the other gets `/dep/<id>-<stem>/` and a build
  log warning.
