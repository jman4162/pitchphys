"""Capture screenshots of every page of the pitchphys Streamlit app.

Usage (from the repo root):

    .venv/bin/playwright install chromium  # one-time, ~150 MB browser download
    .venv/bin/python scripts/capture_screenshots.py

By default this boots a local Streamlit server, navigates to each page,
and writes PNGs to ``docs/screenshots/``. Pass ``--url https://...`` to
screenshot a deployed instance instead of a local one.
"""

from __future__ import annotations

import argparse
import contextlib
import shutil
import socket
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_ENTRY = REPO_ROOT / "app" / "streamlit_app.py"
SCREENSHOTS_DIR = REPO_ROOT / "docs" / "screenshots"

# Streamlit auto-discovers pages from app/pages/*.py and routes them at
# /<filename without extension>. The filename's leading "NN_" is dropped and
# underscores become spaces in the sidebar, but the URL keeps the underscores.
PAGES = (
    ("01_playground.png", "/Pitch_Playground", 6.0),
    ("02_magnus_explorer.png", "/Magnus_Explorer", 6.0),
    ("03_fastball_vs_curveball.png", "/Fastball_vs_Curveball", 6.0),
    ("04_active_spin_gyro.png", "/Active_Spin_Gyro", 8.0),  # 11-sample sweep takes a moment
    ("05_drag_environment.png", "/Drag_Environment", 6.0),
)


def _free_port() -> int:
    """Return a free TCP port on localhost."""
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_for(url: str, timeout_s: float = 30.0) -> None:
    """Poll ``url`` until it returns 200 or timeout."""
    import urllib.request

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as resp:
                if resp.status == 200:
                    return
        except Exception:
            pass
        time.sleep(0.5)
    raise TimeoutError(f"Streamlit didn't come up on {url}")


def _start_local_streamlit() -> tuple[subprocess.Popen[bytes], str]:
    """Boot Streamlit headlessly on a free port. Returns (process, base_url)."""
    streamlit_bin = shutil.which("streamlit") or str(REPO_ROOT / ".venv" / "bin" / "streamlit")
    port = _free_port()
    proc = subprocess.Popen(
        [
            streamlit_bin,
            "run",
            str(APP_ENTRY),
            "--server.port",
            str(port),
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    _wait_for(base, timeout_s=45.0)
    # Give Streamlit a beat to compile the app.
    time.sleep(2.0)
    return proc, base


def _capture(playwright_module: object, base_url: str) -> None:
    pw = playwright_module.sync_playwright().start()  # type: ignore[attr-defined]
    try:
        browser = pw.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1440, "height": 900}, device_scale_factor=2
        )
        page = context.new_page()

        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        # Landing page
        page.goto(base_url)
        page.wait_for_timeout(4000)
        landing = SCREENSHOTS_DIR / "00_landing.png"
        page.screenshot(path=str(landing), full_page=True)
        print(f"wrote {landing.relative_to(REPO_ROOT)}")

        for filename, route, wait_ms_after in PAGES:
            url = f"{base_url}{route}"
            print(f"capturing {filename} from {url}")
            page.goto(url)
            page.wait_for_timeout(int(wait_ms_after * 1000))
            out = SCREENSHOTS_DIR / filename
            page.screenshot(path=str(out), full_page=True)
            print(f"wrote {out.relative_to(REPO_ROOT)}")

        browser.close()
    finally:
        pw.stop()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        help="Base URL of a running Streamlit app (e.g. https://pitchphys.streamlit.app). "
        "If omitted, a local Streamlit server is started and torn down.",
    )
    args = parser.parse_args()

    try:
        import playwright.sync_api as playwright_module
    except ModuleNotFoundError:
        print(
            "playwright is not installed. Install with `pip install -e .[dev]` "
            "and then run `playwright install chromium`."
        )
        return 1

    if args.url:
        _capture(playwright_module, args.url.rstrip("/"))
        return 0

    proc, base = _start_local_streamlit()
    try:
        _capture(playwright_module, base)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
