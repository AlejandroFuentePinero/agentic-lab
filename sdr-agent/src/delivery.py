"""Email delivery: format the chosen draft and send it via SendGrid.

Exposes a single `build_email_manager(settings)` that returns the Email Manager
agent. Internally the manager owns three tools:

- `subject_writer`  — sub-agent that generates a subject line
- `html_converter`  — sub-agent that converts the body to HTML
- `send_html_email` — function tool that hands the result to SendGrid

The Sales Manager hands off to this agent once it has picked a winning draft.
"""

from __future__ import annotations

import sendgrid
from agents import Agent, function_tool
from sendgrid.helpers.mail import Content, Email, Mail, To

from .config import Settings


_MANAGER_INSTRUCTIONS = (
    "You are an email formatter and sender. You receive the body of an email to be sent. "
    "You first use the subject_writer tool to write a subject for the email, then use the "
    "html_converter tool to convert the body to HTML. Finally, you use the send_html_email "
    "tool to send the email with the subject and HTML body."
)

_SUBJECT_INSTRUCTIONS = (
    "You can write a subject for a cold sales email. You are given a message and you need "
    "to write a subject for an email that is likely to get a response."
)

_HTML_INSTRUCTIONS = (
    "You can convert a text email body to an HTML email body. You are given a text email "
    "body which might have some markdown and you need to convert it to an HTML email body "
    "with simple, clear, compelling layout and design."
)


def build_email_manager(settings: Settings) -> Agent:
    subject_writer = Agent(
        name="Email subject writer",
        instructions=_SUBJECT_INSTRUCTIONS,
        model=settings.utility_model,
    )
    html_converter = Agent(
        name="HTML email body converter",
        instructions=_HTML_INSTRUCTIONS,
        model=settings.utility_model,
    )

    tools = [
        subject_writer.as_tool(
            tool_name="subject_writer",
            tool_description="Write a subject for a cold sales email",
        ),
        html_converter.as_tool(
            tool_name="html_converter",
            tool_description="Convert a text email body to an HTML email body",
        ),
        _build_send_tool(settings),
    ]

    return Agent(
        name="Email Manager",
        instructions=_MANAGER_INSTRUCTIONS,
        tools=tools,
        model=settings.utility_model,
        handoff_description="Convert an email to HTML and send it",
    )


def _build_send_tool(settings: Settings):
    @function_tool
    def send_html_email(subject: str, html_body: str) -> dict[str, str]:
        """Send an HTML email with the given subject and body to the configured recipient."""
        client = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
        mail = Mail(
            Email(settings.from_email),
            To(settings.to_email),
            subject,
            Content("text/html", html_body),
        ).get()
        response = client.client.mail.send.post(request_body=mail)
        return {"status": "success", "code": str(response.status_code)}

    return send_html_email
