#!/usr/bin/env python3
"""Test script for image upload functionality."""

import urllib.request
import io
import json
import base64
from PIL import Image
from typing import Dict, Any

# Backend URL
BACKEND_URL = "http://localhost:8000"

def create_test_image() -> bytes:
    """Create a simple test image in memory."""
    # Create a small test image (100x100 red square)
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    return img_bytes.getvalue()

def test_upload_image() -> Dict[str, Any]:
    """Test uploading an image via the API."""
    print("Testing image upload endpoint...")

    # Create test image
    image_data = create_test_image()

    # Prepare multipart form data
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = (
        f'------{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="test_image.png"\r\n'
        f'Content-Type: image/png\r\n'
        f'\r\n'
    ).encode()

    body += image_data
    body += f'\r\n------{boundary}--\r\n'.encode()

    # Create request
    req = urllib.request.Request(
        f'{BACKEND_URL}/api/messages/upload-image',
        data=body,
        method='POST'
    )
    req.add_header('Content-Type', f'multipart/form-data; boundary=----{boundary}')

    try:
        response = urllib.request.urlopen(req, timeout=10)
        result = json.loads(response.read().decode())

        print(f"✓ Upload successful!")
        print(f"  URL: {result['url']}")
        print(f"  Filename: {result['filename']}")
        print(f"  Size: {result['size']} bytes")

        return result
    except urllib.error.HTTPError as e:
        print(f"✗ Upload failed with HTTP {e.code}: {e.read().decode()}")
        return None
    except Exception as e:
        print(f"✗ Upload failed: {e}")
        return None

def test_serve_image(filename: str) -> bool:
    """Test serving an uploaded image."""
    print(f"\nTesting image serving for {filename}...")

    try:
        response = urllib.request.urlopen(
            f'{BACKEND_URL}/api/messages/images/{filename}',
            timeout=10
        )
        image_data = response.read()

        print(f"✓ Image served successfully!")
        print(f"  Size: {len(image_data)} bytes")
        print(f"  Content-Type: {response.headers.get('Content-Type')}")

        return True
    except Exception as e:
        print(f"✗ Failed to serve image: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Image Upload Functionality Tests")
    print("=" * 60)

    # Test 1: Upload image
    upload_result = test_upload_image()

    if not upload_result:
        print("\n✗ Cannot proceed with further tests without successful upload")
        return False

    # Test 2: Serve image
    filename = upload_result['filename'].split('/')[-1]
    serve_success = test_serve_image(filename)

    print("\n" + "=" * 60)
    if upload_result and serve_success:
        print("✓ All tests passed!")
        print("=" * 60)
        return True
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
