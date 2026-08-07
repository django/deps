"""Sphinx extension providing the ``.. dep-index::`` directive.

The directive reads ``_data/deps.json`` (produced by tools/generate.py) and
renders a filterable, sortable table of all DEPs. Filter UI runs in the browser
on a static JSON blob embedded in the page.
"""
from __future__ import annotations

import json
from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.application import Sphinx


STATUS_ORDER = ["accepted", "draft", "final", "rejected", "superseded", "withdrawn"]


def _row_html(dep: dict) -> str:
    is_unnumbered = not dep.get("id")
    status = dep["status"]
    status_class = "draft-unnumbered" if is_unnumbered and status == "draft" else status
    status_label = "Draft (unnumbered)" if is_unnumbered and status == "draft" else status.title()
    dep_label = dep.get("id") or "—"
    authors = ", ".join(dep.get("authors") or []) or "—"
    created = dep.get("created") or ""
    last_modified = dep.get("last_modified") or ""
    type_ = dep.get("type") or ""
    title = dep["title"]
    permalink = dep["permalink"]
    return (
        f'<tr data-status="{status_class}" data-type="{type_}" '
        f'data-authors="{authors.lower()}" data-created="{created}" '
        f'data-modified="{last_modified}" data-id="{dep_label}">'
        f'<td class="dep-id">{dep_label}</td>'
        f'<td><a href="{permalink}">{title}</a></td>'
        f'<td><span class="dep-status dep-status-{status_class}">{status_label}</span></td>'
        f'<td>{type_}</td>'
        f'<td>{authors}</td>'
        f'<td>{created}</td>'
        f'<td>{last_modified}</td>'
        "</tr>"
    )


def _build_html(deps: list[dict]) -> str:
    statuses = sorted(
        {("draft-unnumbered" if not d.get("id") and d["status"] == "draft" else d["status"]) for d in deps},
        key=lambda s: (STATUS_ORDER.index(s.split("-")[0]) if s.split("-")[0] in STATUS_ORDER else 99, s),
    )
    types = sorted({d.get("type") or "" for d in deps if d.get("type")})

    status_options = "".join(
        f'<option value="{s}">{("Draft (unnumbered)" if s == "draft-unnumbered" else s.title())}</option>'
        for s in statuses
    )
    type_options = "".join(f'<option value="{t}">{t}</option>' for t in types)

    rows = "\n".join(_row_html(d) for d in deps)
    total = len(deps)

    return f"""
<div class="dep-index-controls">
  <label>Status
    <select id="dep-filter-status" multiple size="6">{status_options}</select>
  </label>
  <label>Type
    <select id="dep-filter-type" multiple size="6">{type_options}</select>
  </label>
  <label>Author contains
    <input id="dep-filter-author" type="search" placeholder="e.g. Godwin">
  </label>
  <label>&nbsp;
    <button type="button" id="dep-filter-reset">Reset filters</button>
  </label>
  <div class="dep-index-summary"><span id="dep-index-count">{total}</span> of {total} DEPs</div>
</div>
<table class="dep-index" id="dep-index">
  <thead>
    <tr>
      <th data-sort="id">DEP <span class="sort-indicator">↕</span></th>
      <th data-sort="title">Title <span class="sort-indicator">↕</span></th>
      <th data-sort="status">Status <span class="sort-indicator">↕</span></th>
      <th data-sort="type">Type <span class="sort-indicator">↕</span></th>
      <th data-sort="authors">Author(s) <span class="sort-indicator">↕</span></th>
      <th data-sort="created">Created <span class="sort-indicator">↕</span></th>
      <th data-sort="modified">Last modified <span class="sort-indicator">↕</span></th>
    </tr>
  </thead>
  <tbody>
{rows}
  </tbody>
</table>
<script>
(function () {{
  const table = document.getElementById("dep-index");
  if (!table) return;
  const tbody = table.tBodies[0];
  const rows = Array.from(tbody.rows);
  const statusEl = document.getElementById("dep-filter-status");
  const typeEl = document.getElementById("dep-filter-type");
  const authorEl = document.getElementById("dep-filter-author");
  const countEl = document.getElementById("dep-index-count");
  const resetEl = document.getElementById("dep-filter-reset");
  let sortKey = "id";
  let sortDir = 1;

  function selectedValues(el) {{
    return Array.from(el.selectedOptions).map(o => o.value);
  }}

  function readState() {{
    const params = new URLSearchParams(window.location.hash.slice(1));
    const statuses = (params.get("status") || "").split(",").filter(Boolean);
    const types = (params.get("type") || "").split(",").filter(Boolean);
    const author = params.get("author") || "";
    Array.from(statusEl.options).forEach(o => o.selected = statuses.includes(o.value));
    Array.from(typeEl.options).forEach(o => o.selected = types.includes(o.value));
    authorEl.value = author;
    sortKey = params.get("sort") || "id";
    sortDir = params.get("dir") === "desc" ? -1 : 1;
  }}

  function writeState() {{
    const params = new URLSearchParams();
    const s = selectedValues(statusEl).join(",");
    const t = selectedValues(typeEl).join(",");
    if (s) params.set("status", s);
    if (t) params.set("type", t);
    if (authorEl.value) params.set("author", authorEl.value);
    if (sortKey !== "id") params.set("sort", sortKey);
    if (sortDir === -1) params.set("dir", "desc");
    const h = params.toString();
    history.replaceState(null, "", h ? "#" + h : window.location.pathname);
  }}

  function applyFilters() {{
    const statuses = selectedValues(statusEl);
    const types = selectedValues(typeEl);
    const author = authorEl.value.trim().toLowerCase();
    let visible = 0;
    for (const r of rows) {{
      const okStatus = !statuses.length || statuses.includes(r.dataset.status);
      const okType = !types.length || types.includes(r.dataset.type);
      const okAuthor = !author || r.dataset.authors.includes(author);
      const show = okStatus && okType && okAuthor;
      r.classList.toggle("hidden", !show);
      if (show) visible++;
    }}
    countEl.textContent = visible;
    writeState();
  }}

  function applySort() {{
    const sorted = rows.slice().sort((a, b) => {{
      const av = a.dataset[sortKey] || a.cells[headerIndex(sortKey)].textContent;
      const bv = b.dataset[sortKey] || b.cells[headerIndex(sortKey)].textContent;
      if (av === bv) return 0;
      return av < bv ? -sortDir : sortDir;
    }});
    sorted.forEach(r => tbody.appendChild(r));
    table.querySelectorAll("th").forEach(th => {{
      const ind = th.querySelector(".sort-indicator");
      if (!ind) return;
      ind.textContent = th.dataset.sort === sortKey ? (sortDir === 1 ? "↑" : "↓") : "↕";
    }});
  }}

  function headerIndex(key) {{
    const ths = Array.from(table.tHead.rows[0].cells);
    return ths.findIndex(th => th.dataset.sort === key);
  }}

  table.tHead.addEventListener("click", e => {{
    const th = e.target.closest("th");
    if (!th || !th.dataset.sort) return;
    if (sortKey === th.dataset.sort) sortDir *= -1; else {{ sortKey = th.dataset.sort; sortDir = 1; }}
    applySort();
    writeState();
  }});

  [statusEl, typeEl, authorEl].forEach(el => el.addEventListener("input", applyFilters));
  resetEl.addEventListener("click", () => {{
    Array.from(statusEl.options).forEach(o => o.selected = false);
    Array.from(typeEl.options).forEach(o => o.selected = false);
    authorEl.value = "";
    sortKey = "id"; sortDir = 1;
    applyFilters();
    applySort();
  }});
  window.addEventListener("hashchange", () => {{ readState(); applyFilters(); applySort(); }});

  readState();
  applyFilters();
  applySort();
}})();
</script>
"""


class DepIndexDirective(Directive):
    has_content = False
    required_arguments = 0
    optional_arguments = 0

    def run(self):
        env = self.state.document.settings.env
        data_path = Path(env.srcdir) / "_data" / "deps.json"
        deps = json.loads(data_path.read_text(encoding="utf-8"))
        # Sort by id for stable initial ordering; unnumbered drafts last.
        deps.sort(key=lambda d: (d.get("id") is None, d.get("id") or d["slug"]))
        return [nodes.raw("", _build_html(deps), format="html")]


def setup(app: Sphinx):
    app.add_directive("dep-index", DepIndexDirective)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
