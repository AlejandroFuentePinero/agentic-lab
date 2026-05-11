"""SDR agent: multi-agent cold-email outreach demo (openai-agents SDK)."""

from .config import Settings, load_settings
from .orchestrator import build_sales_manager

__all__ = ["Settings", "load_settings", "build_sales_manager"]
