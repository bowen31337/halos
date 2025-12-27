"""Simple test for image upload feature without external dependencies."""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import httpx


async def create_simple_test_image():
    """Create a minimal PNG file using raw bytes."""
    # Minimal 1x1 red PNG
    png_bytes = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x05, 0xFE,
        0xD4, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
        0x44, 0xAE, 0x42, 0x60, 0x82
    ])
    return png_bytes


async def test_image_upload_api():
    """Test the image upload API endpoint."""

    print("Testing image upload API...")

    # Create test image
    test_image = await create_simple_test_image()
    print(f"Created test image: {len(test_image)} bytes")

    async with httpx.AsyncClient() as client:
        # Test 1: Upload image
        print("\n1. Testing image upload endpoint...")
        files = {'file': ('test.png', test_image, 'image/png')}
        try:
            response = await client.post('http://localhost:8000/api/messages/upload-image', files=files)
            if response.status_code == 201:
                upload_data = response.json()
                image_url = upload_data['url']
                print(f"   ✓ Image uploaded successfully: {image_url}")
            else:
                print(f"   ✗ Upload failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"   ✗ Upload error: {e}")
            return False

        # Test 2: Create conversation
        print("\n2. Testing conversation creation...")
        try:
            response = await client.post(
                'http://localhost:8000/api/conversations',
                json={'title': 'Image Test Conversation'}
            )
            if response.status_code == 201:
                conv_data = response.json()
                conv_id = conv_data['id']
                print(f"   ✓ Conversation created: {conv_id}")
            else:
                print(f"   ✗ Conversation creation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ✗ Conversation error: {e}")
            return False

        # Test 3: Create message with attachment
        print("\n3. Testing message creation with attachment...")
        try:
            response = await client.post(
                f'http://localhost:8000/api/messages/conversations/{conv_id}/messages',
                json={
                    'role': 'user',
                    'content': 'What is in this image?',
                    'attachments': [image_url]
                }
            )
            if response.status_code == 201:
                msg_data = response.json()
                print(f"   ✓ Message created with attachment")
                print(f"   Message ID: {msg_data['id']}")
                print(f"   Content: {msg_data['content']}")
                print(f"   Attachments: {msg_data['attachments']}")
            else:
                print(f"   ✗ Message creation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ✗ Message error: {e}")
            return False

        # Test 4: Retrieve messages and verify attachment
        print("\n4. Testing message retrieval...")
        try:
            response = await client.get(
                f'http://localhost:8000/api/messages/conversations/{conv_id}/messages'
            )
            if response.status_code == 200:
                messages = response.json()
                print(f"   ✓ Retrieved {len(messages)} message(s)")

                # Verify the message has attachment
                user_msg = messages[0]
                if user_msg.get('attachments') == [image_url]:
                    print(f"   ✓ Attachment correctly stored and retrieved")
                else:
                    print(f"   ✗ Attachment mismatch: {user_msg.get('attachments')}")
                    return False
            else:
                print(f"   ✗ Message retrieval failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ✗ Retrieval error: {e}")
            return False

        # Test 5: Verify image can be served
        print("\n5. Testing image serving...")
        try:
            response = await client.get(f'http://localhost:8000{image_url}')
            if response.status_code == 200:
                print(f"   ✓ Image served successfully ({len(response.content)} bytes)")
            else:
                print(f"   ✗ Image serving failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ✗ Image serving error: {e}")
            return False

        print("\n=== ALL API TESTS PASSED ===")
        return True


async def test_frontend_code_structure():
    """Verify frontend code has the required components."""

    print("\n\nVerifying frontend code structure...")

    # Check Message interface has attachments
    store_file = Path('/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/stores/conversationStore.ts')
    if store_file.exists():
        content = store_file.read_text()
        if 'attachments?: string[]' in content:
            print("   ✓ Message interface has attachments field")
        else:
            print("   ✗ Message interface missing attachments field")
            return False
    else:
        print("   ✗ conversationStore.ts not found")
        return False

    # Check ChatInput has image handling
    chat_input_file = Path('/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/ChatInput.tsx')
    if chat_input_file.exists():
        content = chat_input_file.read_text()
        checks = [
            ('handleFileSelect', 'File select handler'),
            ('handleFileChange', 'File change handler'),
            ('handlePaste', 'Paste handler'),
            ('images', 'Image state'),
            ('removeImage', 'Remove image handler'),
            ('upload-image', 'Upload API call'),
        ]

        all_passed = True
        for check, desc in checks:
            if check in content:
                print(f"   ✓ {desc} found")
            else:
                print(f"   ✗ {desc} missing")
                all_passed = False
        if not all_passed:
            return False
    else:
        print("   ✗ ChatInput.tsx not found")
        return False

    # Check MessageBubble has image display
    bubble_file = Path('/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/MessageBubble.tsx')
    if bubble_file.exists():
        content = bubble_file.read_text()
        if 'message.attachments' in content:
            print("   ✓ MessageBubble handles attachments")
        else:
            print("   ✗ MessageBubble missing attachment handling")
            return False
    else:
        print("   ✗ MessageBubble.tsx not found")
        return False

    # Check API service has attachments support
    api_file = Path('/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/services/api.ts')
    if api_file.exists():
        content = api_file.read_text()
        if 'attachments?: string[]' in content:
            print("   ✓ API service supports attachments")
        else:
            print("   ✗ API service missing attachments support")
            return False
    else:
        print("   ✗ api.ts not found")
        return False

    print("\n=== FRONTEND CODE VERIFICATION PASSED ===")
    return True


async def main():
    """Run all tests."""

    print("=" * 60)
    print("IMAGE UPLOAD FEATURE TEST SUITE")
    print("=" * 60)

    # Check backend is running
    print("\nChecking backend status...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                print("   ✓ Backend is running")
            else:
                print("   ✗ Backend not responding correctly")
                return False
    except Exception as e:
        print(f"   ✗ Backend is not running on port 8000: {e}")
        return False

    # Run API tests
    api_passed = await test_image_upload_api()

    # Run frontend verification
    frontend_passed = await test_frontend_code_structure()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"API Tests: {'PASSED' if api_passed else 'FAILED'}")
    print(f"Frontend Code: {'PASSED' if frontend_passed else 'FAILED'}")

    if api_passed and frontend_passed:
        print("\n🎉 ALL TESTS PASSED - Image upload feature is working!")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
