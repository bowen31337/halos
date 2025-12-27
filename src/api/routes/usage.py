"""Usage tracking endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/daily")
async def get_daily_usage() -> dict:
    """Get daily usage statistics."""
    return {
        "date": "2025-01-01",
        "total_tokens": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "conversations": 0,
        "messages": 0,
        "estimated_cost": 0.0,
    }


@router.get("/monthly")
async def get_monthly_usage() -> dict:
    """Get monthly usage statistics."""
    return {
        "month": "2025-01",
        "total_tokens": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "conversations": 0,
        "messages": 0,
        "estimated_cost": 0.0,
        "daily_breakdown": [],
    }


@router.get("/by-model")
async def get_usage_by_model() -> list[dict]:
    """Get usage breakdown by model."""
    return [
        {
            "model": "claude-sonnet-4-5-20250929",
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "messages": 0,
            "estimated_cost": 0.0,
        }
    ]


@router.get("/cache-stats")
async def get_cache_stats() -> dict:
    """Get prompt caching statistics."""
    return {
        "cache_hits": 0,
        "cache_misses": 0,
        "hit_rate": 0.0,
        "tokens_saved": 0,
        "cost_saved": 0.0,
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation_usage(conversation_id: str) -> dict:
    """Get usage for a specific conversation."""
    return {
        "conversation_id": conversation_id,
        "total_tokens": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "messages": 0,
        "estimated_cost": 0.0,
    }


@router.get("/export")
async def export_usage() -> dict:
    """Export usage data."""
    return {
        "format": "json",
        "data": {
            "daily": [],
            "monthly": [],
            "by_model": [],
        },
    }
