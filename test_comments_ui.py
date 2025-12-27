"""Test the comments feature in the browser UI."""

import asyncio
from playwright.async_api import async_playwright
import httpx
import uuid

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

async def setup_test_data():
    """Create test conversation with messages."""
    async with httpx.AsyncClient() as client:
        # Create conversation
        response = await client.post(f"{BASE_URL}/api/conversations", json={
            "title": "UI Test - Comments Feature",
            "model": "claude-sonnet-4-5-20250929"
        })
        conversation = response.json()
        conversation_id = conversation["id"]

        # Create a message directly
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from src.models import Message, Conversation
        from src.core.config import settings
        from sqlalchemy import select

        engine = create_async_engine(settings.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role="assistant",
                content="This is a test message for the comments feature. Please add comments to test the UI!"
            )
            session.add(message)
            await session.commit()

            # Update conversation
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conv = result.scalar_one_or_none()
            if conv:
                conv.message_count = 1
                conv.last_message_at = message.created_at
                await session.commit()

            message_id = message.id

        # Share with comments enabled
        response = await client.post(
            f"{BASE_URL}/api/conversations/{conversation_id}/share",
            json={
                "access_level": "read",
                "allow_comments": True,
                "expires_in_days": 7
            }
        )
        shared = response.json()

        return {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "share_token": shared["share_token"],
            "title": conversation["title"]
        }

async def test_comments_ui():
    """Test the comments feature in the browser."""
    print("=" * 60)
    print("Testing Comments UI in Browser")
    print("=" * 60)

    # Setup test data
    print("\n📝 Setting up test data...")
    test_data = await setup_test_data()
    share_token = test_data["share_token"]
    share_url = f"{FRONTEND_URL}/share/{share_token}"
    print(f"✓ Share URL: {share_url}")

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        try:
            # Step 1: Navigate to shared conversation
            print(f"\n🌐 Step 1: Navigating to shared conversation...")
            await page.goto(share_url)
            await page.wait_for_load_state("networkidle")
            print("✓ Page loaded")

            # Step 2: Verify the conversation is displayed
            print("\n📋 Step 2: Verifying conversation display...")
            title = await page.locator("h1").text_content()
            print(f"✓ Title: {title}")
            assert test_data["title"] in title

            # Step 3: Check if comments section is visible
            print("\n💬 Step 3: Checking for comments section...")
            # Look for the comments area
            comments_input = page.locator("input[placeholder*='comment' i]").first
            await comments_input.wait_for(state="visible", timeout=5000)
            print("✓ Comments input is visible")

            # Step 4: Add a comment
            print("\n✍️ Step 4: Adding a comment...")
            await comments_input.fill("This is a UI test comment!")
            await page.keyboard.press("Enter")
            print("✓ Comment submitted")

            # Wait for comment to appear
            await page.wait_for_selector("text=This is a UI test comment!", timeout=3000)
            print("✓ Comment appeared in UI")

            # Step 5: Verify comment is displayed
            print("\n👁️ Step 5: Verifying comment display...")
            comment_text = await page.locator("text=This is a UI test comment!").text_content()
            print(f"✓ Comment visible: {comment_text}")

            # Step 6: Test reply button
            print("\n↩️ Step 6: Testing reply functionality...")
            reply_button = page.locator("button:has-text('Reply')").first
            await reply_button.click()
            print("✓ Reply button clicked")

            # Step 7: Add a reply
            print("\n💭 Step 7: Adding a reply...")
            reply_input = page.locator("input[placeholder*='reply' i]").first
            await reply_input.wait_for(state="visible")
            await reply_input.fill("This is a reply from UI!")
            await page.keyboard.press("Enter")
            print("✓ Reply submitted")

            # Wait for reply to appear
            await page.wait_for_selector("text=This is a reply from UI!", timeout=3000)
            print("✓ Reply appeared in UI")

            # Step 8: Take a screenshot
            print("\n📸 Step 8: Taking screenshot...")
            await page.screenshot(path="test_comments_ui.png", full_page=True)
            print("✓ Screenshot saved to test_comments_ui.png")

            # Step 9: Test delete button
            print("\n🗑️ Step 9: Testing delete functionality...")
            delete_button = page.locator("button:has-text('Delete')").first
            await delete_button.click()
            # Handle confirmation dialog if present
            try:
                await page.wait_for_selector("text=Delete this comment?", timeout=1000)
                await page.keyboard.press("Enter")
            except:
                pass
            print("✓ Delete clicked")

            # Step 10: Verify comments via API
            print("\n🔍 Step 10: Verifying via API...")
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BASE_URL}/api/comments/shared/{share_token}/comments"
                )
                comments = response.json()
                print(f"✓ API confirms {len(comments)} comment(s)")

            print("\n" + "=" * 60)
            print("✅ All UI tests passed!")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path="test_comments_error.png", full_page=True)
            print("Error screenshot saved to test_comments_error.png")

        finally:
            await browser.close()

    # Cleanup
    print("\n🧹 Cleaning up...")
    async with httpx.AsyncClient() as client:
        await client.delete(f"{BASE_URL}/api/conversations/{test_data['conversation_id']}")
        print("✓ Test conversation deleted")

if __name__ == "__main__":
    asyncio.run(test_comments_ui())
