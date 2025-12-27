#!/usr/bin/env python3
"""Test current application state."""

import requests
import json
import time

def test_application():
    """Test the current state of the application."""
    print("Testing current application state...")

    # Test backend health
    print("\n1. Testing backend health...")
    try:
        response = requests.get('http://localhost:8000/health')
        print(f"Backend health: {response.json()}")
    except Exception as e:
        print(f"Backend not accessible: {e}")
        return

    # Test API docs
    print("\n2. Testing API endpoints...")
    try:
        response = requests.get('http://localhost:8000/docs')
        if response.status_code == 200:
            print("✓ API documentation accessible")
        else:
            print(f"✗ API docs not accessible: {response.status_code}")
    except Exception as e:
        print(f"✗ API docs error: {e}")

    # Test conversation creation
    print("\n3. Testing conversation creation...")
    try:
        response = requests.post('http://localhost:8000/api/conversations', json={
            'title': 'Test Conversation',
            'model': 'claude-sonnet-4-5-20250929'
        })
        if response.status_code in [200, 201]:
            conversation = response.json()
            print(f"✓ Conversation created: {conversation.get('id')}")
        else:
            print(f"✗ Conversation creation failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ Conversation creation error: {e}")

    # Test frontend accessibility
    print("\n4. Testing frontend accessibility...")
    try:
        response = requests.get('http://localhost:5173')
        if response.status_code == 200:
            print("✓ Frontend accessible")
            # Check if it's a React app
            if 'react' in response.text.lower():
                print("✓ React application detected")
            else:
                print("? Not clearly a React application")
        else:
            print(f"✗ Frontend not accessible: {response.status_code}")
    except Exception as e:
        print(f"✗ Frontend error: {e}")

    print("\n5. Testing agent endpoints...")
    try:
        response = requests.get('http://localhost:8000/api/agent')
        if response.status_code == 200:
            print("✓ Agent endpoint accessible")
        else:
            print(f"✗ Agent endpoint not accessible: {response.status_code}")
    except Exception as e:
        print(f"✗ Agent endpoint error: {e}")

if __name__ == '__main__':
    test_application()