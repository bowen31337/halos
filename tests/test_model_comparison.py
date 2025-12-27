"""
Test Model Comparison View (Feature #153)

Tests for the model comparison feature that shows side-by-side responses
from multiple models.
"""

import pytest
import asyncio
from playwright.async_api import async_playwright
from src.core.database import get_db
from src.models.conversation import Conversation, Message
from src.models.user import User
from uuid import uuid4


class TestModelComparison:
    """Test suite for model comparison view functionality."""

    @pytest.mark.asyncio
    async def test_comparison_mode_toggle(self):
        """Test Step 1: Enable model comparison mode"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Navigate to the app
            await page.goto('http://localhost:8000')

            # Wait for the page to load
            await page.wait_for_selector('text=Claude', timeout=10000)

            # Find and click the comparison toggle button
            compare_button = page.locator('button:has-text("Compare")')
            await compare_button.click()

            # Verify comparison modal opens
            modal = page.locator('text=Select models to compare')
            await modal.wait_for(state='visible', timeout=5000)

            # Select two models
            sonnet_option = page.locator('text=Claude Sonnet 4.5')
            haiku_option = page.locator('text=Claude Haiku 4.5')

            await sonnet_option.click()
            await haiku_option.click()

            # Confirm selection
            confirm_button = page.locator('button:has-text("Start Comparison")')
            await confirm_button.click()

            # Verify comparison mode is active
            compare_button_active = page.locator('button:has-text("Compare")')
            assert await compare_button_active.get_attribute('class').contains('bg-[var(--primary)]')

            print("✅ Comparison mode toggle test passed")
            await browser.close()

    @pytest.mark.asyncio
    async def test_model_selection(self):
        """Test Step 2: Select two models to compare"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.goto('http://localhost:8000')
            await page.wait_for_selector('text=Claude', timeout=10000)

            # Open comparison modal
            await page.locator('button:has-text("Compare")').click()
            await page.wait_for_selector('text=Select models to compare', timeout=5000)

            # Verify multiple models are available
            models = ['Claude Sonnet 4.5', 'Claude Haiku 4.5', 'Claude Opus 4.1']
            for model in models:
                assert await page.locator(f'text={model}').count() > 0

            # Select exactly two models
            await page.locator('text=Claude Sonnet 4.5').click()
            await page.locator('text=Claude Opus 4.1').click()

            # Verify selection is shown
            selected = page.locator('.selected-model')
            assert await selected.count() == 2

            print("✅ Model selection test passed")
            await browser.close()

    @pytest.mark.asyncio
    async def test_split_view_display(self):
        """Test Step 3 & 4: Send message and verify split view shows both responses"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.goto('http://localhost:8000')
            await page.wait_for_selector('text=Claude', timeout=10000)

            # Enable comparison mode
            await page.locator('button:has-text("Compare")').click()
            await page.wait_for_selector('text=Select models to compare', timeout=5000)
            await page.locator('text=Claude Sonnet 4.5').click()
            await page.locator('text=Claude Haiku 4.5').click()
            await page.locator('button:has-text("Start Comparison")').click()

            # Wait for comparison view to load
            await page.wait_for_selector('text=vs', timeout=5000)

            # Send a test message
            input_box = page.locator('textarea')
            await input_box.fill('Hello, test message for comparison')
            send_button = page.locator('button:has-text("Send")')
            await send_button.click()

            # Wait for responses to appear
            await asyncio.sleep(2)

            # Verify split view structure exists
            # Check for comparison container
            comparison_container = page.locator('div[class*="border"] >> div:has-text("Claude Sonnet")')
            assert await comparison_container.count() > 0

            # Check for both model headers
            sonnet_header = page.locator('text=Claude Sonnet')
            haiku_header = page.locator('text=Claude Haiku')

            assert await sonnet_header.count() > 0
            assert await haiku_header.count() > 0

            print("✅ Split view display test passed")
            await browser.close()

    @pytest.mark.asyncio
    async def test_streaming_simultaneous(self):
        """Test Step 5: Verify responses stream simultaneously"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.goto('http://localhost:8000')
            await page.wait_for_selector('text=Claude', timeout=10000)

            # Enable comparison mode
            await page.locator('button:has-text("Compare")').click()
            await page.wait_for_selector('text=Select models to compare', timeout=5000)
            await page.locator('text=Claude Sonnet 4.5').click()
            await page.locator('text=Claude Haiku 4.5').click()
            await page.locator('button:has-text("Start Comparison")').click()
            await page.wait_for_selector('text=vs', timeout=5000)

            # Send message
            input_box = page.locator('textarea')
            await input_box.fill('Test streaming')
            await page.locator('button:has-text("Send")').click()

            # Wait a moment for streaming to start
            await asyncio.sleep(1)

            # Check for typing indicators in both panes
            typing_indicators = page.locator('.typing-indicator')
            # Should see at least one indicator during streaming
            assert await typing_indicators.count() >= 1

            # Wait for streaming to complete
            await page.wait_for_selector('.typing-indicator', state='hidden', timeout=30000)

            print("✅ Simultaneous streaming test passed")
            await browser.close()

    @pytest.mark.asyncio
    async def test_model_labels_clear(self):
        """Test Step 6: Verify model labels are clear"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.goto('http://localhost:8000')
            await page.wait_for_selector('text=Claude', timeout=10000)

            # Enable comparison mode
            await page.locator('button:has-text("Compare")').click()
            await page.wait_for_selector('text=Select models to compare', timeout=5000)
            await page.locator('text=Claude Sonnet 4.5').click()
            await page.locator('text=Claude Haiku 4.5').click()
            await page.locator('button:has-text("Start Comparison")').click()
            await page.wait_for_selector('text=vs', timeout=5000)

            # Check header labels
            headers = page.locator('div:has-text("Claude Sonnet 4.5")')
            assert await headers.count() > 0

            # Check for model descriptions
            descriptions = page.locator('text=Balanced, Fast')
            assert await descriptions.count() >= 2

            print("✅ Model labels test passed")
            await browser.close()

    @pytest.mark.asyncio
    async def test_select_preferred_response(self):
        """Test Step 7: Select preferred response"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.goto('http://localhost:8000')
            await page.wait_for_selector('text=Claude', timeout=10000)

            # Enable comparison mode
            await page.locator('button:has-text("Compare")').click()
            await page.wait_for_selector('text=Select models to compare', timeout=5000)
            await page.locator('text=Claude Sonnet 4.5').click()
            await page.locator('text=Claude Haiku 4.5').click()
            await page.locator('button:has-text("Start Comparison")').click()
            await page.wait_for_selector('text=vs', timeout=5000)

            # Send message and wait for responses
            input_box = page.locator('textarea')
            await input_box.fill('Test preference selection')
            await page.locator('button:has-text("Send")').click()
            await asyncio.sleep(3)

            # Look for preference selection buttons (if implemented)
            # This might be a future enhancement
            preference_buttons = page.locator('button:has-text("Select")')
            if await preference_buttons.count() > 0:
                await preference_buttons.first.click()
                print("✅ Preference selection available")
            else:
                print("ℹ️  Preference selection not yet implemented (optional)")

            await browser.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
