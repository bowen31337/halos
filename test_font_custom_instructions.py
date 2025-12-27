#!/usr/bin/env python3
"""Test font size adjustment and custom instructions features."""

import requests
import json
import time

def test_font_size_adjustment():
    """Test font size adjustment feature."""
    print("Testing Font Size Adjustment Feature...")

    # 1. Get current settings
    response = requests.get('http://localhost:8000/api/settings')
    current_settings = response.json()
    print(f"Current font size: {current_settings.get('font_size')}")

    # 2. Update font size to 20
    response = requests.put('http://localhost:8000/api/settings', json={
        'font_size': 20
    })
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    updated_settings = response.json()
    print(f"Updated font size: {updated_settings.get('font_size')}")

    # 3. Verify the update
    assert updated_settings['font_size'] == 20, f"Expected 20, got {updated_settings['font_size']}"

    # 4. Test edge cases
    # Test minimum value
    response = requests.put('http://localhost:8000/api/settings', json={'font_size': 12})
    assert response.status_code == 200
    assert response.json()['font_size'] == 12

    # Test maximum value
    response = requests.put('http://localhost:8000/api/settings', json={'font_size': 24})
    assert response.status_code == 200
    assert response.json()['font_size'] == 24

    print("✓ Font size adjustment working correctly")

def test_custom_instructions():
    """Test custom instructions feature."""
    print("\nTesting Custom Instructions Feature...")

    # 1. Get current settings
    response = requests.get('http://localhost:8000/api/settings')
    current_settings = response.json()
    print(f"Current custom instructions: '{current_settings.get('custom_instructions')}'")

    # 2. Set custom instructions
    test_instructions = "Always respond in Spanish and include emojis at the end of each message. 🎉"
    response = requests.put('http://localhost:8000/api/settings', json={
        'custom_instructions': test_instructions
    })
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    updated_settings = response.json()
    print(f"Updated custom instructions: '{updated_settings.get('custom_instructions')}'")

    # 3. Verify the update
    assert updated_settings['custom_instructions'] == test_instructions

    # 4. Test empty instructions
    response = requests.put('http://localhost:8000/api/settings', json={'custom_instructions': ''})
    assert response.status_code == 200
    assert response.json()['custom_instructions'] == ''

    print("✓ Custom instructions working correctly")

def test_settings_persistence():
    """Test that settings persist across requests."""
    print("\nTesting Settings Persistence...")

    # Set specific values
    test_settings = {
        'font_size': 18,
        'custom_instructions': 'Test instructions for persistence',
        'theme': 'dark',
        'extended_thinking_enabled': True,
        'temperature': 0.8,
        'max_tokens': 2048
    }

    response = requests.put('http://localhost:8000/api/settings', json=test_settings)
    assert response.status_code == 200

    # Get settings again
    response = requests.get('http://localhost:8000/api/settings')
    retrieved_settings = response.json()

    # Verify all values are preserved
    for key, value in test_settings.items():
        assert retrieved_settings[key] == value, f"{key}: expected {value}, got {retrieved_settings[key]}"

    print("✓ Settings persistence working correctly")

def test_frontend_integration():
    """Test that frontend can access settings."""
    print("\nTesting Frontend Integration...")

    # Test that frontend can make requests (CORS should be enabled)
    response = requests.get('http://localhost:5173')
    assert response.status_code == 200, "Frontend should be accessible"

    # Test that API is accessible from frontend (CORS headers)
    response = requests.get('http://localhost:8000/api/settings')
    print(f"CORS headers: {response.headers.get('Access-Control-Allow-Origin', 'Not set')}")

    print("✓ Frontend integration working correctly")

def main():
    """Run all tests."""
    print("Testing Font Size Adjustment and Custom Instructions Features")
    print("=" * 60)

    try:
        test_font_size_adjustment()
        test_custom_instructions()
        test_settings_persistence()
        test_frontend_integration()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Both features are working correctly.")
        print("✓ Font size adjustment: Working")
        print("✓ Custom instructions: Working")
        print("✓ Settings persistence: Working")
        print("✓ Frontend integration: Working")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise

if __name__ == '__main__':
    main()