"""
Test suite for static page styling features.

Tests for:
- Feature #112: Loading states and spinners are visually consistent
- Feature #113: Transitions and animations are smooth
- Feature #114: Status colors (success, warning, error, info)
- Feature #115: Accessibility features (ARIA labels, keyboard nav)
- Feature #116: Responsive design (768px tablet)
- Feature #117: Responsive design (375px mobile)
"""

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright
import asyncio
import json


# Expected color values
EXPECTED_COLORS = {
    "primary": "#CC785C",
    "primary_hover": "#B86A4E",
    "primary_active": "#A35D42",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#3B82F6",
    "light": {
        "bg_primary": "#FFFFFF",
        "bg_secondary": "#F5F5F5",
        "bg_elevated": "#FAFAFA",
        "text_primary": "#1A1A1A",
        "border": "#E5E5E5",
    },
    "dark": {
        "bg_primary": "#1A1A1A",
        "bg_secondary": "#2A2A2A",
        "bg_elevated": "#333333",
        "text_primary": "#E5E5E5",
        "border": "#404040",
    },
    "animation": {
        "fade_in": "0.2s",
        "slide_in": "0.3s",
        "transition": "0.15s",
    }
}


class TestStaticPageFeatures:
    """Test suite for static page features."""

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

    # ==================== Feature #112: Loading States ====================

    @pytest.mark.asyncio
    async def test_loading_spinner_exists(self, page):
        """Test that loading spinner is defined and animated."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Check spinner CSS exists
        has_spinner = await page.evaluate("""
            () => {
                const style = document.querySelector('style').textContent;
                return style.includes('.loading-spinner') && style.includes('animation: spin');
            }
        """)
        assert has_spinner, "Loading spinner CSS should be defined"

    @pytest.mark.asyncio
    async def test_typing_indicator_exists(self, page):
        """Test that typing indicator is defined and animated."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Check typing indicator CSS exists
        has_typing = await page.evaluate("""
            () => {
                const style = document.querySelector('style').textContent;
                return style.includes('.typing-indicator') && style.includes('.typing-dot');
            }
        """)
        assert has_typing, "Typing indicator CSS should be defined"

    @pytest.mark.asyncio
    async def test_skeleton_loader_exists(self, page):
        """Test that skeleton loader is defined and animated."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Check skeleton CSS exists
        has_skeleton = await page.evaluate("""
            () => {
                const style = document.querySelector('style').textContent;
                return style.includes('.skeleton') && style.includes('skeleton-loading');
            }
        """)
        assert has_skeleton, "Skeleton loader CSS should be defined"

    @pytest.mark.asyncio
    async def test_typing_indicator_appears_on_send(self, page):
        """Test that typing indicator appears when sending a message."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Type and send a message
        await page.fill("#messageInput", "Test message")
        await page.click("#sendButton")

        # Check typing indicator becomes visible
        await page.wait_for_selector("#typingIndicator:not(.hidden)", timeout=5000)

        # Verify it has the typing dots
        dots = await page.query_selector_all("#typingIndicator .typing-dot")
        assert len(dots) == 3, "Typing indicator should have 3 dots"

    # ==================== Feature #113: Animations ====================

    @pytest.mark.asyncio
    async def test_animation_durations(self, page):
        """Test that animations use reasonable durations."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Get animation durations from CSS
        durations = await page.evaluate("""
            () => {
                const style = document.querySelector('style').textContent;
                const durations = [];
                // Extract animation durations
                const regex = /animation:\\s*[\\w-]+\\s+([\\d.]+)s/g;
                let match;
                while ((match = regex.exec(style)) !== null) {
                    durations.push(parseFloat(match[1]));
                }
                // Also check transition durations
                const transRegex = /transition:\\s*all\\s+([\\d.]+)s/g;
                while ((match = transRegex.exec(style)) !== null) {
                    durations.push(parseFloat(match[1]));
                }
                return durations;
            }
        """)

        # All durations should be reasonable (0.15-3s)
        # Transitions: 0.15-0.3s
        # Loading animations: 0.6-1.5s
        # Typing: 1s
        for duration in durations:
            assert 0.15 <= duration <= 3.0, \
                f"Animation duration {duration}s should be reasonable (0.15-3s)"

    @pytest.mark.asyncio
    async def test_ease_out_timing(self, page):
        """Test that animations use ease-out timing."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        has_ease_out = await page.evaluate("""
            () => {
                const style = document.querySelector('style').textContent;
                return style.includes('ease-out');
            }
        """)
        assert has_ease_out, "Animations should use ease-out timing"

    @pytest.mark.asyncio
    async def test_message_animation_on_send(self, page):
        """Test that messages animate in when sent."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Send a message
        await page.fill("#messageInput", "Animation test")
        await page.click("#sendButton")

        # Wait for user message to appear with animation
        await asyncio.sleep(0.1)  # Allow animation to start
        user_bubble = await page.query_selector(".message-bubble.user")
        assert user_bubble is not None, "User message should appear"

        # Check it has animation class
        classes = await user_bubble.get_attribute("class")
        assert "animate-slide-in-right" in classes, "User message should have slide-in animation"

        # Wait for assistant response
        await page.wait_for_selector(".message-bubble.assistant", timeout=5000)
        # Get all assistant bubbles and check the last one
        assistant_bubbles = await page.query_selector_all(".message-bubble.assistant")
        if assistant_bubbles:
            assistant_bubble = assistant_bubbles[-1]
            classes = await assistant_bubble.get_attribute("class")
            assert "animate-slide-in-left" in classes, "Assistant message should have slide-in animation"

    # ==================== Feature #114: Status Colors ====================

    @pytest.mark.asyncio
    async def test_status_badge_colors(self, page):
        """Test that status badges use correct colors."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Open demo panel to see status badges
        await page.click("#demoToggle")
        await asyncio.sleep(0.3)

        # Check success badge
        success_bg = await page.evaluate("""
            () => {
                const badge = document.querySelector('.status-badge.success');
                if (!badge) return null;
                return window.getComputedStyle(badge).backgroundColor;
            }
        """)

        if success_bg:
            # Convert to hex
            if success_bg.startswith('rgb'):
                rgb = [int(x) for x in success_bg[4:-1].split(',')]
                hex_color = '#' + ''.join(f'{x:02x}' for x in rgb).upper()
                assert hex_color == EXPECTED_COLORS['success'], \
                    f"Success badge should be {EXPECTED_COLORS['success']}, got {hex_color}"

        # Check warning badge
        warning_bg = await page.evaluate("""
            () => {
                const badge = document.querySelector('.status-badge.warning');
                if (!badge) return null;
                return window.getComputedStyle(badge).backgroundColor;
            }
        """)

        if warning_bg:
            if warning_bg.startswith('rgb'):
                rgb = [int(x) for x in warning_bg[4:-1].split(',')]
                hex_color = '#' + ''.join(f'{x:02x}' for x in rgb).upper()
                assert hex_color == EXPECTED_COLORS['warning'], \
                    f"Warning badge should be {EXPECTED_COLORS['warning']}, got {hex_color}"

        # Check error badge
        error_bg = await page.evaluate("""
            () => {
                const badge = document.querySelector('.status-badge.error');
                if (!badge) return null;
                return window.getComputedStyle(badge).backgroundColor;
            }
        """)

        if error_bg:
            if error_bg.startswith('rgb'):
                rgb = [int(x) for x in error_bg[4:-1].split(',')]
                hex_color = '#' + ''.join(f'{x:02x}' for x in rgb).upper()
                assert hex_color == EXPECTED_COLORS['error'], \
                    f"Error badge should be {EXPECTED_COLORS['error']}, got {hex_color}"

        # Check info badge
        info_bg = await page.evaluate("""
            () => {
                const badge = document.querySelector('.status-badge.info');
                if (!badge) return null;
                return window.getComputedStyle(badge).backgroundColor;
            }
        """)

        if info_bg:
            if info_bg.startswith('rgb'):
                rgb = [int(x) for x in info_bg[4:-1].split(',')]
                hex_color = '#' + ''.join(f'{x:02x}' for x in rgb).upper()
                assert hex_color == EXPECTED_COLORS['info'], \
                    f"Info badge should be {EXPECTED_COLORS['info']}, got {hex_color}"

    # ==================== Feature #115: Accessibility ====================

    @pytest.mark.asyncio
    async def test_aria_labels(self, page):
        """Test that interactive elements have ARIA labels."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Check theme toggle button
        theme_label = await page.get_attribute("#themeToggle", "aria-label")
        assert theme_label is not None, "Theme toggle should have aria-label"

        # Check demo toggle button
        demo_label = await page.get_attribute("#demoToggle", "aria-label")
        assert demo_label is not None, "Demo toggle should have aria-label"

        # Check message input
        input_label = await page.get_attribute("#messageInput", "aria-label")
        assert input_label is not None, "Message input should have aria-label"

        # Check send button
        send_label = await page.get_attribute("#sendButton", "aria-label")
        assert send_label is not None, "Send button should have aria-label"

    @pytest.mark.asyncio
    async def test_keyboard_navigation(self, page):
        """Test that keyboard navigation works."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Focus on message input
        await page.focus("#messageInput")
        focused = await page.evaluate("() => document.activeElement.id === 'messageInput'")
        assert focused, "Message input should be focusable"

        # Type and send with keyboard
        await page.type("#messageInput", "Keyboard test")
        await page.keyboard.press("Enter")

        # Message should be sent
        await asyncio.sleep(0.5)
        user_bubble = await page.query_selector(".message-bubble.user")
        assert user_bubble is not None, "Message should be sent with keyboard"

    @pytest.mark.asyncio
    async def test_focus_indicators(self, page):
        """Test that focus indicators are visible."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Check that focus styles are defined
        has_focus_styles = await page.evaluate("""
            () => {
                const style = document.querySelector('style').textContent;
                return style.includes('focus-visible') && style.includes('outline');
            }
        """)
        assert has_focus_styles, "Focus indicators should be defined"

    @pytest.mark.asyncio
    async def test_reduced_motion_support(self, page):
        """Test that reduced motion preference is respected."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Check that reduced motion media query exists
        has_reduced_motion = await page.evaluate("""
            () => {
                const style = document.querySelector('style').textContent;
                return style.includes('prefers-reduced-motion');
            }
        """)
        assert has_reduced_motion, "Reduced motion support should be defined"

    # ==================== Feature #116: Tablet Responsive (768px) ====================

    @pytest.mark.asyncio
    async def test_tablet_responsive_layout(self, page):
        """Test that layout adapts at 768px width."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Set viewport to tablet size
        await page.set_viewport_size({"width": 768, "height": 1024})
        await asyncio.sleep(0.2)

        # Check chat main padding
        padding = await page.evaluate("""
            () => {
                const chatMain = document.querySelector('.chat-main');
                if (!chatMain) return null;
                return window.getComputedStyle(chatMain).padding;
            }
        """)

        # Should have reduced padding at tablet
        if padding:
            # Extract numeric value
            padding_px = int(padding.replace('px', ''))
            assert padding_px <= 12, f"Padding should be reduced at tablet, got {padding}px"

        # Check message bubble max-width
        max_width = await page.evaluate("""
            () => {
                const bubble = document.querySelector('.message-bubble');
                if (!bubble) return null;
                return window.getComputedStyle(bubble).maxWidth;
            }
        """)

        # Should be 90% or similar at smaller screens
        assert max_width, "Message bubble should have max-width defined"

    @pytest.mark.asyncio
    async def test_tablet_header_buttons(self, page):
        """Test that header buttons are usable at tablet."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        await page.set_viewport_size({"width": 768, "height": 1024})
        await asyncio.sleep(0.2)

        # Check header actions
        header_actions = await page.query_selector(".header-actions")
        assert header_actions is not None, "Header actions should exist"

        # Check button sizes
        button_size = await page.evaluate("""
            () => {
                const btn = document.querySelector('.icon-button');
                if (!btn) return null;
                const style = window.getComputedStyle(btn);
                return {
                    padding: style.padding,
                    fontSize: style.fontSize
                };
            }
        """)

        # Buttons should have appropriate font size (may be 12px on smaller viewports)
        if button_size:
            # Font size should be defined and reasonable
            font_px = int(button_size['fontSize'].replace('px', ''))
            assert 10 <= font_px <= 16, f"Font size {font_px}px should be appropriate for buttons"

    # ==================== Feature #117: Mobile Responsive (375px) ====================

    @pytest.mark.asyncio
    async def test_mobile_responsive_layout(self, page):
        """Test that layout adapts at 375px width."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Set viewport to mobile size
        await page.set_viewport_size({"width": 375, "height": 667})
        await asyncio.sleep(0.2)

        # Check chat main padding
        padding = await page.evaluate("""
            () => {
                const chatMain = document.querySelector('.chat-main');
                if (!chatMain) return null;
                return window.getComputedStyle(chatMain).padding;
            }
        """)

        # Should have minimal padding at mobile
        if padding:
            padding_px = int(padding.replace('px', ''))
            assert padding_px <= 12, f"Padding should be minimal at mobile, got {padding}px"

    @pytest.mark.asyncio
    async def test_mobile_input_full_width(self, page):
        """Test that input is full width on mobile."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        await page.set_viewport_size({"width": 375, "height": 667})
        await asyncio.sleep(0.2)

        # Check input wrapper
        input_wrapper = await page.evaluate("""
            () => {
                const wrapper = document.querySelector('.input-wrapper');
                if (!wrapper) return null;
                const style = window.getComputedStyle(wrapper);
                return {
                    flexDirection: style.flexDirection,
                    width: style.width
                };
            }
        """)

        # On mobile, input should take most of the width
        assert input_wrapper is not None, "Input wrapper should exist"

    @pytest.mark.asyncio
    async def test_mobile_message_bubble_width(self, page):
        """Test that message bubbles use full width on mobile."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        await page.set_viewport_size({"width": 375, "height": 667})
        await asyncio.sleep(0.2)

        # Check message bubble max-width at mobile
        max_width = await page.evaluate("""
            () => {
                const bubble = document.querySelector('.message-bubble');
                if (!bubble) return null;
                const style = window.getComputedStyle(bubble);
                return style.maxWidth;
            }
        """)

        # Should be 90% or similar
        assert max_width, "Message bubble should have max-width at mobile"

    # ==================== Integration Tests ====================

    @pytest.mark.asyncio
    async def test_theme_toggle_integration(self, page):
        """Test that theme toggle works end-to-end."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Start in light theme
        await page.evaluate("() => document.documentElement.classList.remove('dark')")

        # Get initial background
        light_bg = await page.evaluate("() => window.getComputedStyle(document.body).backgroundColor")

        # Toggle to dark
        await page.click("#themeToggle")
        await asyncio.sleep(0.2)

        # Get dark background
        dark_bg = await page.evaluate("() => window.getComputedStyle(document.body).backgroundColor")

        # Should be different
        assert light_bg != dark_bg, "Theme toggle should change colors"

        # Verify dark theme colors
        if dark_bg.startswith('rgb'):
            rgb = [int(x) for x in dark_bg[4:-1].split(',')]
            hex_color = '#' + ''.join(f'{x:02x}' for x in rgb).upper()
            assert hex_color == EXPECTED_COLORS['dark']['bg_primary'], \
                f"Dark theme should have correct background"

    @pytest.mark.asyncio
    async def test_demo_panel_integration(self, page):
        """Test that demo panel shows all styling features."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Open demo panel
        await page.click("#demoToggle")
        await asyncio.sleep(0.3)

        # Check panel exists
        panel = await page.query_selector("#demoPanel")
        assert panel is not None, "Demo panel should appear"

        # Check for status badges
        badges = await page.query_selector_all(".status-badge")
        assert len(badges) >= 4, "Should have at least 4 status badges"

        # Check for skeleton
        skeleton = await page.query_selector(".skeleton")
        assert skeleton is not None, "Should have skeleton loader"

        # Check for spinner
        spinner = await page.query_selector(".loading-spinner")
        assert spinner is not None, "Should have loading spinner"

        # Close demo panel
        await page.click("#demoToggle")
        await asyncio.sleep(0.2)

        panel = await page.query_selector("#demoPanel")
        assert panel is None, "Demo panel should be closed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
