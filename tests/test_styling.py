"""
Test suite for styling features (#101-104).

Tests for:
- Feature #101: Primary orange/amber color (#CC785C)
- Feature #102: Light theme background colors
- Feature #103: Dark theme colors
- Feature #104: Typography (font family and sizes)
"""

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright
import asyncio
import json
import os


# Expected color values
EXPECTED_COLORS = {
    "primary": "#CC785C",
    "primary_hover": "#B86A4E",
    "primary_active": "#A35D42",
    "light": {
        "bg_primary": "#FFFFFF",
        "bg_secondary": "#F5F5F5",
        "bg_elevated": "#FAFAFA",
        "surface_elevated": "#FAFAFA",
        "text_primary": "#1A1A1A",
        "text_secondary": "#6B7280",
        "border": "#E5E5E5",
    },
    "dark": {
        "bg_primary": "#1A1A1A",
        "bg_secondary": "#2A2A2A",
        "bg_elevated": "#333333",
        "surface_elevated": "#333333",
        "text_primary": "#E5E5E5",
        "text_secondary": "#9CA3AF",
        "border": "#404040",
    },
    "typography": {
        "font_family": ["Inter", "SF Pro", "system-ui", "Segoe UI", "Roboto"],
        "code_font": ["JetBrains Mono", "Fira Code", "Consolas", "Monaco"],
        "base_font_size": "16px",
    }
}


class TestStylingFeatures:
    """Test suite for all styling features."""

    @pytest_asyncio.fixture
    async def browser(self):
        """Setup browser fixture."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            yield browser
            await browser.close()

    @pytest_asyncio.fixture
    async def page(self, browser):
        """Setup page fixture with context."""
        context = await browser.new_context()
        page = await context.new_page()
        yield page
        await context.close()

    async def get_computed_color(self, page, selector, property_name):
        """Get computed color value for an element."""
        return await page.evaluate(f"""
            () => {{
                const el = document.querySelector('{selector}');
                if (!el) return null;
                const style = window.getComputedStyle(el);
                const value = style.getPropertyValue('{property_name}').trim();
                // Convert rgb to hex for comparison
                if (value.startsWith('rgb')) {{
                    const rgb = value.match(/\\d+/g);
                    if (rgb) {{
                        return '#' + rgb.map(x => {{
                            const hex = parseInt(x).toString(16);
                            return hex.length === 1 ? '0' + hex : hex;
                        }}).join('').toUpperCase();
                    }}
                }}
                return value;
            }}
        """)

    async def get_element_font(self, page, selector):
        """Get font properties for an element."""
        return await page.evaluate(f"""
            () => {{
                const el = document.querySelector('{selector}');
                if (!el) return null;
                const style = window.getComputedStyle(el);
                return {{
                    fontFamily: style.fontFamily,
                    fontSize: style.fontSize,
                    fontWeight: style.fontWeight,
                }};
            }}
        """)

    # ==================== Feature #101: Primary Color ====================

    @pytest.mark.asyncio
    async def test_primary_color_exists(self, page):
        """Test that primary color CSS variable is defined."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Get the root CSS variables
        root_styles = await page.evaluate("""
            () => {
                const style = getComputedStyle(document.documentElement);
                return {
                    primary: style.getPropertyValue('--primary').trim(),
                    primaryHover: style.getPropertyValue('--primary-hover').trim(),
                    primaryActive: style.getPropertyValue('--primary-active').trim(),
                };
            }
        """)

        assert root_styles['primary'] == EXPECTED_COLORS['primary'], \
            f"Primary color should be {EXPECTED_COLORS['primary']}, got {root_styles['primary']}"
        assert root_styles['primaryHover'] == EXPECTED_COLORS['primary_hover'], \
            f"Primary hover should be {EXPECTED_COLORS['primary_hover']}, got {root_styles['primaryHover']}"
        assert root_styles['primaryActive'] == EXPECTED_COLORS['primary_active'], \
            f"Primary active should be {EXPECTED_COLORS['primary_active']}, got {root_styles['primaryActive']}"

    @pytest.mark.asyncio
    async def test_primary_color_on_send_button(self, page):
        """Test that send button uses primary color."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Wait for the chat input to be visible
        await page.wait_for_selector("textarea, input[type='text']", timeout=5000)

        # Type a message to make the send button visible
        await page.fill("textarea, input[type='text']", "Test message")

        # Get the send button background color
        send_button = await page.query_selector("button:has(svg[stroke='currentColor'])")
        if not send_button:
            send_button = await page.query_selector("button[title*='Send'], button[type='submit']")

        if send_button:
            bg_color = await send_button.evaluate("el => window.getComputedStyle(el).backgroundColor")
            # Convert to hex for comparison
            if bg_color.startswith('rgb'):
                rgb = [int(x) for x in bg_color[4:-1].split(',')]
                hex_color = '#' + ''.join(f'{x:02x}' for x in rgb).upper()
                assert hex_color == EXPECTED_COLORS['primary'], \
                    f"Send button should use primary color {EXPECTED_COLORS['primary']}, got {hex_color}"

    # ==================== Feature #102: Light Theme ====================

    @pytest.mark.asyncio
    async def test_light_theme_colors(self, page):
        """Test that light theme uses correct background colors."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Ensure light theme is set
        await page.evaluate("() => document.documentElement.classList.remove('dark')")

        # Get light theme CSS variables
        root_styles = await page.evaluate("""
            () => {
                const style = getComputedStyle(document.documentElement);
                return {
                    bgPrimary: style.getPropertyValue('--bg-primary').trim(),
                    bgSecondary: style.getPropertyValue('--bg-secondary').trim(),
                    bgElevated: style.getPropertyValue('--bg-elevated').trim(),
                    textPrimary: style.getPropertyValue('--text-primary').trim(),
                    border: style.getPropertyValue('--border').trim(),
                };
            }
        """)

        light = EXPECTED_COLORS['light']
        assert root_styles['bgPrimary'] == light['bg_primary'], \
            f"Light bg-primary should be {light['bg_primary']}, got {root_styles['bgPrimary']}"
        assert root_styles['bgSecondary'] == light['bg_secondary'], \
            f"Light bg-secondary should be {light['bg_secondary']}, got {root_styles['bgSecondary']}"
        assert root_styles['bgElevated'] == light['bg_elevated'], \
            f"Light bg-elevated should be {light['bg_elevated']}, got {root_styles['bgElevated']}"
        assert root_styles['textPrimary'] == light['text_primary'], \
            f"Light text-primary should be {light['text_primary']}, got {root_styles['textPrimary']}"
        assert root_styles['border'] == light['border'], \
            f"Light border should be {light['border']}, got {root_styles['border']}"

    @pytest.mark.asyncio
    async def test_light_theme_body_background(self, page):
        """Test that body has white background in light theme."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Ensure light theme
        await page.evaluate("() => document.documentElement.classList.remove('dark')")

        body_bg = await page.evaluate("() => window.getComputedStyle(document.body).backgroundColor")
        # Convert to hex
        if body_bg.startswith('rgb'):
            rgb = [int(x) for x in body_bg[4:-1].split(',')]
            hex_color = '#' + ''.join(f'{x:02x}' for x in rgb).upper()
            assert hex_color == EXPECTED_COLORS['light']['bg_primary'], \
                f"Body should have white background in light theme, got {hex_color}"

    # ==================== Feature #103: Dark Theme ====================

    @pytest.mark.asyncio
    async def test_dark_theme_colors(self, page):
        """Test that dark theme uses correct background colors."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Ensure dark theme is set
        await page.evaluate("() => document.documentElement.classList.add('dark')")

        # Get dark theme CSS variables
        root_styles = await page.evaluate("""
            () => {
                const style = getComputedStyle(document.documentElement);
                return {
                    bgPrimary: style.getPropertyValue('--bg-primary').trim(),
                    bgSecondary: style.getPropertyValue('--bg-secondary').trim(),
                    bgElevated: style.getPropertyValue('--bg-elevated').trim(),
                    textPrimary: style.getPropertyValue('--text-primary').trim(),
                    border: style.getPropertyValue('--border').trim(),
                };
            }
        """)

        dark = EXPECTED_COLORS['dark']
        assert root_styles['bgPrimary'] == dark['bg_primary'], \
            f"Dark bg-primary should be {dark['bg_primary']}, got {root_styles['bgPrimary']}"
        assert root_styles['bgSecondary'] == dark['bg_secondary'], \
            f"Dark bg-secondary should be {dark['bg_secondary']}, got {root_styles['bgSecondary']}"
        assert root_styles['bgElevated'] == dark['bg_elevated'], \
            f"Dark bg-elevated should be {dark['bg_elevated']}, got {root_styles['bgElevated']}"
        assert root_styles['textPrimary'] == dark['text_primary'], \
            f"Dark text-primary should be {dark['text_primary']}, got {root_styles['textPrimary']}"
        assert root_styles['border'] == dark['border'], \
            f"Dark border should be {dark['border']}, got {root_styles['border']}"

    @pytest.mark.asyncio
    async def test_dark_theme_body_background(self, page):
        """Test that body has dark background in dark theme."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Ensure dark theme
        await page.evaluate("() => document.documentElement.classList.add('dark')")

        body_bg = await page.evaluate("() => window.getComputedStyle(document.body).backgroundColor")
        # Convert to hex
        if body_bg.startswith('rgb'):
            rgb = [int(x) for x in body_bg[4:-1].split(',')]
            hex_color = '#' + ''.join(f'{x:02x}' for x in rgb).upper()
            assert hex_color == EXPECTED_COLORS['dark']['bg_primary'], \
                f"Body should have dark background in dark theme, got {hex_color}"

    # ==================== Feature #104: Typography ====================

    @pytest.mark.asyncio
    async def test_body_font_family(self, page):
        """Test that body uses correct font family."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        body_font = await page.evaluate("() => window.getComputedStyle(document.body).fontFamily")

        # Check that it contains one of the expected fonts
        font_lower = body_font.lower()
        expected_fonts = [f.lower() for f in EXPECTED_COLORS['typography']['font_family']]

        has_expected_font = any(font in font_lower for font in expected_fonts)
        assert has_expected_font, \
            f"Body font should contain one of {expected_fonts}, got {body_font}"

    @pytest.mark.asyncio
    async def test_body_font_size(self, page):
        """Test that body uses correct base font size."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        body_font_size = await page.evaluate("() => window.getComputedStyle(document.body).fontSize")
        assert body_font_size == EXPECTED_COLORS['typography']['base_font_size'], \
            f"Body font size should be {EXPECTED_COLORS['typography']['base_font_size']}, got {body_font_size}"

    @pytest.mark.asyncio
    async def test_code_font_family(self, page):
        """Test that code uses monospace font."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Get code font from CSS
        code_font = await page.evaluate("""
            () => {
                const style = getComputedStyle(document.documentElement);
                // Create a temp element to get code font
                const temp = document.createElement('code');
                document.body.appendChild(temp);
                const font = window.getComputedStyle(temp).fontFamily;
                temp.remove();
                return font;
            }
        """)

        # Check that it contains one of the expected code fonts
        font_lower = code_font.lower()
        expected_code_fonts = [f.lower() for f in EXPECTED_COLORS['typography']['code_font']]

        has_expected_font = any(font in font_lower for font in expected_code_fonts)
        assert has_expected_font, \
            f"Code font should contain one of {expected_code_fonts}, got {code_font}"

    @pytest.mark.asyncio
    async def test_message_text_size(self, page):
        """Test that message text uses correct size (16px)."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Wait for chat interface
        await page.wait_for_selector("textarea, input[type='text']", timeout=5000)

        # Get body font size (should be 16px)
        body_font_size = await page.evaluate("() => window.getComputedStyle(document.body).fontSize")
        assert body_font_size == "16px", \
            f"Body font size should be 16px, got {body_font_size}"

    @pytest.mark.asyncio
    async def test_semibold_headings(self, page):
        """Test that headings use semibold weight."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Get prose heading weight from CSS
        heading_weight = await page.evaluate("""
            () => {
                const style = getComputedStyle(document.documentElement);
                // Create temp h2 element
                const temp = document.createElement('h2');
                temp.className = 'prose';
                document.body.appendChild(temp);
                const weight = window.getComputedStyle(temp).fontWeight;
                temp.remove();
                return weight;
            }
        """)

        # Should be 600 (semibold) or higher
        weight_num = int(heading_weight) if heading_weight.isdigit() else 0
        assert weight_num >= 600, \
            f"Heading weight should be semibold (600+), got {heading_weight}"


# ==================== Integration Test ====================

class TestStylingIntegration:
    """Integration tests for styling with theme switching."""

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
    async def test_theme_switching(self, page):
        """Test that theme switching updates colors correctly."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")

        # Start with light theme
        await page.evaluate("() => document.documentElement.classList.remove('dark')")

        light_bg = await page.evaluate("() => window.getComputedStyle(document.body).backgroundColor")

        # Switch to dark
        await page.evaluate("() => document.documentElement.classList.add('dark')")
        await asyncio.sleep(0.2)  # Allow transition

        dark_bg = await page.evaluate("() => window.getComputedStyle(document.body).backgroundColor")

        # Colors should be different
        assert light_bg != dark_bg, \
            f"Light and dark backgrounds should differ: {light_bg} vs {dark_bg}"

        # Verify specific values
        if light_bg.startswith('rgb'):
            light_hex = '#' + ''.join(f'{int(x):02x}' for x in light_bg[4:-1].split(',')).upper()
            assert light_hex == "#FFFFFF", f"Light bg should be white, got {light_hex}"

        if dark_bg.startswith('rgb'):
            dark_hex = '#' + ''.join(f'{int(x):02x}' for x in dark_bg[4:-1].split(',')).upper()
            assert dark_hex == "#1A1A1A", f"Dark bg should be dark gray, got {dark_hex}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
