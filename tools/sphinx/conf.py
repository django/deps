"""Sphinx configuration for the DEPs static site.

Lives at tools/sphinx/conf.py and is copied to _generated/conf.py by
tools/generate.py before sphinx-build runs.
"""
import os
import sys
from pathlib import Path

# _generated/_ext is added when this conf is run from _generated/.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "_ext"))

project = "Django Enhancement Proposals"
copyright = "Django Software Foundation and individual contributors"
author = "Django contributors"

extensions = ["dep_index"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "_data", "Thumbs.db", ".DS_Store"]

# RST is the dominant format; .md template is linked to GitHub.
source_suffix = {".rst": "restructuredtext"}
master_doc = "index"

# dirhtml emits dep/0009/index.html so URLs are /dep/0009/.
html_theme = "alabaster"
html_static_path = ["_static"]
html_css_files = ["dep.css"]
html_show_sphinx = False
html_show_sourcelink = False
html_baseurl = os.environ.get("DEP_SITE_BASEURL", "")

html_theme_options = {
    "description": "Formal proposals for major Django features",
    "github_user": "django",
    "github_repo": "deps",
    "fixed_sidebar": True,
    "page_width": "1080px",
    "sidebar_width": "240px",
}

html_context = {
    "github_user": "django",
    "github_repo": "deps",
    "github_branch": "main",
}

# Suppress warnings for the "orphan" status of every DEP page (intentional).
suppress_warnings = ["toc.not_included"]
