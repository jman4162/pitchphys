"""Console-script entry point for the bundled Streamlit app.

Usage:
    pitchphys-app              # opens http://localhost:8501

The launcher locates ``streamlit_app.py`` from the bundled package
(``pitchphys/_app/`` after ``pip install pitchphys[app]``) or from a
source checkout (``app/streamlit_app.py`` at the repo root). It then
invokes ``streamlit run`` via the public Streamlit CLI.
"""

from __future__ import annotations

import sys
from importlib.resources import as_file, files
from pathlib import Path


def _resolve_app_path() -> str:
    """Locate ``streamlit_app.py`` (installed wheel first, source checkout next)."""
    try:
        bundled = files("pitchphys").joinpath("_app", "streamlit_app.py")
        if bundled.is_file():
            with as_file(bundled) as p:
                return str(p)
    except (ModuleNotFoundError, FileNotFoundError):
        pass
    # Source checkout fallback (src layout: parents[2] is the repo root).
    src_root = Path(__file__).resolve().parents[2]
    candidate = src_root / "app" / "streamlit_app.py"
    if candidate.is_file():
        return str(candidate)
    raise FileNotFoundError(
        "Could not locate streamlit_app.py. Reinstall with "
        "`pip install pitchphys[app]` or run from the repo root."
    )


def main() -> int:
    """Entry point; sets up sys.argv and shells out to Streamlit's CLI."""
    try:
        from streamlit.web import cli as stcli
    except ModuleNotFoundError as exc:
        print(
            "streamlit is not installed. Install the [app] extra with: "
            "`pip install pitchphys[app]`",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    app_path = _resolve_app_path()
    # Pass any extra CLI flags through to `streamlit run` (e.g.
    # `pitchphys-app --server.port 9000`).
    extra = sys.argv[1:]
    sys.argv = ["streamlit", "run", app_path, *extra]
    return int(stcli.main())


if __name__ == "__main__":
    raise SystemExit(main())
