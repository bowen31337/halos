#!/usr/bin/env python3
"""UI tests for memory management feature using Playwright.

This test verifies Feature #66: Memory management UI allows viewing and deleting memories

Test Steps:
1. Open memory management modal
2. Verify list of stored memories displays
3. Verify each memory shows category and content
4. Click to edit a memory
5. Modify content and save
6. Verify changes persist
7. Delete a memory
8. Verify it no longer appears
"""

import pytest
from playwright.sync_api import Page, expect


class TestMemoryUI:
    """Test memory management UI workflows."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def test_memory_button_in_header(self, page: Page, base_url: str):
        """Test that memory button appears in header."""
        # Navigate to app
        page.goto(base_url)

        # Create a new conversation first (memory button shows in conversations)
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        # Check for memory button in header
        memory_button = page.locator('button[title="Long-term Memory"]')
        expect(memory_button).to_be_visible()

    def test_open_memory_manager(self, page: Page, base_url: str):
        """Test opening the memory management modal."""
        # Navigate to app
        page.goto(base_url)

        # Create a new conversation
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        # Click memory button
        page.click('button[title="Long-term Memory"]')

        # Wait for memory manager modal to appear
        page.wait_for_selector("text=Long-Term Memory", timeout=5000)

        # Verify modal content
        expect(page.locator("text=Memory Enabled")).to_be_visible()
        expect(page.locator("text=Create New Memory")).to_be_visible()
        expect(page.locator("text=Search memories")).to_be_visible()

    def test_create_memory(self, page: Page, base_url: str):
        """Test creating a new memory."""
        # Navigate to app
        page.goto(base_url)

        # Create a new conversation
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        # Open memory manager
        page.click('button[title="Long-term Memory"]')
        page.wait_for_selector("text=Long-Term Memory")

        # Click create new memory button
        page.click("text=Create New Memory")

        # Fill in memory content
        page.fill('textarea[placeholder*="Enter memory content"]', "User prefers dark mode")

        # Select category
        page.select_option('select', 'preference')

        # Click save
        page.click("text=Save Memory")

        # Wait for memory to appear in list
        page.wait_for_selector("text=User prefers dark mode", timeout=5000)

        # Verify the memory is visible
        expect(page.locator("text=User prefers dark mode")).to_be_visible()
        expect(page.locator("text=PREFERENCE")).to_be_visible()

    def test_edit_memory(self, page: Page, base_url: str):
        """Test editing an existing memory."""
        # Navigate to app
        page.goto(base_url)

        # Create a new conversation
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        # Open memory manager
        page.click('button[title="Long-term Memory"]')
        page.wait_for_selector("text=Long-Term Memory")

        # Create a memory first
        page.click("text=Create New Memory")
        page.fill('textarea[placeholder*="Enter memory content"]', "Original content")
        page.select_option('select', 'fact')
        page.click("text=Save Memory")
        page.wait_for_selector("text=Original content", timeout=5000)

        # Click edit button (pencil icon)
        page.click('button[title="Edit"]')

        # Modify content
        page.fill('textarea[rows="4"]', "Updated content")

        # Save changes
        page.click("text=Save")

        # Wait for update and verify
        page.wait_for_selector("text=Updated content", timeout=5000)
        expect(page.locator("text=Updated content")).to_be_visible()
        expect(page.locator("text=Original content")).not_to_be_visible()

    def test_delete_memory(self, page: Page, base_url: str):
        """Test deleting a memory."""
        # Navigate to app
        page.goto(base_url)

        # Create a new conversation
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        # Open memory manager
        page.click('button[title="Long-term Memory"]')
        page.wait_for_selector("text=Long-Term Memory")

        # Create a memory first
        page.click("text=Create New Memory")
        page.fill('textarea[placeholder*="Enter memory content"]', "To be deleted")
        page.select_option('select', 'fact')
        page.click("text=Save Memory")
        page.wait_for_selector("text=To be deleted", timeout=5000)

        # Click delete button (trash icon)
        # Handle confirmation dialog
        page.on("dialog", lambda dialog: dialog.accept())
        page.click('button[title="Delete"]')

        # Wait for memory to disappear
        page.wait_for_timeout(1000)  # Brief wait for deletion
        expect(page.locator("text=To be deleted")).not_to_be_visible()

    def test_search_memories(self, page: Page, base_url: str):
        """Test searching for memories."""
        # Navigate to app
        page.goto(base_url)

        # Create a new conversation
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        # Open memory manager
        page.click('button[title="Long-term Memory"]')
        page.wait_for_selector("text=Long-Term Memory")

        # Create multiple memories
        test_memories = ["Python programming", "Java development", "Python is great"]
        for memory in test_memories:
            page.click("text=Create New Memory")
            page.fill('textarea[placeholder*="Enter memory content"]', memory)
            page.select_option('select', 'fact')
            page.click("text=Save Memory")
            page.wait_for_selector(f"text={memory}", timeout=5000)

        # Search for "Python"
        page.fill('input[placeholder*="Search memories"]', "Python")
        page.click("text=Search")

        # Wait for search results
        page.wait_for_timeout(1000)

        # Should show 2 Python-related memories
        expect(page.locator("text=Python programming")).to_be_visible()
        expect(page.locator("text=Python is great")).to_be_visible()
        expect(page.locator("text=Java development")).not_to_be_visible()

    def test_memory_toggle_active(self, page: Page, base_url: str):
        """Test toggling memory active/inactive status."""
        # Navigate to app
        page.goto(base_url)

        # Create a new conversation
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        # Open memory manager
        page.click('button[title="Long-term Memory"]')
        page.wait_for_selector("text=Long-Term Memory")

        # Create a memory
        page.click("text=Create New Memory")
        page.fill('textarea[placeholder*="Enter memory content"]', "Test toggle")
        page.select_option('select', 'fact')
        page.click("text=Save Memory")
        page.wait_for_selector("text=Test toggle", timeout=5000)

        # Toggle to inactive (pause button)
        page.click('button[title="Deactivate"]')

        # Wait for update
        page.wait_for_timeout(500)

        # Memory should still be visible but with inactive styling
        expect(page.locator("text=Test toggle")).to_be_visible()

        # Toggle back to active (play button)
        page.click('button[title="Activate"]')

        # Wait for update
        page.wait_for_timeout(500)

        # Memory should be active
        expect(page.locator("text=Test toggle")).to_be_visible()

    def test_memory_enabled_toggle(self, page: Page, base_url: str):
        """Test the memory enabled/disabled toggle."""
        # Navigate to app
        page.goto(base_url)

        # Create a new conversation
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        # Open memory manager
        page.click('button[title="Long-term Memory"]')
        page.wait_for_selector("text=Long-Term Memory")

        # Find the memory enabled toggle
        toggle = page.locator('input[type="checkbox"]').first

        # Get initial state
        initial_state = toggle.is_checked()

        # Toggle it
        toggle.click()

        # Wait for state change
        page.wait_for_timeout(500)

        # Verify state changed
        new_state = toggle.is_checked()
        assert new_state != initial_state, "Toggle should change state"

        # Close and reopen to verify persistence
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        page.click('button[title="Long-term Memory"]')
        page.wait_for_selector("text=Long-Term Memory")

        # Check if state persisted
        toggle_after = page.locator('input[type="checkbox"]').first
        assert toggle_after.is_checked() == new_state, "State should persist"


if __name__ == "__main__":
    import sys
    pytest.main([__file__, "-v", "-s"])
