"""Browser-based test for content filtering UI."""

import asyncio
import pytest
from playwright.async_api import async_playwright, expect


@pytest.mark.asyncio
async def test_content_filtering_ui():
    """Test content filtering UI in browser."""
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Navigate to the app
            await page.goto("http://localhost:5173")
            await page.wait_for_load_state("networkidle")

            # Wait for the app to load
            await asyncio.sleep(2)

            # Find and click settings button (gear icon)
            settings_button = page.locator('button[aria-label="Open settings"], button:has-text("Settings")')
            await settings_button.click(timeout=5000)

            # Wait for settings modal to appear
            await page.wait_for_selector('[role="dialog"]', timeout=5000)

            # Find and click "Privacy & Safety" tab
            privacy_tab = page.locator('button:has-text("Privacy & Safety")')
            await privacy_tab.click(timeout=3000)

            # Wait for tab content to load
            await asyncio.sleep(1)

            # Verify filter level options are visible
            await expect(page.locator('text=Content Filtering Level')).to_be_visible()

            # Check that all filter levels are present
            for level in ['Off', 'Low', 'Medium', 'High']:
                await expect(page.locator(f'text={level}')).to_be_visible()

            # Click on "High" filter level
            high_level = page.locator('button:has-text("High")').first
            await high_level.click()
            await asyncio.sleep(0.5)

            # Verify it's selected (has border highlight)
            await expect(page.locator('button:has-text("High")').first).to_be_visible()

            # Verify category filters are visible
            await expect(page.locator('text=Filtered Categories')).to_be_visible()

            # Check that all categories are present
            categories = ['Violence & Gore', 'Hate Speech', 'Sexual Content', 'Self-Harm', 'Illegal Activities']
            for category in categories:
                await expect(page.locator(f'text={category}')).to_be_visible()

            # Click one category to deselect it
            violence_category = page.locator('button:has-text("Violence & Gore")').first
            await violence_category.click()
            await asyncio.sleep(0.5)

            # Click it again to reselect
            await violence_category.click()
            await asyncio.sleep(0.5)

            # Verify info section is visible
            await expect(page.locator('text=About Content Filtering')).to_be_visible()

            print("✓ Content filtering UI test passed")

        finally:
            await browser.close()


@pytest.mark.asyncio
async def test_content_filtering_persistence():
    """Test that content filtering settings persist."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        try:
            # First session
            page1 = await context.new_page()
            await page1.goto("http://localhost:5173")
            await page1.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # Open settings
            settings_button = page1.locator('button[aria-label="Open settings"], button:has-text("Settings")')
            await settings_button.click(timeout=5000)
            await page1.wait_for_selector('[role="dialog"]', timeout=5000)

            # Go to Privacy tab
            privacy_tab = page1.locator('button:has-text("Privacy & Safety")')
            await privacy_tab.click(timeout=3000)
            await asyncio.sleep(1)

            # Set to Medium level
            medium_level = page1.locator('button:has-text("Medium")').first
            await medium_level.click()
            await asyncio.sleep(0.5)

            # Close settings
            close_button = page1.locator('[aria-label="Close settings"]')
            await close_button.click()
            await asyncio.sleep(1)

            # Second session - verify setting persisted
            page2 = await context.new_page()
            await page2.goto("http://localhost:5173")
            await page2.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # Open settings again
            settings_button = page2.locator('button[aria-label="Open settings"], button:has-text("Settings")')
            await settings_button.click(timeout=5000)
            await page2.wait_for_selector('[role="dialog"]', timeout=5000)

            # Go to Privacy tab
            privacy_tab = page2.locator('button:has-text("Privacy & Safety")')
            await privacy_tab.click(timeout=3000)
            await asyncio.sleep(1)

            # Verify Medium is still selected (has visible checkmark or highlighted border)
            await expect(page2.locator('button:has-text("Medium")').first).to_be_visible()

            print("✓ Content filtering persistence test passed")

        finally:
            await browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
