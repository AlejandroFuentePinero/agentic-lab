# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`agentic-lab` is a lab for small/medium agentic AI projects. Each agent lives in its own subdirectory at the repo root and runs in isolation. The root `pyproject.toml` holds shared dependencies for the whole lab; there is no per-agent `pyproject.toml` yet, and no uv workspace configured. If a future agent has materially different deps (and especially conflicting versions), revisit whether to split into `[tool.uv.workspace]` members.

Each agent directory owns a `README.md` — read it before working in that directory. The agent's runnable Python package lives at `<agent>/src/` and is invoked with `python -m src` from inside the agent directory.

### Agents

- `sdr-agent/` — multi-agent cold-outreach SDR. Implements lab 2 + lab 3 patterns (agent-as-tool, handoffs, function tools, input + output guardrails, structured outputs) on Sonnet + gpt-4o-mini, delivering via SendGrid. See `sdr-agent/README.md`.

### Reference material (not runtime)

- `example-code/sdr-example/` — the original Jupyter notebooks the agents are ported from. Gitignored, kept locally as a reference for what each pattern looks like in the lab format.

## Toolchain

- Python `>=3.12`, dependency-managed with **uv** (`uv.lock` committed — do not regenerate with pip/poetry).
- Runtime deps of note: `openai-agents` (the SDK driving every agent), `anthropic`, `openai`, `litellm` (multi-provider routing for the agents SDK), `sendgrid`, `chromadb`, `gradio`, `pydantic`, `tenacity`, `python-dotenv`.
- Dev deps: `pytest`, `pytest-json-report`, `pypdf`.
- Secrets live in `.env` at the repo root (gitignored). Each agent's README lists which keys it needs.

## Commands

```bash
uv sync                                       # install/refresh deps from uv.lock
uv add <pkg>                                  # add a runtime dep
uv add --group dev <pkg>                      # add a dev dep
uv run pytest                                 # full test suite (config in pyproject [tool.pytest.ini_options])
uv run pytest path/to/test_x.py::test_name    # single test

# Run an agent (the pattern is: cd into its dir, then `python -m src`):
cd <agent>/ && uv run python -m src           # default behaviour
cd <agent>/ && uv run python -m src "<arg>"   # most agents accept a prompt arg
```

`uv run` from inside an agent subdirectory still picks up the repo-root project (uv walks upward to find `pyproject.toml`/`uv.lock`), so the same shared venv is used everywhere.

## Conventions

- New agents go in their own top-level directory (`<agent-name>/`), with an `src/` package inside and a `README.md` at the agent root.
- Inside each `src/` package, prefer a **few deep modules** (one per capability) over many shallow single-purpose files. Hide internal agents/tools/guardrails behind a single `build_*` factory and re-export only what callers actually need from `__init__.py`.
- Don't commit anything from `.venv/`, `.env*` (except `.env.example` if added), or Chroma persistence dirs (`chroma/`, `.chroma/`) — already in `.gitignore`.
