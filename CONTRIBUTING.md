# Contributing

The full contributor guide lives on the docs site:

**→ https://jman4162.github.io/pitchphys/contributing/**

## TL;DR

```bash
git clone https://github.com/jman4162/pitchphys
cd pitchphys
python -m venv .venv
.venv/bin/pip install -e ".[dev,viz,app,docs]"

# Before opening a PR
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy src
```

Bug reports, feature requests, and pull requests are welcome on
[GitHub Issues](https://github.com/jman4162/pitchphys/issues).
