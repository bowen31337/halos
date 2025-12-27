"""Test script to verify template API endpoints."""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_templates_api():
    """Test the templates API end-to-end."""

    async with httpx.AsyncClient() as client:
        print("=" * 80)
        print("Testing Template API")
        print("=" * 80)

        # Step 1: List templates (should be empty initially)
        print("\n[Step 1] Listing templates...")
        response = await client.get(f"{BASE_URL}/api/templates")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            templates = response.json()
            print(f"✅ Found {len(templates)} templates")
        else:
            print(f"❌ Failed: {response.text}")
            return False

        # Step 2: Create a template
        print("\n[Step 2] Creating template...")
        create_response = await client.post(
            f"{BASE_URL}/api/templates",
            json={
                "title": "Code Review Assistant",
                "description": "Helps review code for bugs and improvements",
                "category": "coding",
                "system_prompt": "You are a code review assistant. Analyze code for bugs, security issues, and improvements.",
                "initial_message": "Please review this code:",
                "model": "claude-sonnet-4-5-20250929",
                "tags": ["coding", "review"]
            }
        )
        print(f"Status: {create_response.status_code}")
        if create_response.status_code in [200, 201]:
            template = create_response.json()
            template_id = template["id"]
            print(f"✅ Created template: {template_id}")
            print(f"   Title: {template['title']}")
            print(f"   Category: {template['category']}")
        else:
            print(f"❌ Failed: {create_response.text}")
            return False

        # Step 3: Get the template
        print("\n[Step 3] Getting template...")
        get_response = await client.get(f"{BASE_URL}/api/templates/{template_id}")
        print(f"Status: {get_response.status_code}")
        if get_response.status_code == 200:
            template = get_response.json()
            print(f"✅ Retrieved template: {template['title']}")
        else:
            print(f"❌ Failed: {get_response.text}")
            return False

        # Step 4: Update the template
        print("\n[Step 4] Updating template...")
        update_response = await client.put(
            f"{BASE_URL}/api/templates/{template_id}",
            json={
                "title": "Code Review Expert",
                "description": "Expert code review assistant"
            }
        )
        print(f"Status: {update_response.status_code}")
        if update_response.status_code == 200:
            template = update_response.json()
            print(f"✅ Updated template: {template['title']}")
        else:
            print(f"❌ Failed: {update_response.text}")
            return False

        # Step 5: Use the template (increment usage)
        print("\n[Step 5] Using template...")
        use_response = await client.post(f"{BASE_URL}/api/templates/{template_id}/use")
        print(f"Status: {use_response.status_code}")
        if use_response.status_code == 200:
            template = use_response.json()
            print(f"✅ Used template. Usage count: {template['usage_count']}")
        else:
            print(f"❌ Failed: {use_response.text}")
            return False

        # Step 6: List categories
        print("\n[Step 6] Listing categories...")
        cat_response = await client.get(f"{BASE_URL}/api/templates/categories")
        print(f"Status: {cat_response.status_code}")
        if cat_response.status_code == 200:
            categories = cat_response.json()
            print(f"✅ Found {len(categories)} categories")
            for cat in categories:
                print(f"   - {cat['category']}: {cat['count']}")
        else:
            print(f"❌ Failed: {cat_response.text}")
            return False

        # Step 7: Delete the template
        print("\n[Step 7] Deleting template...")
        delete_response = await client.delete(f"{BASE_URL}/api/templates/{template_id}")
        print(f"Status: {delete_response.status_code}")
        if delete_response.status_code == 204:
            print(f"✅ Deleted template")
        else:
            print(f"❌ Failed: {delete_response.text}")
            return False

        # Step 8: Verify deletion
        print("\n[Step 8] Verifying deletion...")
        verify_response = await client.get(f"{BASE_URL}/api/templates/{template_id}")
        print(f"Status: {verify_response.status_code}")
        if verify_response.status_code == 404:
            print(f"✅ Template successfully deleted (404 response)")
        else:
            print(f"❌ Template still exists")
            return False

        print("\n" + "=" * 80)
        print("✅ ALL TEMPLATE API TESTS PASSED!")
        print("=" * 80)
        return True

if __name__ == "__main__":
    asyncio.run(test_templates_api())
