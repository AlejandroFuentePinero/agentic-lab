# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`agentic-lab` is a lab for small/medium agentic AI projects. Each agent lives in its own subdirectory at the repo root (first one: `sdr-agent/`, currently empty). The root `pyproject.toml` holds shared dependencies; there is no per-agent `pyproject.toml` yet, and no workspace configured. If a second agent is added with materially different deps, revisit whether to split into `[tool.uv.workspace]` members.

## Toolchain

- Python `>=3.12`, dependency-managed with **uv** (`uv.lock` committed — do not regenerate with pip/poetry).
- Runtime deps of note: `anthropic`, `openai`, `litellm` (multi-provider LLM routing), `chromadb` (vector store), `gradio` (UI), `huggingface-hub`, `pydantic`, `tenacity` (retries), `python-dotenv`.
- Dev deps: `pytest`, `pytest-json-report`, `pypdf`.
- Secrets live in `.env` at the repo root (gitignored). Load via `python-dotenv`.

## Commands

```bash
uv sync                                       # install/refresh deps from uv.lock
uv add <pkg>                                  # add a runtime dep
uv add --group dev <pkg>                      # add a dev dep
uv run python -m <module>                     # run a module in the project env
uv run pytest                                 # full test suite
uv run pytest path/to/test_x.py::test_name    # single test
```

## Conventions

- New agents go in their own top-level directory (`<agent-name>/`), matching `sdr-agent/`.
- Don't commit anything from `.venv/`, `.env*` (except `.env.example` if added), or Chroma persistence dirs (`chroma/`, `.chroma/`) — already in `.gitignore`.
