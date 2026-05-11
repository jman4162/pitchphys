"""MkDocs pre-build hook: copy notebooks into docs/ so mkdocs-jupyter can render them.

`mkdocs-jupyter` requires notebook files to live under the docs directory.
Rather than duplicating notebooks in git (committing executed `.ipynb` outputs
in two places), we copy them at build time and gitignore the build-time copies.
"""

from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS_SRC = REPO_ROOT / "notebooks"
NOTEBOOKS_DST = REPO_ROOT / "docs" / "notebooks"


def on_pre_build(config):
    """Copy notebooks into docs/notebooks/ before mkdocs scans the docs tree."""
    NOTEBOOKS_DST.mkdir(parents=True, exist_ok=True)
    for nb in sorted(NOTEBOOKS_SRC.glob("*.ipynb")):
        target = NOTEBOOKS_DST / nb.name
        shutil.copy2(nb, target)
    return config
