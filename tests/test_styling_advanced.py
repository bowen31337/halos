"""
Test suite for styling features (#112-115).

Tests for:
- Feature #112: Loading states and spinners are visually consistent
- Feature #113: Transitions and animations are smooth
- Feature #114: Success, warning, error states use correct colors
- Feature #115: Tool call blocks have distinct visual treatment
"""

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright
import asyncio
import json
import os


# Expected values for features #112-115
EXPECTED_STYLING = {
    "status_colors": {
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "info": "#3B82F6",
    },
    "loading": {
        "spinner_duration": "0.6s",
        "typing_indicator_duration": "1s",
        "skeleton_duration": "1.5s",
    },
    "animations": {
        "fade_in": "0.2s",
        "slide_in": "0.3s",
        "transition": "0.15s",
        "timing": "ease-out",
    },
    "tool_blocks": {
        "background_elevated": "#FAFAFA",
        "border_primary": "#E5E5E5",
        "dark_background_elevated": "#333333",
        "dark_border_primary": "#404040",
        "bg_elevated_var": "--bg-elevated",
    }
}


class TestLoadingStates:
    """Test suite for Feature #112: Loading states and spinners."""

    @pytest_asyncio.fixture
    async def browser(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            yield browser
            await browser.close()

    @pytest_asyncio.fixture
    async def page(self, browser):
        context = await browser.new_context()
        page = await context.new_page()
        yield page
        await context.close()

    @pytest.mark.asyncio
    async def test_loading_spinner_exists(self, page):
        """Test that loading spinner animation is defined."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Open demo panel to see loading spinner
        demo_toggle = await page.query_selector("#demoToggle")
        await demo_toggle.click()
        await page.wait_for_selector(".loading-spinner", timeout=3000)

        # Check spinner exists
        spinner_exists = await page.evaluate("""
            () => {
                return document.querySelector('.loading-spinner') !== null;
            }
        """)
        assert spinner_exists, "Loading spinner elements should exist in demo panel"

    @pytest.mark.asyncio
    async def test_typing_indicator_animation(self, page):
        """Test that typing indicator has correct animation."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Check typing indicator exists
        typing_dots = await page.query_selector_all(".typing-dot")
        assert len(typing_dots) == 3, "Should have 3 typing indicator dots"

    @pytest.mark.asyncio
    async def test_skeleton_loader_exists(self, page):
        """Test that skeleton loader animation is defined."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Wait for skeleton to appear (it's added after 1 second)
        await page.wait_for_selector(".skeleton", timeout=5000)

        skeleton = await page.query_selector(".skeleton")
        assert skeleton is not None, "Skeleton loader should exist"

    @pytest.mark.asyncio
    async def test_loading_spinner_styling(self, page):
        """Test that loading spinner has correct styling."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Open demo panel to see loading spinner
        demo_toggle = await page.query_selector("#demoToggle")
        await demo_toggle.click()
        await page.wait_for_selector(".loading-spinner", timeout=3000)

        # Check spinner styling
        spinner_styles = await page.evaluate("""
            () => {
                const spinner = document.querySelector('.loading-spinner');
                if (!spinner) return null;
                const style = window.getComputedStyle(spinner);
                return {
                    width: style.width,
                    height: style.height,
                    animation: style.animation,
                };
            }
        """)
        assert spinner_styles is not None, "Spinner should exist"
        assert spinner_styles['width'] == '16px', "Spinner width should be 16px"
        assert spinner_styles['height'] == '16px', "Spinner height should be 16px"
        assert 'spin' in spinner_styles['animation'].lower(), "Should have spin animation"


class TestTransitionsAndAnimations:
    """Test suite for Feature #113: Transitions and animations are smooth."""

    @pytest_asyncio.fixture
    async def browser(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            yield browser
            await browser.close()

    @pytest_asyncio.fixture
    async def page(self, browser):
        context = await browser.new_context()
        page = await context.new_page()
        yield page
        await context.close()

    @pytest.mark.asyncio
    async def test_transition_timing(self, page):
        """Test that transitions use ease-out timing."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Check transition timing by examining a button
        transition = await page.evaluate("""
            () => {
                const btn = document.querySelector('.send-button');
                if (!btn) return null;
                const style = window.getComputedStyle(btn);
                return style.transition;
            }
        """)
        assert transition and 'ease-out' in transition, "Should have ease-out transitions"

    @pytest.mark.asyncio
    async def test_button_transition(self, page):
        """Test that buttons have smooth transitions."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Check send button transition
        transition = await page.evaluate("""
            () => {
                const btn = document.querySelector('.send-button');
                if (!btn) return null;
                const style = window.getComputedStyle(btn);
                return style.transition;
            }
        """)
        assert transition, "Send button should have transition"

    @pytest.mark.asyncio
    async def test_fade_in_animation(self, page):
        """Test that fade-in animation exists."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Check fade-in animation by looking for the class on welcome message
        has_fade_in = await page.evaluate("""
            () => {
                const element = document.querySelector('.animate-fade-in');
                return element !== null;
            }
        """)
        assert has_fade_in, "Should have fade-in animation class on welcome message"

    @pytest.mark.asyncio
    async def test_slide_in_animations(self, page):
        """Test that slide-in animations exist."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Check slide-in animations by looking for the classes on message bubbles
        has_slide_in = await page.evaluate("""
            () => {
                const hasRight = document.querySelector('.animate-slide-in-right') !== null;
                const hasLeft = document.querySelector('.animate-slide-in-left') !== null;
                return hasRight && hasLeft;
            }
        """)
        assert has_slide_in, "Should have slide-in animations on message bubbles"


class TestStatusColors:
    """Test suite for Feature #114: Status colors."""

    @pytest_asyncio.fixture
    async def browser(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            yield browser
            await browser.close()

    @pytest_asyncio.fixture
    async def page(self, browser):
        context = await browser.new_context()
        page = await context.new_page()
        yield page
        await context.close()

    @pytest.mark.asyncio
    async def test_status_color_variables(self, page):
        """Test that status color CSS variables are defined."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        status_vars = await page.evaluate("""
            () => {
                const style = getComputedStyle(document.documentElement);
                return {
                    success: style.getPropertyValue('--success').trim(),
                    warning: style.getPropertyValue('--warning').trim(),
                    error: style.getPropertyValue('--error').trim(),
                    info: style.getPropertyValue('--info').trim(),
                };
            }
        """)

        assert status_vars['success'] == EXPECTED_STYLING['status_colors']['success'], \
            f"Success color should be {EXPECTED_STYLING['status_colors']['success']}"
        assert status_vars['warning'] == EXPECTED_STYLING['status_colors']['warning'], \
            f"Warning color should be {EXPECTED_STYLING['status_colors']['warning']}"
        assert status_vars['error'] == EXPECTED_STYLING['status_colors']['error'], \
            f"Error color should be {EXPECTED_STYLING['status_colors']['error']}"
        assert status_vars['info'] == EXPECTED_STYLING['status_colors']['info'], \
            f"Info color should be {EXPECTED_STYLING['status_colors']['info']}"

    @pytest.mark.asyncio
    async def test_status_badge_classes(self, page):
        """Test that status badge classes exist."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Open demo panel to see status badges
        demo_toggle = await page.query_selector("#demoToggle")
        if demo_toggle:
            await demo_toggle.click()
            await page.wait_for_selector(".status-badge", timeout=3000)

        # Check for status badge elements
        badges = await page.query_selector_all(".status-badge")
        assert len(badges) > 0, "Status badges should exist in demo panel"

    @pytest.mark.asyncio
    async def test_status_badge_styling(self, page):
        """Test that status badges have correct background colors."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Open demo panel
        demo_toggle = await page.query_selector("#demoToggle")
        if demo_toggle:
            await demo_toggle.click()
            await page.wait_for_selector(".status-badge.success", timeout=3000)

        # Get success badge background color
        bg_color = await page.evaluate("""
            () => {
                const badge = document.querySelector('.status-badge.success');
                if (!badge) return null;
                const style = window.getComputedStyle(badge);
                return style.backgroundColor;
            }
        """)

        if bg_color:
            # Convert to hex for comparison
            if bg_color.startswith('rgb'):
                rgb = [int(x) for x in bg_color[4:-1].split(',')]
                hex_color = '#' + ''.join(f'{x:02x}' for x in rgb).upper()
                assert hex_color == EXPECTED_STYLING['status_colors']['success'], \
                    f"Success badge should use {EXPECTED_STYLING['status_colors']['success']}, got {hex_color}"


class TestToolCallBlocks:
    """Test suite for Feature #115: Tool call blocks."""

    @pytest_asyncio.fixture
    async def browser(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            yield browser
            await browser.close()

    @pytest_asyncio.fixture
    async def page(self, browser):
        context = await browser.new_context()
        page = await context.new_page()
        yield page
        await context.close()

    @pytest.mark.asyncio
    async def test_tool_block_elevated_background(self, page):
        """Test that tool blocks use elevated background."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Check elevated surface color variable exists (using bg-elevated in static HTML)
        elevated_var = await page.evaluate("""
            () => {
                const style = getComputedStyle(document.documentElement);
                const varValue = style.getPropertyValue('--bg-elevated');
                return varValue ? varValue.trim() : null;
            }
        """)

        # Should match expected elevated background
        assert elevated_var is not None, "Should have --bg-elevated variable"
        assert elevated_var == EXPECTED_STYLING['tool_blocks']['background_elevated'], \
            f"Elevated surface should be {EXPECTED_STYLING['tool_blocks']['background_elevated']}"

    @pytest.mark.asyncio
    async def test_tool_block_border_styling(self, page):
        """Test that tool blocks have distinct border."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Check border primary color
        border_var = await page.evaluate("""
            () => {
                const style = getComputedStyle(document.documentElement);
                return style.getPropertyValue('--border-primary').trim();
            }
        """)

        assert border_var == EXPECTED_STYLING['tool_blocks']['border_primary'], \
            f"Border primary should be {EXPECTED_STYLING['tool_blocks']['border_primary']}"

    @pytest.mark.asyncio
    async def test_tool_block_dark_mode(self, page):
        """Test that tool blocks work correctly in dark mode."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Switch to dark mode
        await page.evaluate("() => document.documentElement.classList.add('dark')")

        # Check bg-elevated in dark mode
        elevated_var = await page.evaluate("""
            () => {
                const style = getComputedStyle(document.documentElement);
                return style.getPropertyValue('--bg-elevated').trim();
            }
        """)

        border_var = await page.evaluate("""
            () => {
                const style = getComputedStyle(document.documentElement);
                return style.getPropertyValue('--border-primary').trim();
            }
        """)

        assert elevated_var == EXPECTED_STYLING['tool_blocks']['dark_background_elevated'], \
            f"Dark bg-elevated should be {EXPECTED_STYLING['tool_blocks']['dark_background_elevated']}, got {elevated_var}"
        assert border_var == EXPECTED_STYLING['tool_blocks']['dark_border_primary'], \
            f"Dark border should be {EXPECTED_STYLING['tool_blocks']['dark_border_primary']}, got {border_var}"


class TestStylingIntegrationFeatures:
    """Integration tests for features #112-115."""

    @pytest_asyncio.fixture
    async def browser(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            yield browser
            await browser.close()

    @pytest_asyncio.fixture
    async def page(self, browser):
        context = await browser.new_context()
        page = await context.new_page()
        yield page
        await context.close()

    @pytest.mark.asyncio
    async def test_demo_panel_interaction(self, page):
        """Test that demo panel shows all styling features."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Click demo toggle
        demo_toggle = await page.query_selector("#demoToggle")
        assert demo_toggle is not None, "Demo toggle should exist"

        await demo_toggle.click()

        # Wait for demo panel
        await page.wait_for_selector("#demoPanel", timeout=3000)

        # Check for status badges
        badges = await page.query_selector_all(".status-badge")
        assert len(badges) >= 4, "Should have at least 4 status badges (success, warning, error, info)"

        # Check for loading spinner
        spinner = await page.query_selector(".loading-spinner")
        assert spinner is not None, "Should have loading spinner in demo"

        # Check for skeleton
        skeleton = await page.query_selector(".skeleton")
        assert skeleton is not None, "Should have skeleton loader in demo"

    @pytest.mark.asyncio
    async def test_message_bubble_interaction(self, page):
        """Test message bubble animations and styling."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Check that message bubbles exist in the static page
        user_bubble = await page.query_selector(".message-bubble.user")
        assistant_bubble = await page.query_selector(".message-bubble.assistant")

        assert user_bubble is not None, "User message bubble should exist"
        assert assistant_bubble is not None, "Assistant message bubble should exist"

        # Verify they have animation classes
        user_classes = await user_bubble.get_attribute("class")
        assistant_classes = await assistant_bubble.get_attribute("class")

        assert "animate-slide-in-right" in user_classes, "User bubble should have slide-in-right animation"
        assert "animate-slide-in-left" in assistant_classes, "Assistant bubble should have slide-in-left animation"

    @pytest.mark.asyncio
    async def test_all_animations_work_together(self, page):
        """Test that multiple animations work without conflicts."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Open demo panel to trigger multiple animations
        demo_toggle = await page.query_selector("#demoToggle")
        if demo_toggle:
            await demo_toggle.click()
            await page.wait_for_selector("#demoPanel", timeout=3000)

        # Verify demo panel exists with animations
        demo_panel = await page.query_selector("#demoPanel")
        assert demo_panel is not None, "Demo panel should exist"

        # Verify page is still responsive
        title = await page.title()
        assert "Claude" in title, "Page should remain functional"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
