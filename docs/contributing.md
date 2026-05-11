# Contributing

Bug reports, feature requests, and pull requests are welcome on [GitHub](https://github.com/jman4162/pitchphys/issues).

## Quick-start dev setup

```bash
git clone https://github.com/jman4162/pitchphys
cd pitchphys
python -m venv .venv
.venv/bin/pip install -e ".[dev,viz,app,docs]"
```

This installs the package in editable mode plus all the developer extras:

- `dev` — pytest, ruff, mypy, playwright
- `viz` — matplotlib, plotly
- `app` — streamlit (plus everything in `viz`)
- `docs` — mkdocs-material, mkdocstrings, mkdocs-jupyter

## Running the checks

The CI workflow (`.github/workflows/test.yml`) runs all of these on every push to `main` and every PR. Run them locally before you push to avoid the round-trip.

```bash
.venv/bin/pytest -q          # ~190 tests, ~1.5 s
.venv/bin/ruff check .       # lint
.venv/bin/ruff format --check .   # format check
.venv/bin/mypy src           # strict typing
.venv/bin/mkdocs build --strict   # docs build (fails on warnings)
```

If you change `app/*.py`, also smoke-test the Streamlit app:

```bash
.venv/bin/streamlit run app/streamlit_app.py
```

If you change anything under `src/pitchphys/aero/`, you should re-run the Nathan Table I regression specifically:

```bash
.venv/bin/pytest tests/test_aero_nathan.py -v
```

## Code style

- **Type hints required.** `mypy --strict` runs in CI; new code must pass.
- **Ruff is the formatter** (Black-compatible). Run `ruff format .` before committing.
- **Physics symbols are exempt from snake_case.** `Re`, `S`, `Cd`, `Cl`, `F`, `R`, `omega` keep their textbook-standard names; the per-file-ignores in `pyproject.toml` document where.
- **No new dependencies in core.** The engine should stay at `numpy + scipy`. Anything else goes in the right `[project.optional-dependencies]` group.
- **Tests for new physics.** If you add a force or a model, add a regression test that pins it to a known value (analytic limit, paper reference, or empirical anchor).

## Architectural principles

A few load-bearing principles, documented in `CLAUDE.md`:

1. **SI units internally; conversions at the boundary.** Meters, seconds, kg, radians inside the engine. `pitchphys.units` converts mph/rpm/ft/inches at user-facing edges.
2. **Right-handed coordinates.** `x` right, `y` toward plate, `z` up. The spin-axis convention is the single source of truth in `pitchphys.coordinates` — never re-derive it elsewhere.
3. **Composable, toggleable forces.** Gravity, drag, Magnus, and (v0.3) seam-shifted wake are independent callables in `pitchphys.core.forces`. The `forces=[...]` argument to `simulate()` exposes this directly.
4. **Active spin is first-class.** Spin-rate alone doesn't predict movement; the `active_spin_fraction` parameter is required.
5. **Aero models are pluggable.** Any class satisfying the `AeroModel` Protocol can replace the default `LyuAeroModel`.
6. **NumPy + SciPy core.** Numba and JAX are explicitly deferred to a future version.

If your PR conflicts with these principles, flag it in the description and we'll discuss before merging.

## Filing issues

- **Bugs**: include a minimal reproducing snippet, the version you're on (`pip show pitchphys`), and your platform.
- **Physics questions** that aren't bugs are very welcome — open them as Discussions, not Issues.
- **Feature requests**: skim [SPEC_DRAFT.md](https://github.com/jman4162/pitchphys/blob/main/SPEC_DRAFT.md) first to see if it's already on the v0.3+ roadmap.

## License

`pitchphys` is MIT-licensed. Contributions are accepted under the same terms.
