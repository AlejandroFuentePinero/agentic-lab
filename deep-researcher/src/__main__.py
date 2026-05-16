"""Entry point: `python -m src` from the agent directory.

Two modes, chosen by whether a query is passed on the command line:

- No argument → launches the Gradio UI in the browser (interactive mode).
- A query string → runs the same pipeline headless and streams status + the
  final report to stdout. Useful for quick iteration without the browser.

Both modes route through the clarifier by default. The decision *whether* to
ask is the clarifier's call — the UI never asks the user "would you like
clarification?"; it just runs the clarifier and only surfaces a question
step if the clarifier raises one. CLI prompts stdin for each question;
Gradio renders one textbox per question. Both expose a clean bypass for
batch / scripted use where stdin is not interactive (`--no-clarify` on the
CLI, a checkbox in the UI).
"""

from __future__ import annotations

import argparse
import asyncio

import gradio as gr

from .clarification import Clarification
from .config import load_settings
from .orchestrator import ResearchManager


# Clarifier is capped at 3 questions in its instructions. We pre-allocate
# exactly that many answer textboxes and show/hide them as needed — Gradio's
# component model dislikes dynamic component counts, so this is the cleanest
# way to render N labelled answer fields where N varies per query.
_MAX_QUESTIONS = 3


def _build_ui(manager: ResearchManager) -> gr.Blocks:
    async def step(
        query: str,
        skip: bool,
        a0: str,
        a1: str,
        a2: str,
        pending_questions: list[str],
    ):
        """Single button handler. State machine driven by `pending_questions`.

        - Empty pending_questions: this is a fresh click. Run the clarifier
          (unless skipped). If it raises questions, expose textboxes and stop
          — waiting for the user to answer and click the button again. If it
          raises none, run the pipeline directly.
        - Non-empty pending_questions: this is a follow-up click. Pair the
          answers back to the questions and run the pipeline.
        """
        answers = [a0, a1, a2]

        def reset_ui_updates():
            return (
                *[gr.update(visible=False, value="", label="") for _ in range(_MAX_QUESTIONS)],
                [],  # clear pending_questions state
                gr.update(value="Research"),  # restore button label
            )

        # ── Follow-up click: clarifications are already gathered, run the pipeline.
        if pending_questions:
            clarifications = [
                Clarification(question=q, answer=a.strip())
                for q, a in zip(pending_questions, answers)
                if a and a.strip()
            ] or None
            async for chunk in manager.run(query, clarifications=clarifications):
                yield (chunk, *reset_ui_updates())
            return

        # ── Fresh click: validate, optionally clarify, then run.
        if not query or not query.strip():
            yield ("_Type a query first._", *reset_ui_updates())
            return

        if not skip:
            # Surface that the clarifier is running so the user knows *something*
            # is happening between their click and either the question step or
            # the planner kicking off.
            yield ("Asking the clarifier whether the query needs sharpening…", *reset_ui_updates())
            questions = await manager.clarify(query)
            if questions:
                box_updates = []
                for i in range(_MAX_QUESTIONS):
                    if i < len(questions):
                        box_updates.append(
                            gr.update(visible=True, label=questions[i], value="")
                        )
                    else:
                        box_updates.append(gr.update(visible=False, value="", label=""))
                yield (
                    "_The clarifier raised the questions below. Answer them and click "
                    "**Continue with research**._",
                    *box_updates,
                    questions,
                    gr.update(value="Continue with research"),
                )
                return

        # Skipped, or clarifier had no questions → straight to the pipeline.
        async for chunk in manager.run(query):
            yield (chunk, *reset_ui_updates())

    with gr.Blocks(theme=gr.themes.Default(primary_hue="sky"), title="Deep Researcher") as ui:
        gr.Markdown("# Deep Researcher\nResearch a topic, get a sourced markdown report.")
        query_box = gr.Textbox(label="What topic would you like to research?")
        skip_clarify = gr.Checkbox(
            label="Skip clarification (run straight to planning)",
            value=False,
        )
        run_button = gr.Button("Research", variant="primary")
        answer_boxes = [
            gr.Textbox(label="", visible=False, lines=1) for _ in range(_MAX_QUESTIONS)
        ]
        pending_questions = gr.State([])
        output = gr.Markdown(label="Status / Report")

        outputs = [output, *answer_boxes, pending_questions, run_button]
        inputs = [query_box, skip_clarify, *answer_boxes, pending_questions]
        run_button.click(fn=step, inputs=inputs, outputs=outputs)
        query_box.submit(fn=step, inputs=inputs, outputs=outputs)

    return ui


async def _run_cli(manager: ResearchManager, query: str, no_clarify: bool) -> None:
    clarifications: list[Clarification] | None = None
    if not no_clarify:
        questions = await manager.clarify(query)
        if questions:
            print("The clarifier has a few questions to sharpen the search plan:")
            collected: list[Clarification] = []
            for q in questions:
                print(f"\n  Q: {q}")
                try:
                    answer = input("  A: ").strip()
                except EOFError:
                    answer = ""
                if answer:
                    collected.append(Clarification(question=q, answer=answer))
            clarifications = collected or None
            print()
    async for chunk in manager.run(query, clarifications=clarifications):
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
    parser.add_argument(
        "--no-clarify",
        action="store_true",
        help="Skip the clarification step and go straight to planning. Useful for "
        "batch / scripted runs where stdin is not interactive.",
    )
    args = parser.parse_args()

    manager = ResearchManager(load_settings())
    if args.query is None:
        _build_ui(manager).launch(inbrowser=True)
    else:
        asyncio.run(_run_cli(manager, args.query, no_clarify=args.no_clarify))


if __name__ == "__main__":
    main()
