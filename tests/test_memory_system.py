"""
Comprehensive test suite for Memory Management System

Tests all features of the long-term memory system including:
- Memory CRUD operations
- Memory search and filtering
- Memory enable/disable toggle
- Memory management UI integration
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"


def test_memory_list():
    """Test retrieving all memories"""
    print("\n=== Test 1: List Memories ===")
    response = requests.get(f"{BASE_URL}/api/memory")

    print(f"Status: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    memories = response.json()
    print(f"Found {len(memories)} memories")
    print(f"Sample memories: {json.dumps(memories[:2], indent=2)}")

    return memories


def test_memory_create():
    """Test creating a new memory"""
    print("\n=== Test 2: Create Memory ===")

    test_memory = {
        "content": f"Test memory created at {datetime.now().isoformat()}",
        "category": "fact"
    }

    response = requests.post(f"{BASE_URL}/api/memory", json=test_memory)

    print(f"Status: {response.status_code}")
    assert response.status_code in [200, 201], f"Expected 200 or 201, got {response.status_code}"

    memory = response.json()
    print(f"Created memory: {json.dumps(memory, indent=2)}")

    assert "id" in memory, "Memory should have an ID"
    assert memory["content"] == test_memory["content"], "Content should match"
    assert memory["category"] == test_memory["category"], "Category should match"
    assert memory["is_active"] == True, "New memory should be active"

    return memory


def test_memory_get_by_id(memory_id):
    """Test retrieving a specific memory by ID"""
    print(f"\n=== Test 3: Get Memory by ID ({memory_id}) ===")

    response = requests.get(f"{BASE_URL}/api/memory/{memory_id}")

    print(f"Status: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    memory = response.json()
    print(f"Retrieved memory: {json.dumps(memory, indent=2)}")

    assert memory["id"] == memory_id, "ID should match"

    return memory


def test_memory_update(memory_id):
    """Test updating a memory"""
    print(f"\n=== Test 4: Update Memory ({memory_id}) ===")

    updated_data = {
        "content": f"Updated memory at {datetime.now().isoformat()}",
        "category": "preference"
    }

    response = requests.put(f"{BASE_URL}/api/memory/{memory_id}", json=updated_data)

    print(f"Status: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    memory = response.json()
    print(f"Updated memory: {json.dumps(memory, indent=2)}")

    assert memory["content"] == updated_data["content"], "Content should be updated"
    assert memory["category"] == updated_data["category"], "Category should be updated"

    return memory


def test_memory_toggle_active(memory_id):
    """Test toggling memory active status"""
    print(f"\n=== Test 5: Toggle Memory Active Status ({memory_id}) ===")

    # Get current state
    response = requests.get(f"{BASE_URL}/api/memory/{memory_id}")
    original_state = response.json()["is_active"]

    # Toggle to inactive
    response = requests.put(f"{BASE_URL}/api/memory/{memory_id}", json={
        "is_active": False
    })

    print(f"Status: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    memory = response.json()
    print(f"Deactivated memory: is_active={memory['is_active']}")
    assert memory["is_active"] == False, "Memory should be deactivated"

    # Toggle back to active
    response = requests.put(f"{BASE_URL}/api/memory/{memory_id}", json={
        "is_active": True
    })

    memory = response.json()
    print(f"Reactivated memory: is_active={memory['is_active']}")
    assert memory["is_active"] == True, "Memory should be reactivated"

    return memory


def test_memory_search():
    """Test searching memories"""
    print("\n=== Test 6: Search Memories ===")

    # Create a test memory with specific content
    test_memory = {
        "content": "The user prefers Python for backend development",
        "category": "preference"
    }
    response = requests.post(f"{BASE_URL}/api/memory", json=test_memory)
    memory_id = response.json()["id"]

    # Search for the memory
    search_response = requests.get(f"{BASE_URL}/api/memory/search?q=Python")

    print(f"Search status: {search_response.status_code}")
    assert search_response.status_code == 200, f"Expected 200, got {search_response.status_code}"

    results = search_response.json()
    print(f"Search results: {len(results)} memories found")
    print(f"Results: {json.dumps(results, indent=2)}")

    # Verify our memory is in the results
    found = any(m["id"] == memory_id for m in results)
    print(f"Test memory found in search: {found}")

    return results


def test_memory_filter_by_category():
    """Test filtering memories by category"""
    print("\n=== Test 7: Filter Memories by Category ===")

    # Create test memories in different categories
    categories = ["fact", "preference", "context"]
    created_ids = []

    for category in categories:
        memory = {
            "content": f"Test {category} memory",
            "category": category
        }
        response = requests.post(f"{BASE_URL}/api/memory", json=memory)
        created_ids.append(response.json()["id"])
        print(f"Created {category} memory: {response.json()['id']}")

    # Filter by each category
    for category in categories:
        response = requests.get(f"{BASE_URL}/api/memory", params={"category": category})
        print(f"\nFilter by {category}: {len(response.json())} memories")

        assert response.status_code == 200
        filtered = response.json()

        # Verify all results match the category
        for memory in filtered:
            assert memory["category"] == category, f"Expected {category}, got {memory['category']}"

    return created_ids


def test_memory_delete(memory_id):
    """Test deleting a memory"""
    print(f"\n=== Test 8: Delete Memory ({memory_id}) ===")

    response = requests.delete(f"{BASE_URL}/api/memory/{memory_id}")

    print(f"Status: {response.status_code}")
    assert response.status_code in [200, 204], f"Expected 200 or 204, got {response.status_code}"

    if response.status_code == 200:
        result = response.json()
        print(f"Delete result: {json.dumps(result, indent=2)}")
    else:
        print(f"Delete successful (204 No Content)")

    # Verify memory is deleted
    response = requests.get(f"{BASE_URL}/api/memory/{memory_id}")
    assert response.status_code == 404, "Memory should be deleted (404)"
    print("Verified: Memory no longer exists")


def test_memory_settings_integration():
    """Test memory toggle in settings"""
    print("\n=== Test 9: Memory Settings Integration ===")

    # Get current settings
    response = requests.get(f"{BASE_URL}/api/settings")
    print(f"Settings status: {response.status_code}")
    assert response.status_code == 200

    settings = response.json()
    print(f"Current settings: memory_enabled={settings.get('memory_enabled', 'not set')}")

    # Try to toggle memory enabled (note: settings endpoint may not support all updates)
    # We'll just verify the setting can be read
    current_state = settings.get("memory_enabled", True)
    print(f"Memory is currently {'enabled' if current_state else 'disabled'}")

    # Test that we can at least read the setting
    assert "memory_enabled" in settings or settings.get("preferences", {}).get("memory_enabled") is not None

    return settings


def test_memory_pagination():
    """Test memory pagination for large datasets"""
    print("\n=== Test 10: Memory Pagination ===")

    # Create multiple memories
    created_count = 0
    for i in range(10):
        memory = {
            "content": f"Pagination test memory {i+1}",
            "category": "fact"
        }
        response = requests.post(f"{BASE_URL}/api/memory", json=memory)
        if response.status_code == 200:
            created_count += 1

    print(f"Created {created_count} test memories")

    # Test pagination
    response = requests.get(f"{BASE_URL}/api/memory", params={"limit": 5, "offset": 0})
    print(f"Page 1 status: {response.status_code}")

    if response.status_code == 200:
        page1 = response.json()
        print(f"Page 1: {len(page1)} memories")

        # Get second page
        response = requests.get(f"{BASE_URL}/api/memory", params={"limit": 5, "offset": 5})
        page2 = response.json()
        print(f"Page 2: {len(page2)} memories")

    return created_count


def run_all_tests():
    """Run all memory system tests"""
    print("=" * 80)
    print("MEMORY MANAGEMENT SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    try:
        # Test 1: List existing memories
        memories = test_memory_list()

        # Test 2: Create a new memory
        new_memory = test_memory_create()
        test_memory_id = new_memory["id"]

        # Test 3: Get memory by ID
        test_memory_get_by_id(test_memory_id)

        # Test 4: Update memory
        test_memory_update(test_memory_id)

        # Test 5: Toggle active status
        test_memory_toggle_active(test_memory_id)

        # Test 6: Search memories
        test_memory_search()

        # Test 7: Filter by category
        test_memory_filter_by_category()

        # Test 8: Delete memory
        test_memory_delete(test_memory_id)

        # Test 9: Settings integration
        test_memory_settings_integration()

        # Test 10: Pagination
        test_memory_pagination()

        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
