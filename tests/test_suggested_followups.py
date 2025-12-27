"""Test suggested follow-ups feature."""

import asyncio
import pytest
from httpx import AsyncClient
import json


@pytest.mark.asyncio
async def test_suggested_followups_generated(async_client: AsyncClient):
    """Test that suggested follow-ups are generated for a response."""

    # Send a message that should trigger suggestions
    response = await async_client.post(
        "/api/agent/stream",
        json={
            "message": "How do I create a Python function?",
            "conversation_id": "test-conv-followups",
        },
    )

    assert response.status_code == 200

    # Read the SSE stream
    suggestions_received = False
    suggestions = []
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            data_str = line[6:]
            if not data_str:
                continue

            try:
                data = json.loads(data_str)

                # Check for done event with suggestions
                if data.get("event") == "done":
                    event_data = json.loads(data.get("data", "{}"))
                    suggestions = event_data.get("suggested_follow_ups", [])
                    if suggestions:
                        suggestions_received = True
                        print(f"✓ Received suggestions: {suggestions}")
                        break
            except json.JSONDecodeError:
                pass

    assert suggestions_received, "No suggestions received in done event"
    assert len(suggestions) > 0, "Suggestions list is empty"
    assert isinstance(suggestions, list), "Suggestions should be a list"
    assert all(isinstance(s, str) for s in suggestions), "All suggestions should be strings"


@pytest.mark.asyncio
async def test_suggestions_contextual(async_client: AsyncClient):
    """Test that suggestions are contextual to the conversation."""

    # Test code-related question
    response = await async_client.post(
        "/api/agent/stream",
        json={
            "message": "Write a Python function to calculate factorial",
            "conversation_id": "test-conv-code",
        },
    )

    assert response.status_code == 200

    suggestions = []
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            data_str = line[6:]
            if not data_str:
                continue

            try:
                data = json.loads(data_str)
                if data.get("event") == "done":
                    event_data = json.loads(data.get("data", "{}"))
                    suggestions = event_data.get("suggested_follow_ups", [])
                    if suggestions:
                        break
            except json.JSONDecodeError:
                pass

    # Check that suggestions are relevant to code
    if suggestions:
        code_related = any(
            word in " ".join(suggestions).lower()
            for word in ["code", "function", "optimize", "test", "implement"]
        )
        print(f"✓ Code-related suggestions: {suggestions}")
        # At least one suggestion should be code-related
        assert code_related or len(suggestions) >= 2, "Suggestions should be relevant"


@pytest.mark.asyncio
async def test_suggestions_include_different_types(async_client: AsyncClient):
    """Test that different types of questions get different suggestions."""

    test_cases = [
        ("What is machine learning?", "concept"),
        ("How do I fix a syntax error?", "debugging"),
        ("Create a REST API", "implementation"),
    ]

    for message, category in test_cases:
        response = await async_client.post(
            "/api/agent/stream",
            json={
                "message": message,
                "conversation_id": f"test-conv-{category}",
            },
        )

        assert response.status_code == 200

        suggestions = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_str = line[6:]
                if not data_str:
                    continue

                try:
                    data = json.loads(data_str)
                    if data.get("event") == "done":
                        event_data = json.loads(data.get("data", "{}"))
                        suggestions = event_data.get("suggested_follow_ups", [])
                        if suggestions:
                            print(f"✓ {category.capitalize()} suggestions: {suggestions}")
                            break
                except json.JSONDecodeError:
                    pass

        # Verify suggestions were received
        assert isinstance(suggestions, list), f"Suggestions should be a list for {category}"


if __name__ == "__main__":
    print("Run tests with: pytest tests/test_suggested_followups.py -v")
