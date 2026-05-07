"""Tests for the pitchphys-app console-script launcher."""

from __future__ import annotations

import sys
from unittest import mock

import pytest

from pitchphys import app_launcher


def test_resolve_app_path_finds_source_checkout() -> None:
    path = app_launcher._resolve_app_path()
    assert path.endswith("streamlit_app.py")
    assert "app" in path or "_app" in path


def test_main_invokes_streamlit_cli_with_run_argv() -> None:
    """main() should set sys.argv = ['streamlit', 'run', <path>] and call cli.main."""
    fake_cli = mock.Mock()
    fake_cli.main = mock.Mock(return_value=0)
    fake_module = mock.Mock(cli=fake_cli)

    original_argv = list(sys.argv)
    try:
        sys.argv = ["pitchphys-app"]
        with (
            mock.patch.dict(sys.modules, {"streamlit": mock.Mock(), "streamlit.web": fake_module}),
            mock.patch.object(
                app_launcher, "_resolve_app_path", return_value="/fake/streamlit_app.py"
            ),
        ):
            rc = app_launcher.main()
        assert rc == 0
        assert sys.argv[0] == "streamlit"
        assert sys.argv[1] == "run"
        assert sys.argv[2] == "/fake/streamlit_app.py"
        fake_cli.main.assert_called_once()
    finally:
        sys.argv = original_argv


def test_main_passes_extra_cli_args_through() -> None:
    """`pitchphys-app --server.port 9000` should forward to `streamlit run ...`."""
    fake_cli = mock.Mock()
    fake_cli.main = mock.Mock(return_value=0)
    fake_module = mock.Mock(cli=fake_cli)

    original_argv = list(sys.argv)
    try:
        sys.argv = ["pitchphys-app", "--server.port", "9000"]
        with (
            mock.patch.dict(sys.modules, {"streamlit": mock.Mock(), "streamlit.web": fake_module}),
            mock.patch.object(
                app_launcher, "_resolve_app_path", return_value="/fake/streamlit_app.py"
            ),
        ):
            app_launcher.main()
        assert sys.argv[3:] == ["--server.port", "9000"]
    finally:
        sys.argv = original_argv


def test_main_raises_clear_error_without_streamlit() -> None:
    """If streamlit isn't importable, main() exits with code 1 and a hint."""
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("streamlit"):
            raise ModuleNotFoundError(f"No module named {name!r}")
        return real_import(name, *args, **kwargs)

    with mock.patch("builtins.__import__", side_effect=fake_import):
        with pytest.raises(SystemExit) as excinfo:
            app_launcher.main()
        assert excinfo.value.code == 1
