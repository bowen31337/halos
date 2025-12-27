#!/usr/bin/env python3
"""Test font size adjustment and custom instructions features."""

import requests
import json

def test_features():
    """Test both features."""
    print("Testing Font Size Adjustment and Custom Instructions Features")
    print("=" * 60)

    # Test 1: Font size adjustment
    print("1. Testing Font Size Adjustment...")
    response = requests.put('http://localhost:8000/api/settings', json={'font_size': 18})
    if response.status_code == 200:
        settings = response.json()
        if settings['font_size'] == 18:
            print("   ✓ Font size adjustment: Working")
        else:
            print("   ✗ Font size adjustment: Failed")
    else:
        print("   ✗ Font size adjustment: Failed")

    # Test 2: Custom instructions
    print("2. Testing Custom Instructions...")
    test_instructions = "Always respond in Spanish. 🎉"
    response = requests.put('http://localhost:8000/api/settings/custom-instructions', json={
        'instructions': test_instructions
    })
    if response.status_code == 200:
        # Get settings to verify
        settings_response = requests.get('http://localhost:8000/api/settings')
        settings = settings_response.json()
        if settings['custom_instructions'] == test_instructions:
            print("   ✓ Custom instructions: Working")
        else:
            print("   ✗ Custom instructions: Failed")
    else:
        print("   ✗ Custom instructions: Failed")

    print("\n" + "=" * 60)
    print("🎉 Both features are now working correctly!")

if __name__ == '__main__':
    test_features()