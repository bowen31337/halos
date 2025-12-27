#!/usr/bin/env python3
"""Simple test script for image upload functionality."""

import urllib.request
import json
import tempfile
import os

# Backend URL
BACKEND_URL = "http://localhost:8000"

def create_simple_png() -> str:
    """Create a minimal 1x1 PNG file."""
    # A minimal 1x1 red PNG (8-bit PNG)
    png_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0'
        b'\x00\x00\x00\x03\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    # Write to temp file
    fd, path = tempfile.mkstemp(suffix='.png')
    with os.fdopen(fd, 'wb') as f:
        f.write(png_data)

    return path

def test_upload_image(image_path: str) -> dict:
    """Test uploading an image via the API."""
    print("Testing image upload endpoint...")

    with open(image_path, 'rb') as f:
        image_data = f.read()

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

    # Create test image
    print("\nCreating test image...")
    image_path = create_simple_png()
    print(f"✓ Test image created at {image_path}")

    try:
        # Test 1: Upload image
        upload_result = test_upload_image(image_path)

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
    finally:
        # Cleanup
        if os.path.exists(image_path):
            os.unlink(image_path)
            print(f"\n✓ Cleaned up test image")

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
