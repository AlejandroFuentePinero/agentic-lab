# Agentic AI Lab

A personal lab for **small and medium agentic AI projects** — multi-agent systems built on top of LLMs, each contained in its own subdirectory and runnable on its own. Every project explores a different set of patterns (orchestration, tool use, guardrails, structured outputs, retrieval, …) on the same shared toolchain (Python 3.12 + `uv` + the OpenAI Agents SDK).

Pick a project, read its README, run it. Nothing in this repo depends on anything else in this repo.

---

## Projects

| Project | What it does | Status |
| --- | --- | --- |
| [`sdr-agent`](./sdr-agent) | Multi-agent **Sales Development Representative**. Drafts three persona-flavoured cold emails in parallel (Anthropic Sonnet), picks the best one, formats it as HTML and ships it through SendGrid — driven by an LLM Sales Manager that uses sub-agents as tools, performs a handoff to a delivery agent, and applies both an input and an output guardrail. | Shipped |
| [`deep-researcher`](./deep-researcher) | Multi-agent **deep research** tool. Plans web searches from a user query, runs them in parallel via OpenAI's hosted `WebSearchTool`, synthesises results into a long-form markdown report, then runs a strict **critic** that grounds every cited URL against the search results — driving up to two bounded revision passes when it finds fabricated or unsupported citations. Reports save locally with a References section listing every URL the writer relied on, and stream live through a Gradio UI (also runnable headless from the CLI). | Shipped |

Each project's README has its own architecture diagram, prerequisite list (which API keys it needs), and run commands. Diagrams use Mermaid and render natively on GitHub.

---

## Toolchain

- **Python 3.12+**, dependency-managed with [`uv`](https://docs.astral.sh/uv/). The lockfile is committed and shared across every project.
- **[`openai-agents`](https://github.com/openai/openai-agents-python)** as the agent runtime. Multi-provider routing via `litellm` (Anthropic + OpenAI today; trivially extendable to Google, Groq, etc.).
- **`pytest`** for tests. Each project has its own pytest config (`pytest.ini` or settings in the root `pyproject.toml`) so the agents' `src/` packages don't clash on import. Run tests from inside each project directory.

A single `pyproject.toml` at the root keeps dependencies aligned across all projects. If a future project ever needs incompatible deps, the plan is to migrate to `[tool.uv.workspace]` members.

---

## Getting started

```bash
git clone <repo-url>
cd agentic-lab
uv sync                           # creates .venv and installs the locked deps
```

Don't have `uv`? Install it with `pip install uv`, or follow the [official guide](https://docs.astral.sh/uv/getting-started/installation/). A pre-exported `requirements.txt` is also provided for environments that can't (or don't want to) use `uv`:

```bash
pip install -r requirements.txt
```

Then pick a project, set the env vars listed in its README, and run it:

```bash
cd sdr-agent
uv run python -m src              # see sdr-agent/README.md for required env vars
```

Run the test suite for each project from its own directory:

```bash
cd sdr-agent       && uv run pytest
cd deep-researcher && uv run pytest
```

Each project has its own `pytest.ini` (or root-level `pyproject.toml` config) so tests pick up the right `src/` package.

---

## Repo layout

```
agentic-lab/
├── README.md              ← you are here
├── CLAUDE.md              ← working notes for future Claude Code sessions
├── pyproject.toml         ← shared deps + pytest config
├── uv.lock                ← canonical lockfile (uv)
├── requirements.txt       ← exported from uv.lock for non-uv users
└── <project>/             ← one directory per project
    ├── README.md          ← project-specific docs — start here when exploring a project
    ├── src/               ← runnable Python package (python -m src)
    └── tests/             ← project tests; run via `uv run pytest` from inside the project directory
```

Conventions inside each project: a `src/` package built as a small number of **deep** modules (one per capability) rather than many shallow files, and a `tests/` folder runnable from the repo root via the shared pytest config. New projects follow the same shape so navigating between them stays predictable.
