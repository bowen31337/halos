"""Utility functions for the application."""

import uuid
from datetime import datetime


def generate_thread_id() -> str:
    """
    Generate a unique thread ID for LangGraph.

    Returns:
        str: A unique thread ID
    """
    return f"thread_{uuid.uuid4().hex[:16]}"


def get_current_timestamp() -> str:
    """
    Get current timestamp in ISO format.

    Returns:
        str: Current timestamp
    """
    return datetime.utcnow().isoformat()