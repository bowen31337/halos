"""Content filtering service for moderating AI responses.

This module provides content filtering functionality to check and moderate
user inputs and AI responses based on configurable filter levels and categories.
"""

import re
from typing import List, Dict, Optional, Tuple
from enum import Enum


class FilterLevel(str, Enum):
    """Content filtering severity levels."""
    OFF = "off"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FilterCategory(str, Enum):
    """Content categories that can be filtered."""
    VIOLENCE = "violence"
    HATE = "hate"
    SEXUAL = "sexual"
    SELF_HARM = "self-harm"
    ILLEGAL = "illegal"


class ContentFilterService:
    """Service for filtering and moderating content."""

    # Keyword patterns for each category (simplified - production would use ML models)
    VIOLENCE_KEYWORDS = [
        "kill", "murder", "violence", "torture", "attack", "assault",
        "weapon", "bomb", "explode", "stab", "shoot", "punch", "fight"
    ]

    HATE_KEYWORDS = [
        "hate", "discriminate", "racist", "sexist", "homophobic",
        "slur", "supremacist", "nazi", "terrorist"
    ]

    SEXUAL_KEYWORDS = [
        "porn", "explicit", "nude", "sexual", "nsfw", "erotic"
    ]

    SELF_HARM_KEYWORDS = [
        "suicide", "kill myself", "self-harm", "cutting", "overdose",
        "anorexic", "bulimic", "end my life"
    ]

    ILLEGAL_KEYWORDS = [
        "drug", "steal", "robbery", "fraud", "money laundering",
        "hack", "pirate", "counterfeit"
    ]

    def __init__(self):
        """Initialize the content filter service."""
        self.category_keywords = {
            FilterCategory.VIOLENCE: self.VIOLENCE_KEYWORDS,
            FilterCategory.HATE: self.HATE_KEYWORDS,
            FilterCategory.SEXUAL: self.SEXUAL_KEYWORDS,
            FilterCategory.SELF_HARM: self.SELF_HARM_KEYWORDS,
            FilterCategory.ILLEGAL: self.ILLEGAL_KEYWORDS,
        }

    def check_content(
        self,
        content: str,
        filter_level: FilterLevel = FilterLevel.LOW,
        enabled_categories: List[FilterCategory] = None
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check content against filter rules.

        Args:
            content: The text content to check
            filter_level: Severity level (off, low, medium, high)
            enabled_categories: List of categories to filter (if None, filters all)

        Returns:
            Tuple of (is_allowed, filter_result)
            - is_allowed: True if content passes filters
            - filter_result: Dict with details about any violations
        """
        if filter_level == FilterLevel.OFF:
            return True, {"status": "no_filter", "categories": {}}

        if enabled_categories is None:
            enabled_categories = list(FilterCategory)

        violations = {}
        total_score = 0

        # Check each enabled category
        for category in enabled_categories:
            if category not in self.category_keywords:
                continue

            category_violation = self._check_category(content, category, filter_level)
            if category_violation["detected"]:
                violations[category.value] = category_violation
                total_score += category_violation["score"]

        # Determine if content is blocked based on level and score
        threshold = self._get_threshold_for_level(filter_level)
        is_blocked = total_score >= threshold

        if is_blocked:
            return False, {
                "status": "blocked",
                "reason": "Content violates filter policy",
                "filter_level": filter_level.value,
                "total_score": total_score,
                "threshold": threshold,
                "violations": violations
            }

        return True, {
            "status": "allowed",
            "filter_level": filter_level.value,
            "violations": violations if violations else None
        }

    def _check_category(
        self,
        content: str,
        category: FilterCategory,
        filter_level: FilterLevel
    ) -> Dict[str, any]:
        """Check content for violations in a specific category."""
        keywords = self.category_keywords.get(category, [])
        content_lower = content.lower()

        detected_keywords = []
        for keyword in keywords:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, content_lower):
                detected_keywords.append(keyword)

        # Calculate score based on keyword count and filter level
        base_score = len(detected_keywords)

        # Adjust score based on filter level
        level_multiplier = {
            FilterLevel.LOW: 1.0,
            FilterLevel.MEDIUM: 1.5,
            FilterLevel.HIGH: 2.0
        }.get(filter_level, 1.0)

        final_score = int(base_score * level_multiplier)

        return {
            "detected": final_score > 0,
            "score": final_score,
            "keywords_found": detected_keywords,
            "category": category.value
        }

    def _get_threshold_for_level(self, filter_level: FilterLevel) -> int:
        """Get the blocking threshold for a filter level."""
        thresholds = {
            FilterLevel.LOW: 5,      # Allow some content before blocking
            FilterLevel.MEDIUM: 3,   # More strict
            FilterLevel.HIGH: 1,     # Very strict - block on first detection
            FilterLevel.OFF: 999     # Never block
        }
        return thresholds.get(filter_level, 5)

    def sanitize_response(
        self,
        response: str,
        filter_level: FilterLevel = FilterLevel.LOW,
        enabled_categories: List[FilterCategory] = None
    ) -> Tuple[str, Dict[str, any]]:
        """
        Sanitize an AI response by removing or redacting filtered content.

        Args:
            response: The AI response text
            filter_level: Severity level
            enabled_categories: Categories to filter

        Returns:
            Tuple of (sanitized_text, filter_result)
        """
        if filter_level == FilterLevel.OFF:
            return response, {"status": "no_filter", "modified": False}

        if enabled_categories is None:
            enabled_categories = list(FilterCategory)

        # Check if content needs filtering
        is_allowed, filter_result = self.check_content(
            response, filter_level, enabled_categories
        )

        if is_allowed:
            return response, {**filter_result, "modified": False}

        # Sanitize by redacting violations
        sanitized = response
        modification_count = 0

        for category_id, violation in filter_result.get("violations", {}).items():
            keywords = violation.get("keywords_found", [])
            for keyword in keywords:
                # Replace keyword matches with asterisks
                pattern = r'\b' + re.escape(keyword) + r'\b'
                replacement = '*' * len(keyword)
                sanitized = re.sub(
                    pattern,
                    replacement,
                    sanitized,
                    flags=re.IGNORECASE
                )
                modification_count += 1

        return sanitized, {
            **filter_result,
            "status": "sanitized",
            "modified": True,
            "modifications": modification_count
        }

    def get_filter_settings_summary(
        self,
        filter_level: str,
        enabled_categories: List[str]
    ) -> Dict[str, any]:
        """Get a human-readable summary of filter settings."""
        level_descriptions = {
            "off": "No content filtering enabled",
            "low": "Basic filtering - only obvious violations blocked",
            "medium": "Moderate filtering - most violations blocked",
            "high": "Strict filtering - potential violations also blocked"
        }

        category_labels = {
            "violence": "Violence & Gore",
            "hate": "Hate Speech",
            "sexual": "Sexual Content",
            "self-harm": "Self-Harm",
            "illegal": "Illegal Activities"
        }

        enabled_labels = [
            category_labels.get(cat, cat)
            for cat in enabled_categories
        ]

        return {
            "level": filter_level,
            "level_description": level_descriptions.get(filter_level, ""),
            "enabled_categories": enabled_labels,
            "category_count": len(enabled_labels)
        }


# Global service instance
content_filter_service = ContentFilterService()
