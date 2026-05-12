"""Gathering phase: plan a set of web searches and execute them.

Two agents live here. Both are utility-grade — small structured output,
short summaries — so they share the same model.
"""

from __future__ import annotations

from agents import Agent, ModelSettings, WebSearchTool
from pydantic import BaseModel, Field

from .config import Settings


class WebSearchItem(BaseModel):
    reason: str = Field(description="Why this search helps answer the query.")
    query: str = Field(description="The exact search term to use.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="The list of web searches to perform to best answer the query."
    )


def build_planner(settings: Settings) -> Agent:
    instructions = (
        f"You are a research planner. Given a user query, produce exactly "
        f"{settings.num_searches} distinct web searches that together best "
        f"answer the query. For each search, give a short reason and the exact "
        f"query term to use."
    )
    return Agent(
        name="Planner",
        instructions=instructions,
        model=settings.model,
        output_type=WebSearchPlan,
    )


def build_search_agent(settings: Settings) -> Agent:
    instructions = (
        "You are a research assistant. Given a search term, use the web search "
        "tool, then summarise the results in 2–3 short paragraphs (under 300 "
        "words). Capture the essentials and skip the fluff. The summary will be "
        "consumed by a writer agent, not a human, so brevity beats grammar.\n\n"
        "After the summary, you MUST end your output with a line of the form:\n"
        "  Sources: <url1> | <url2> | <url3>\n"
        "listing the exact URLs of the results you read. The writer agent will "
        "be required to cite these URLs in the final report — if you omit them, "
        "the writer cannot ground its claims and the report fails review."
    )
    return Agent(
        name="Search Agent",
        instructions=instructions,
        tools=[WebSearchTool(search_context_size="low")],
        model=settings.model,
        model_settings=ModelSettings(tool_choice="required"),
    )
