"""UI tests for checkpoint functionality using Playwright."""

import pytest
from playwright.sync_api import Page, expect


class TestCheckpointUI:
    """Test checkpoint UI workflows."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def test_checkpoint_button_in_header(self, page: Page, base_url: str):
        """Test that checkpoint button appears in header when in a conversation."""
        # Navigate to app
        page.goto(base_url)

        # Create a new conversation
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        # Check for checkpoint button in header
        checkpoint_button = page.locator('button[title="Manage checkpoints"]')
        expect(checkpoint_button).to_be_visible()

    def test_create_checkpoint_workflow(self, page: Page, base_url: str):
        """Test creating a checkpoint through the UI."""
        # Navigate to app
        page.goto(base_url)

        # Create conversation and add messages
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        # Send a message
        page.fill('textarea[placeholder*="Message"]', "Hello, this is a test message")
        page.keyboard.press("Enter")

        # Wait for response
        page.wait_for_selector("text=Claude", timeout=10000)

        # Open checkpoint manager
        page.click('button[title="Manage checkpoints"]')
        page.wait_for_selector("text=Conversation Checkpoints")

        # Click create checkpoint button
        page.click("text=Create New Checkpoint")
        page.wait_for_selector("text=Create Checkpoint")

        # Fill in checkpoint details
        page.fill('input[placeholder*="Before major change"]', "Test Checkpoint")
        page.fill('textarea[placeholder*="Why are you saving"]', "Testing checkpoint creation")

        # Click create
        page.click("text=Create")

        # Wait for checkpoint to appear
        page.wait_for_selector("text=Test Checkpoint", timeout=5000)

        # Verify checkpoint is in the list
        expect(page.locator("text=Test Checkpoint")).to_be_visible()
        expect(page.locator("text=Testing checkpoint creation")).to_be_visible()

    def test_restore_checkpoint_workflow(self, page: Page, base_url: str):
        """Test restoring a conversation to a checkpoint."""
        # Navigate to app
        page.goto(base_url)

        # Create conversation
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        # Send multiple messages
        messages = ["First message", "Second message", "Third message"]
        for msg in messages:
            page.fill('textarea[placeholder*="Message"]', msg)
            page.keyboard.press("Enter")
            page.wait_for_selector(f"text={msg}", timeout=10000)

        # Open checkpoint manager
        page.click('button[title="Manage checkpoints"]')
        page.wait_for_selector("text=Conversation Checkpoints")

        # Create checkpoint
        page.click("text=Create New Checkpoint")
        page.fill('input[placeholder*="Before major change"]', "Restore Test")
        page.click("text=Create")
        page.wait_for_selector("text=Restore Test")

        # Add more messages after checkpoint
        page.click("text=Close")  # Close checkpoint manager
        page.fill('textarea[placeholder*="Message"]', "Fourth message after checkpoint")
        page.keyboard.press("Enter")
        page.wait_for_selector("text=Fourth message", timeout=10000)

        # Open checkpoint manager again
        page.click('button[title="Manage checkpoints"]')
        page.wait_for_selector("text=Restore Test")

        # Click restore button
        page.click("text=Restore")

        # Confirm restore
        page.wait_for_selector("text=Confirm Restore")
        page.click("text=Restore")

        # Wait for restore to complete
        page.wait_for_timeout(2000)

        # Verify restore message appears
        expect(page.locator("text=Conversation restored")).to_be_visible()

    def test_delete_checkpoint_workflow(self, page: Page, base_url: str):
        """Test deleting a checkpoint."""
        # Navigate to app
        page.goto(base_url)

        # Create conversation and message
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")
        page.fill('textarea[placeholder*="Message"]', "Test")
        page.keyboard.press("Enter")
        page.wait_for_selector("text=Claude", timeout=10000)

        # Create checkpoint
        page.click('button[title="Manage checkpoints"]')
        page.wait_for_selector("text=Conversation Checkpoints")
        page.click("text=Create New Checkpoint")
        page.fill('input[placeholder*="Before major change"]', "To Delete")
        page.click("text=Create")
        page.wait_for_selector("text=To Delete")

        # Delete checkpoint
        page.click("text=🗑")
        page.wait_for_selector("text=Confirm Delete")
        page.click("text=Delete")

        # Verify checkpoint is removed
        page.wait_for_timeout(1000)
        expect(page.locator("text=To Delete")).not_to_be_visible()

    def test_checkpoint_list_shows_message_count(self, page: Page, base_url: str):
        """Test that checkpoint list shows correct message count."""
        # Navigate to app
        page.goto(base_url)

        # Create conversation
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        # Send 2 messages
        for i in range(2):
            page.fill('textarea[placeholder*="Message"]', f"Message {i+1}")
            page.keyboard.press("Enter")
            page.wait_for_selector(f"text=Message {i+1}", timeout=10000)

        # Create checkpoint
        page.click('button[title="Manage checkpoints"]')
        page.wait_for_selector("text=Conversation Checkpoints")
        page.click("text=Create New Checkpoint")
        page.fill('input[placeholder*="Before major change"]', "2 Messages")
        page.click("text=Create")
        page.wait_for_selector("text=2 Messages")

        # Verify message count badge
        expect(page.locator("text=2 messages")).to_be_visible()

    def test_checkpoint_view_message_preview(self, page: Page, base_url: str):
        """Test viewing message preview in checkpoint."""
        # Navigate to app
        page.goto(base_url)

        # Create conversation with specific messages
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        page.fill('textarea[placeholder*="Message"]', "What is 2+2?")
        page.keyboard.press("Enter")
        page.wait_for_selector("text=What is 2+2?", timeout=10000)

        # Create checkpoint
        page.click('button[title="Manage checkpoints"]')
        page.wait_for_selector("text=Conversation Checkpoints")
        page.click("text=Create New Checkpoint")
        page.fill('input[placeholder*="Before major change"]', "Preview Test")
        page.click("text=Create")
        page.wait_for_selector("text=Preview Test")

        # Click to expand message preview
        page.click("text=View message preview")

        # Verify preview shows message content
        expect(page.locator("text=What is 2+2?")).to_be_visible()

    def test_checkpoint_error_handling(self, page: Page, base_url: str):
        """Test error handling in checkpoint operations."""
        # Navigate to app
        page.goto(base_url)

        # Create conversation
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        # Open checkpoint manager
        page.click('button[title="Manage checkpoints"]')
        page.wait_for_selector("text=Conversation Checkpoints")

        # Create checkpoint with empty form (should work with auto-name)
        page.click("text=Create New Checkpoint")
        page.click("text=Create")

        # Should succeed with auto-generated name
        page.wait_for_selector("text=Checkpoint", timeout=5000)

    def test_checkpoint_manager_closes_correctly(self, page: Page, base_url: str):
        """Test that checkpoint manager closes properly."""
        # Navigate to app
        page.goto(base_url)

        # Create conversation
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        # Open checkpoint manager
        page.click('button[title="Manage checkpoints"]')
        page.wait_for_selector("text=Conversation Checkpoints")

        # Close with X button
        page.click("text=✕")
        page.wait_for_timeout(500)

        # Verify manager is closed
        expect(page.locator("text=Conversation Checkpoints")).not_to_be_visible()

    def test_checkpoint_button_not_visible_without_conversation(self, page: Page, base_url: str):
        """Test that checkpoint button is not visible on welcome screen."""
        # Navigate to app
        page.goto(base_url)

        # Should be on welcome screen
        expect(page.locator("text=Welcome")).to_be_visible()

        # Checkpoint button should not be visible
        expect(page.locator('button[title="Manage checkpoints"]')).not_to_be_visible()

    def test_checkpoint_creation_with_notes(self, page: Page, base_url: str):
        """Test creating checkpoint with optional notes."""
        # Navigate to app
        page.goto(base_url)

        # Create conversation
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")
        page.fill('textarea[placeholder*="Message"]', "Test")
        page.keyboard.press("Enter")
        page.wait_for_selector("text=Claude", timeout=10000)

        # Open checkpoint manager
        page.click('button[title="Manage checkpoints"]')
        page.wait_for_selector("text=Conversation Checkpoints")

        # Create checkpoint with notes
        page.click("text=Create New Checkpoint")
        page.fill('input[placeholder*="Before major change"]', "With Notes")
        page.fill('textarea[placeholder*="Why are you saving"]', "Important checkpoint for later reference")
        page.click("text=Create")

        # Verify notes appear
        page.wait_for_selector("text=With Notes")
        expect(page.locator("text=Important checkpoint for later reference")).to_be_visible()

    def test_multiple_checkpoints_ordering(self, page: Page, base_url: str):
        """Test that multiple checkpoints are displayed in correct order."""
        # Navigate to app
        page.goto(base_url)

        # Create conversation
        page.click("text=New Conversation")
        page.wait_for_selector("text=Claude Sonnet")

        # Create 3 checkpoints with delays to ensure different timestamps
        for i in range(3):
            page.fill('textarea[placeholder*="Message"]', f"Message {i+1}")
            page.keyboard.press("Enter")
            page.wait_for_selector(f"text=Message {i+1}", timeout=10000)

            page.click('button[title="Manage checkpoints"]')
            page.wait_for_selector("text=Conversation Checkpoints")
            page.click("text=Create New Checkpoint")
            page.fill('input[placeholder*="Before major change"]', f"Checkpoint {i+1}")
            page.click("text=Create")
            page.wait_for_selector(f"text=Checkpoint {i+1}")

            # Close and reopen for next iteration
            page.click("text=✕")
            page.wait_for_timeout(500)

        # Open manager and verify order (newest first)
        page.click('button[title="Manage checkpoints"]')
        page.wait_for_selector("text=Conversation Checkpoints")

        # Get all checkpoint names
        checkpoint_names = page.locator("h3.font-medium").all_text_contents()
        # Should be in reverse chronological order
        assert checkpoint_names[0] == "Checkpoint 3"
        assert checkpoint_names[2] == "Checkpoint 1"
