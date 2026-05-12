"""Entry point: `python -m src` from the agent directory.

Two modes, chosen by whether a query is passed on the command line:

- No argument → launches the Gradio UI in the browser (interactive mode).
- A query string → runs the same pipeline headless and streams status + the
  final report to stdout. Useful for quick iteration without the browser.
"""

from __future__ import annotations

import argparse
import asyncio

import gradio as gr

from .config import load_settings
from .orchestrator import ResearchManager


def _build_ui(manager: ResearchManager) -> gr.Blocks:
    async def run(query: str):
        async for chunk in manager.run(query):
            yield chunk

    with gr.Blocks(theme=gr.themes.Default(primary_hue="sky"), title="Deep Researcher") as ui:
        gr.Markdown("# Deep Researcher\nResearch a topic, get a sourced markdown report.")
        query_box = gr.Textbox(label="What topic would you like to research?")
        run_button = gr.Button("Research", variant="primary")
        output = gr.Markdown(label="Report")

        run_button.click(fn=run, inputs=query_box, outputs=output)
        query_box.submit(fn=run, inputs=query_box, outputs=output)

    return ui


async def _run_cli(manager: ResearchManager, query: str) -> None:
    async for chunk in manager.run(query):
        print(chunk, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="deep-researcher",
        description="Multi-agent deep research. Run with a query for CLI mode, or "
        "without arguments to launch the Gradio UI.",
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="If given, runs headless and streams output to stdout. If omitted, launches Gradio.",
    )
    args = parser.parse_args()

    manager = ResearchManager(load_settings())
    if args.query is None:
        _build_ui(manager).launch(inbrowser=True)
    else:
        asyncio.run(_run_cli(manager, args.query))


if __name__ == "__main__":
    main()
