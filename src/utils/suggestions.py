"""Utility functions for generating suggested follow-up questions."""

import re
from typing import List


def generate_suggested_followups(
    user_message: str,
    assistant_response: str,
    conversation_context: List[str] | None = None,
    max_suggestions: int = 3
) -> List[str]:
    """
    Generate relevant follow-up questions based on the conversation.

    This is a simple rule-based approach that can be enhanced with AI later.

    Args:
        user_message: The last user message
        assistant_response: The last assistant response
        conversation_context: Optional list of previous messages for context
        max_suggestions: Maximum number of suggestions to return

    Returns:
        List of suggested follow-up questions
    """

    suggestions = []

    # Extract key topics from the conversation
    topics = extract_topics(user_message + " " + assistant_response)

    # Generate suggestions based on response patterns
    response_lower = assistant_response.lower()

    # Pattern 1: If assistant explained something, suggest asking for more details
    if any(word in response_lower for word in ["explain", "explained", "how to", "steps", "process"]):
        if "code" in response_lower or "function" in response_lower:
            suggestions.append("Can you show me a complete working example?")
        elif "tutorial" in response_lower or "guide" in response_lower:
            suggestions.append("What are the common pitfalls I should avoid?")
        else:
            suggestions.append("Can you explain this in more detail?")

    # Pattern 2: If assistant provided code, suggest improvements or alternatives
    if "```" in assistant_response or "code" in response_lower:
        if "python" in assistant_response.lower():
            suggestions.append("How can I optimize this code for better performance?")
            suggestions.append("Can you add error handling to this code?")
        elif "javascript" in assistant_response.lower() or "typescript" in assistant_response.lower():
            suggestions.append("How can I make this more production-ready?")
        suggestions.append("Can you show me an alternative approach?")

    # Pattern 3: If assistant discussed concepts, suggest practical applications
    if any(word in response_lower for word in ["concept", "theory", "principle", "pattern"]):
        suggestions.append("Can you show me a real-world use case?")

    # Pattern 4: If assistant listed items, suggest asking for more
    if any(word in response_lower for word in ["here are", "following", "options", "ways"]):
        suggestions.append("What do you recommend as the best approach?")
        suggestions.append("Can you compare these options in detail?")

    # Pattern 5: If assistant solved a problem, suggest edge cases
    if any(word in response_lower for word in ["solve", "solution", "fix", "resolved"]):
        suggestions.append("What edge cases should I consider?")
        suggestions.append("How can I test this solution?")

    # Pattern 6: If assistant mentioned tools/libraries, suggest learning resources
    if any(word in response_lower for word in ["library", "framework", "tool", "package"]):
        suggestions.append("Where can I learn more about this?")
        suggestions.append("Are there any good alternatives?")

    # Pattern 7: Context-aware suggestions based on user's original question
    user_lower = user_message.lower()

    # If user asked "how", suggest asking "why"
    if user_lower.startswith("how"):
        suggestions.append("Why does this approach work?")

    # If user asked "what", suggest asking "how"
    if user_lower.startswith("what"):
        suggestions.append("How do I implement this?")

    # If user asked about errors, suggest debugging
    if any(word in user_lower for word in ["error", "bug", "issue", "problem", "not working"]):
        suggestions.append("How can I debug this step by step?")
        suggestions.append("What are the common causes for this?")

    # If user asked for best practices, suggest examples
    if any(word in user_lower for word in ["best practice", "recommend", "should"]):
        suggestions.append("Can you show me a concrete example?")

    # Remove duplicates while preserving order
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            unique_suggestions.append(s)

    # Limit to max_suggestions
    return unique_suggestions[:max_suggestions]


def extract_topics(text: str) -> List[str]:
    """
    Extract key topics from text using simple keyword extraction.

    Args:
        text: The text to extract topics from

    Returns:
        List of topic keywords
    """
    # Common technical terms to look for
    technical_terms = [
        "api", "database", "frontend", "backend", "algorithm", "function",
        "class", "variable", "array", "object", "string", "number",
        "python", "javascript", "typescript", "java", "rust", "go",
        "react", "vue", "angular", "node", "express", "fastapi",
        "sql", "nosql", "mongodb", "postgresql", "mysql",
        "docker", "kubernetes", "aws", "azure", "gcp",
        "machine learning", "ai", "deep learning", "neural network",
        "authentication", "authorization", "security", "encryption",
        "testing", "debugging", "deployment", "cicd"
    ]

    text_lower = text.lower()
    found_topics = []

    for term in technical_terms:
        if term in text_lower:
            found_topics.append(term)

    return found_topics


def generate_contextual_suggestions(
    user_message: str,
    assistant_response: str,
    previous_messages: List[str] | None = None
) -> List[str]:
    """
    Generate contextually relevant follow-up suggestions considering the conversation history.

    Args:
        user_message: The last user message
        assistant_response: The last assistant response
        previous_messages: List of previous message contents for context

    Returns:
        List of contextual follow-up suggestions
    """
    suggestions = generate_suggested_followups(user_message, assistant_response)

    # Add conversation-specific suggestions if there's history
    if previous_messages and len(previous_messages) > 2:
        # If the conversation has been going on for a while
        suggestions.append("Can you summarize what we've discussed so far?")
        suggestions.append("What should I focus on next?")

    return suggestions
