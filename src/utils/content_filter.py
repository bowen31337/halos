"""Content filtering utilities for AI responses."""

from typing import Optional
from src.api.routes.settings import user_settings


def get_content_filter_instructions() -> str:
    """
    Generate content filtering instructions based on user settings.

    Returns instructions to prepend to system messages based on filter level and categories.
    """
    filter_level = user_settings.get("content_filter_level", "low")
    filter_categories = user_settings.get("content_filter_categories", [])

    # If filtering is off, return empty string
    if filter_level == "off" or not filter_categories:
        return ""

    # Base instruction based on level
    level_instructions = {
        "low": "Apply basic content filtering. Avoid generating explicit or highly inappropriate content.",
        "medium": "Apply standard content filtering. Avoid generating content that is violent, hateful, sexually explicit, promotes self-harm, or describes illegal activities in detail.",
        "high": "Apply strict content filtering. Carefully avoid any content that could be considered violent, hateful, sexually explicit, harmful, or illegal. Err on the side of caution and refuse requests that may violate these guidelines.",
    }

    base_instruction = level_instructions.get(filter_level, "")

    # Category-specific instructions
    category_instructions = []

    if "violence" in filter_categories:
        category_instructions.append("avoid graphic violence or detailed descriptions of physical harm")

    if "hate" in filter_categories:
        category_instructions.append("avoid hate speech, discriminatory language, or content that promotes hatred against groups")

    if "sexual" in filter_categories:
        category_instructions.append("avoid sexually explicit content or descriptions of sexual acts")

    if "self-harm" in filter_categories:
        category_instructions.append("avoid content that promotes or provides instructions for self-harm or suicide")

    if "illegal" in filter_categories:
        category_instructions.append("avoid detailed instructions or encouragement for illegal activities")

    # Combine instructions
    if not base_instruction and not category_instructions:
        return ""

    filter_instruction = f"[CONTENT FILTERING: {filter_level.upper()} LEVEL]\n"

    if base_instruction:
        filter_instruction += base_instruction + "\n"

    if category_instructions:
        filter_instruction += "Specifically: " + ", ".join(category_instructions) + "."

    filter_instruction += " [/CONTENT FILTERING]\n\n"

    return filter_instruction


def apply_content_filtering_to_message(message: str) -> str:
    """
    Apply content filtering to a user message.

    This adds filtering instructions to guide the AI's response generation.

    Args:
        message: The original user message

    Returns:
        Message with content filtering instructions prepended
    """
    filter_instruction = get_content_filter_instructions()

    if not filter_instruction:
        return message

    return f"{filter_instruction}{message}"


def should_filter_response(response_content: str) -> tuple[bool, Optional[str]]:
    """
    Check if a response should be filtered based on content filter settings.

    This is a basic implementation that looks for obvious policy violations.
    In production, this would use more sophisticated content moderation.

    Args:
        response_content: The AI's response to check

    Returns:
        Tuple of (should_filter, filter_reason)
    """
    filter_level = user_settings.get("content_filter_level", "low")
    filter_categories = user_settings.get("content_filter_categories", [])

    if filter_level == "off" or not filter_categories:
        return False, None

    # Lowercase the content for checking
    content_lower = response_content.lower()

    # Basic keyword checking (in production, use proper content moderation API)
    # This is just a placeholder to demonstrate the concept

    filter_reasons = []

    if "violence" in filter_categories:
        violence_keywords = ["kill everyone", "mass murder", "torture", "graphic violence"]
        if any(keyword in content_lower for keyword in violence_keywords):
            filter_reasons.append("violence")

    if "hate" in filter_categories:
        hate_keywords = ["racial slur", "hate group", "inferior race"]
        if any(keyword in content_lower for keyword in hate_keywords):
            filter_reasons.append("hate speech")

    if "sexual" in filter_categories:
        sexual_keywords = ["explicit sexual act", "pornographic"]  # Simplified for example
        if any(keyword in content_lower for keyword in sexual_keywords):
            filter_reasons.append("sexual content")

    if "self-harm" in filter_categories:
        self_harm_keywords = ["how to commit suicide", "kill yourself", "self-harm methods"]
        if any(keyword in content_lower for keyword in self_harm_keywords):
            filter_reasons.append("self-harm content")

    if "illegal" in filter_categories:
        illegal_keywords = ["how to make a bomb", "drug manufacturing"]  # Simplified
        if any(keyword in content_lower for keyword in illegal_keywords):
            filter_reasons.append("illegal content")

    if filter_reasons:
        return True, f"Content filtered for: {', '.join(filter_reasons)}"

    return False, None
