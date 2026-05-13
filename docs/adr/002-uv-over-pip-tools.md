# ADR 002 — uv over pip-tools / Poetry

Date: 2026-05-13
Status: Accepted

## Context

Starting fresh meant choosing a dependency manager without legacy constraints. The primary requirements were:

1. Reproducible installs (lockfile in the repo)
2. Fast — CI and local setup should not be the slowest part of the workflow
3. Reliable resolution — no silent dependency conflicts

Options considered:

- **pip + requirements.txt**: No lockfile by default. Manual conflict resolution. Not acceptable.
- **pip-tools**: `pip-compile` generates a lockfile. Mature, simple, but slow on resolution and has no built-in virtualenv management.
- **Poetry**: Good lockfile, built-in venv management, mature ecosystem. Slow on large dependency trees. `poetry.lock` and `pyproject.toml` formats diverge slightly from PEP standards.
- **uv**: Written in Rust. Claims 10–100x faster installs than pip. Uses standard `pyproject.toml` + `uv.lock`. Handles virtualenvs, Python version management, and script running (`uv run`). Relatively new (2024) but stabilizing fast.

## Decision

Use `uv` with a committed `uv.lock` file. All Python invocations in documentation, CI, and scripts use `uv run` rather than activating a virtualenv manually.

## Consequences

**Positive:**
- Install time: `uv sync` on a cold cache takes a few seconds vs. 60+ seconds with pip. This compounds in CI.
- Single lockfile (`uv.lock`) captures all transitive dependencies with exact versions and hashes.
- `uv run` handles venv activation implicitly — no `source .venv/bin/activate` in scripts or docs.
- Standard `pyproject.toml` format. If we ever switch away from uv, the `[project]` and `[dependency-groups]` sections are portable.

**Negative:**
- uv is relatively young. Some rough edges remain — for example, the `uv.lock` format is not human-readable in the way `requirements.txt` is, and `uv tool` / `uvx` patterns are still evolving.
- Ecosystem tooling assumes pip. Some CI templates, Docker base images, and deployment platforms (including Railway's Nixpacks) need explicit `uv` installation steps.
- If Astral (the company behind uv) changes direction, migration back to pip-tools or Poetry is necessary. The lockfile format is not portable, though the `pyproject.toml` is.
- `uv run` can mask virtualenv state issues during debugging. When something is broken at the environment level, it's worth running `uv sync --reinstall` before investigating further.

Net: the speed and ergonomic gains are significant enough to accept the ecosystem immaturity at the current project scale.
