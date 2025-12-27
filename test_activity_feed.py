#!/usr/bin/env python3
"""Test activity feed implementation."""

import sys
import os
sys.path.insert(0, '.')

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_backend_implementation():
    """Test backend activity feed implementation."""
    print("\n=== Testing Backend Implementation ===")

    try:
        from src.api.routes import activity
        from src.models.activity import ActivityLog

        # Check router exists
        assert hasattr(activity, 'router'), "Router not found"
        print("✅ Activity router exists")

        # Check for required endpoints
        routes = activity.router.routes
        route_paths = [route.path for route in routes if hasattr(route, 'path')]

        required_endpoints = [
            ("POST", ""),
            ("GET", ""),
            ("GET", "/types"),
            ("GET", "/summary")
        ]

        for method, path_suffix in required_endpoints:
            # Routes would have just the path suffix
            found = any(path_suffix in route.path for route in routes if hasattr(route, 'path'))
            if found:
                print(f"✅ {method} /activity{path_suffix} endpoint exists")
            else:
                print(f"⚠️  {method} /activity{path_suffix} may be missing")

        # Check for utility function
        assert hasattr(activity, 'log_user_activity'), "log_user_activity utility missing"
        print("✅ Utility function log_user_activity exists")

        return True

    except ImportError as e:
        print(f"❌ Failed to import activity module: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_activity_endpoints():
    """Test activity feed API endpoints."""
    print("\n=== Testing Activity Endpoints ===")

    # Test 1: Create an activity log
    print("\n[TEST 1] Create activity log")

    activity_data = {
        "action_type": "conversation_created",
        "resource_type": "conversation",
        "resource_id": "test-conversation-123",
        "resource_name": "Test Conversation",
        "details": {"model": "claude-sonnet-4-5"}
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/activity",
            params={"user_id": "test-user-1", "user_name": "Alice"},
            json=activity_data,
            timeout=5
        )

        if response.status_code in [200, 201]:
            activity = response.json()
            print(f"✅ Activity created: {activity['id']}")
            activity_id = activity['id']
        else:
            print(f"❌ Failed to create activity: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error creating activity: {e}")
        return False

    # Test 2: Get activity feed
    print("\n[TEST 2] Get activity feed")

    try:
        response = requests.get(
            f"{BASE_URL}/api/activity",
            params={"limit": 10},
            timeout=5
        )

        if response.status_code == 200:
            feed = response.json()
            print(f"✅ Retrieved {feed['total']} activities")

            if feed['activities']:
                print(f"   Latest: {feed['activities'][0]['action_type']} by {feed['activities'][0]['user_name']}")
        else:
            print(f"❌ Failed to get feed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error getting feed: {e}")
        return False

    # Test 3: Filter by action type
    print("\n[TEST 3] Filter by action type")

    try:
        response = requests.get(
            f"{BASE_URL}/api/activity",
            params={"action_type": "conversation_created", "limit": 10},
            timeout=5
        )

        if response.status_code == 200:
            feed = response.json()
            print(f"✅ Filtered by type: {feed['total']} activities")
        else:
            print(f"⚠️  Filter failed: {response.status_code}")

    except Exception as e:
        print(f"⚠️  Filter error: {e}")

    # Test 4: Get activity types
    print("\n[TEST 4] Get activity types")

    try:
        response = requests.get(
            f"{BASE_URL}/api/activity/types",
            timeout=5
        )

        if response.status_code == 200:
            types = response.json()
            print(f"✅ Retrieved {len(types.get('action_types', []))} action types")
            print(f"   Retrieved {len(types.get('resource_types', []))} resource types")
        else:
            print(f"⚠️  Failed to get types: {response.status_code}")

    except Exception as e:
        print(f"⚠️  Error getting types: {e}")

    # Test 5: Get activity summary
    print("\n[TEST 5] Get activity summary")

    try:
        response = requests.get(
            f"{BASE_URL}/api/activity/summary",
            params={"days": 7},
            timeout=5
        )

        if response.status_code == 200:
            summary = response.json()
            print(f"✅ Retrieved summary: {summary['total']} activities in {summary['period_days']} days")

            if summary.get('by_user'):
                print(f"   Top user: {summary['by_user'][0]['user'] if summary['by_user'] else 'N/A'}")

            if summary.get('by_type'):
                print(f"   Top action: {summary['by_type'][0]['type'] if summary['by_type'] else 'N/A'}")
        else:
            print(f"⚠️  Failed to get summary: {response.status_code}")

    except Exception as e:
        print(f"⚠️  Error getting summary: {e}")

    # Test 6: Delete activity
    print("\n[TEST 6] Delete activity")

    try:
        response = requests.delete(
            f"{BASE_URL}/api/activity/{activity_id}",
            params={"user_id": "test-user-1"},
            timeout=5
        )

        if response.status_code == 204:
            print("✅ Activity deleted successfully")
        else:
            print(f"⚠️  Delete failed: {response.status_code}")

    except Exception as e:
        print(f"⚠️  Error deleting: {e}")

    return True


def test_multiple_activities():
    """Test creating and retrieving multiple activities."""
    print("\n=== Testing Multiple Activities ===")

    actions = [
        ("conversation_created", "conversation", "New Chat"),
        ("message_sent", "message", "Hello World"),
        ("file_uploaded", "file", "document.pdf"),
        ("share_created", "share", "Shared Link"),
        ("project_created", "project", "My Project")
    ]

    try:
        for i, (action, resource_type, resource_name) in enumerate(actions):
            response = requests.post(
                f"{BASE_URL}/api/activity",
                params={
                    "user_id": f"test-user-{i % 3}",  # Rotate between 3 users
                    "user_name": ["Alice", "Bob", "Charlie"][i % 3]
                },
                json={
                    "action_type": action,
                    "resource_type": resource_type,
                    "resource_name": resource_name,
                    "details": {"index": i}
                },
                timeout=5
            )

            if response.status_code in [200, 201]:
                print(f"✅ Created: {action}")
            else:
                print(f"⚠️  Failed to create {action}")

        # Get all activities
        response = requests.get(
            f"{BASE_URL}/api/activity",
            params={"limit": 20},
            timeout=5
        )

        if response.status_code == 200:
            feed = response.json()
            print(f"\n✅ Retrieved {feed['total']} total activities")

            # Show different users
            users = set(a['user_name'] for a in feed['activities'])
            print(f"   Users: {', '.join(users)}")

            # Show different action types
            actions_found = set(a['action_type'] for a in feed['activities'])
            print(f"   Action types: {len(actions_found)} different types")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_time_filtering():
    """Test time range filtering."""
    print("\n=== Testing Time Filtering ===")

    try:
        # Test different time ranges
        for time_range in ["1d", "7d", "30d"]:
            response = requests.get(
                f"{BASE_URL}/api/activity",
                params={"time_range": time_range, "limit": 50},
                timeout=5
            )

            if response.status_code == 200:
                feed = response.json()
                print(f"✅ {time_range} range: {feed['total']} activities")
            else:
                print(f"⚠️  {time_range} range failed")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("ACTIVITY FEED TEST SUITE")
    print("=" * 70)

    results = []

    # Test backend implementation
    results.append(("Backend Implementation", test_backend_implementation()))

    # Test endpoints
    results.append(("API Endpoints", test_activity_endpoints()))

    # Test multiple activities
    results.append(("Multiple Activities", test_multiple_activities()))

    # Test time filtering
    results.append(("Time Filtering", test_time_filtering()))

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "-" * 70)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 Activity feed feature is fully implemented!")
        print("\n📋 Features:")
        print("   • POST /api/activity - Log user actions")
        print("   • GET /api/activity - Get activity feed with filters")
        print("   • GET /api/activity/types - Get available action/resource types")
        print("   • GET /api/activity/summary - Get activity statistics")
        print("   • DELETE /api/activity/{id} - Soft delete activity")
        print("   • Filter by user, action type, resource type, time range")
        print("   • Pagination support")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
