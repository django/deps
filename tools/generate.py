"""Pre-build step: scan DEP source files and emit a flat Sphinx source tree.

For each DEP found in the status directories (accepted/, draft/, final/,
rejected/, superseded/, withdrawn/) this script produces:

    _generated/dep/<id>.rst        - flat per-DEP source (filename = DEP id)
    _generated/dep/draft-<slug>.rst - for non-numbered drafts
    _generated/_data/deps.json     - metadata array consumed by the index page
    _generated/index.rst           - landing page calling the dep-index directive
    _generated/conf.py             - Sphinx config (copied from tools/sphinx/)
    _generated/_static/, _templates/, _ext/ - copied from tools/sphinx/

The output of this script is consumed by `sphinx-build -b dirhtml`.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
SPHINX_SRC = TOOLS_DIR / "sphinx"
OUT = REPO_ROOT / "_generated"

STATUS_DIRS = ["accepted", "draft", "final", "rejected", "superseded", "withdrawn"]

# Lines like "  :Field Name: value" or "Field Name: value" at the top of file.
META_RE = re.compile(r"^:?(?P<key>[A-Za-z][A-Za-z \-]*?):\s*(?P<val>.*)$")
# RST title underline characters
UNDERLINE_RE = re.compile(r"^[=\-~`'\"^_*+#<>]+$")
# DEP id from filename like 0009-async.rst -> "0009"
DEP_FILENAME_RE = re.compile(r"^(?P<id>\d{1,5})-")


@dataclass
class Dep:
    id: str | None
    slug: str
    title: str
    status: str
    type: str | None
    authors: list[str]
    created: str | None
    last_modified: str | None
    source_path: str  # relative to repo root, used for "Edit on GitHub"
    permalink: str = field(init=False)

    def __post_init__(self) -> None:
        # Relative path so the site works regardless of deploy subpath
        # (the index page that uses these is always at the site root).
        self.permalink = f"dep/{self.slug}/"


def normalise_key(raw: str) -> str:
    return raw.strip().lower().replace("-", " ")


def split_authors(raw: str) -> list[str]:
    # Authors may be comma-separated; trim trailing "et al." / "others ...".
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return [re.sub(r"\s+et al\.?$", "", p, flags=re.I) for p in parts]


def parse_iso_date(raw: str) -> str | None:
    raw = raw.strip()
    try:
        return date.fromisoformat(raw[:10]).isoformat()
    except ValueError:
        return None


def extract_title(lines: list[str]) -> str:
    """Return the first heading text. Handles both over-and-underline and
    underline-only RST title styles."""
    for i, line in enumerate(lines[:10]):
        if UNDERLINE_RE.fullmatch(line.strip()) and len(line.strip()) >= 3:
            # Title is the line above (underline-only) or below (over+under).
            if i > 0 and lines[i - 1].strip():
                return lines[i - 1].strip()
            if i + 1 < len(lines) and lines[i + 1].strip():
                return lines[i + 1].strip()
    return "(untitled)"


def parse_metadata(lines: list[str]) -> dict[str, str]:
    """Scan the top of the file for metadata lines.

    Stops at the first blank line that follows at least one metadata hit, or at
    the first non-metadata content line after the title block.
    """
    meta: dict[str, str] = {}
    seen_meta = False
    in_title_block = True
    for line in lines[:80]:
        stripped = line.strip()
        if not stripped:
            if seen_meta:
                break
            continue
        if UNDERLINE_RE.fullmatch(stripped):
            in_title_block = False
            continue
        m = META_RE.match(stripped)
        if m:
            key = normalise_key(m.group("key"))
            val = m.group("val").strip()
            if val:
                meta[key] = val
                seen_meta = True
            continue
        if seen_meta and not in_title_block:
            # Hit a non-metadata content line.
            break
    return meta


def slug_from_filename(filename: str) -> str:
    # e.g. "content-negotiation.rst" -> "content-negotiation"
    return Path(filename).stem


def build_dep(path: Path, status: str) -> Dep:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    meta = parse_metadata(lines)
    title = extract_title(lines)

    # Determine the ID: prefer filename numeric prefix, fall back to :DEP:.
    fname_match = DEP_FILENAME_RE.match(path.name)
    if fname_match:
        dep_id = fname_match.group("id").zfill(4)
        slug = dep_id
    elif "dep" in meta and meta["dep"].strip().isdigit():
        dep_id = meta["dep"].strip().zfill(4)
        slug = dep_id
    else:
        dep_id = None
        slug = f"draft-{slug_from_filename(path.name)}"

    authors = split_authors(meta.get("author", "")) if meta.get("author") else []
    return Dep(
        id=dep_id,
        slug=slug,
        title=title,
        status=status,
        type=meta.get("type"),
        authors=authors,
        created=parse_iso_date(meta["created"]) if meta.get("created") else None,
        last_modified=parse_iso_date(meta["last modified"]) if meta.get("last modified") else None,
        source_path=str(path.relative_to(REPO_ROOT)),
    )


# Status precedence used to pick which DEP keeps the canonical /dep/<id>/ slug
# when two files share a numeric ID (e.g. someone re-used "0007" in a draft).
STATUS_PRIORITY = {"final": 0, "accepted": 1, "superseded": 2, "withdrawn": 3, "rejected": 4, "draft": 5}


def collect() -> list[Dep]:
    deps: list[Dep] = []
    for status in STATUS_DIRS:
        d = REPO_ROOT / status
        if not d.is_dir():
            continue
        for path in sorted(d.iterdir()):
            if not path.is_file():
                continue
            if path.suffix not in {".rst", ".md"}:
                continue
            if path.name.lower().startswith("readme"):
                continue
            deps.append(build_dep(path, status))
    return resolve_slug_collisions(deps)


def resolve_slug_collisions(deps: list[Dep]) -> list[Dep]:
    """If two DEPs share a slug (same numeric ID), keep the canonical slug for
    the most-advanced status and append the file-stem to the other(s)."""
    by_slug: dict[str, list[Dep]] = {}
    for dep in deps:
        by_slug.setdefault(dep.slug, []).append(dep)
    for slug, group in by_slug.items():
        if len(group) <= 1:
            continue
        group.sort(key=lambda d: STATUS_PRIORITY.get(d.status, 99))
        for loser in group[1:]:
            stem = Path(loser.source_path).stem
            loser.slug = stem  # e.g. "0007-dependency-policy"
            loser.permalink = f"dep/{loser.slug}/"
            print(f"NOTE:  slug collision on '{slug}' -> '{loser.slug}' for {loser.source_path}", file=sys.stderr)
    return deps


def emit_dep_source(dep: Dep, dep_dir: Path) -> None:
    """Copy a DEP's content into the flat source tree, prefixed with :orphan:.

    The original metadata block remains so the rendered page still shows it.
    """
    src = REPO_ROOT / dep.source_path
    body = src.read_text(encoding="utf-8")
    out = dep_dir / f"{dep.slug}.rst"
    out.write_text(":orphan:\n\n" + body, encoding="utf-8")


def emit_index(deps: list[Dep], out_dir: Path) -> None:
    counts = {s: sum(1 for d in deps if d.status == s) for s in STATUS_DIRS}
    summary = ", ".join(f"{s}: {counts[s]}" for s in STATUS_DIRS if counts[s])
    content = f"""Django Enhancement Proposals
============================

Django Enhancement Proposals (DEPs) are formal proposals for large feature
additions to Django. See `DEP 1 <dep/0001/>`_ for the process.

This index lists every DEP across all status folders. Use the filters to narrow
by status, type, or author; click a column header to sort.

Totals: {summary}.

.. dep-index::

.. raw:: html

   <p style="margin-top:2em;font-size:.9em;color:#555">
     Want to write a DEP? See the
     <a href="https://github.com/django/deps/blob/main/template.rst">RST template</a>
     or the <a href="https://github.com/django/deps/blob/main/template.md">Markdown template</a>.
   </p>
"""
    (out_dir / "index.rst").write_text(content, encoding="utf-8")


def copy_sphinx_assets() -> None:
    for name in ("conf.py", "_static", "_templates", "_ext"):
        src = SPHINX_SRC / name
        dst = OUT / name
        if not src.exists():
            continue
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)


def validate(deps: list[Dep]) -> int:
    errors = 0
    for dep in deps:
        if not dep.id and not dep.slug.startswith("draft-"):
            print(f"ERROR: {dep.source_path}: no DEP id and not a draft slug", file=sys.stderr)
            errors += 1
        if not dep.authors:
            print(f"WARN:  {dep.source_path}: no Author metadata", file=sys.stderr)
        if not dep.created:
            print(f"WARN:  {dep.source_path}: no Created date", file=sys.stderr)
    return errors


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / "dep").mkdir()
    (OUT / "_data").mkdir()

    deps = collect()
    errors = validate(deps)

    for dep in deps:
        emit_dep_source(dep, OUT / "dep")
        label = dep.id or dep.slug
        print(f"  {label:<30} [{dep.status}] {dep.title}")

    (OUT / "_data" / "deps.json").write_text(
        json.dumps([asdict(d) for d in deps], indent=2),
        encoding="utf-8",
    )

    emit_index(deps, OUT)
    copy_sphinx_assets()

    print(f"\nGenerated {len(deps)} DEPs into {OUT.relative_to(REPO_ROOT)}/")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
