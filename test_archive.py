#!/usr/bin/env python3
"""Test script for archive feature"""

import urllib.request
import json

def test_archive_feature():
    """Test the archive conversation feature"""
    print("=== Testing Archive Feature ===\n")

    # 1. Create a test conversation
    print("1. Creating a test conversation...")
    data = json.dumps({'title': 'Archive Test Conversation'}).encode('utf-8')
    req = urllib.request.Request('http://localhost:8000/api/conversations', data=data, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    conv = json.loads(resp.read().decode())
    conv_id = conv['id']
    print(f"   Created: {conv['title']} (ID: {conv_id})")
    print(f"   is_archived: {conv['is_archived']}")
    assert conv['is_archived'] == False, "New conversation should not be archived"
    print("   ✓ PASS")

    # 2. Archive the conversation
    print("\n2. Archiving the conversation...")
    update_data = json.dumps({'is_archived': True}).encode('utf-8')
    update_req = urllib.request.Request(f'http://localhost:8000/api/conversations/{conv_id}', data=update_data, method='PUT', headers={'Content-Type': 'application/json'})
    update_resp = urllib.request.urlopen(update_req)
    updated = json.loads(update_resp.read().decode())
    print(f"   Updated: {updated['title']}")
    print(f"   is_archived: {updated['is_archived']}")
    assert updated['is_archived'] == True, "Conversation should be archived"
    print("   ✓ PASS")

    # 3. Get all conversations (should not show archived by default)
    print("\n3. Getting all conversations (default - active only)...")
    all_req = urllib.request.urlopen('http://localhost:8000/api/conversations')
    all_convos = json.loads(all_req.read().decode())
    found = [c for c in all_convos if c['id'] == conv_id]
    print(f"   Found our conversation: {len(found) > 0}")
    assert len(found) == 0, "Archived conversation should not appear in default list"
    print("   ✓ PASS")

    # 4. Get archived conversations
    print("\n4. Getting archived conversations...")
    archived_req = urllib.request.urlopen('http://localhost:8000/api/conversations?archived=true')
    archived_convos = json.loads(archived_req.read().decode())
    found_archived = [c for c in archived_convos if c['id'] == conv_id]
    print(f"   Found our conversation: {len(found_archived) > 0}")
    assert len(found_archived) == 1, "Archived conversation should appear in archived list"
    print("   ✓ PASS")

    # 5. Unarchive the conversation
    print("\n5. Unarchiving the conversation...")
    unarchive_data = json.dumps({'is_archived': False}).encode('utf-8')
    unarchive_req = urllib.request.Request(f'http://localhost:8000/api/conversations/{conv_id}', data=unarchive_data, method='PUT', headers={'Content-Type': 'application/json'})
    unarchive_resp = urllib.request.urlopen(unarchive_req)
    unarchived = json.loads(unarchive_resp.read().decode())
    print(f"   Updated: {unarchived['title']}")
    print(f"   is_archived: {unarchived['is_archived']}")
    assert unarchived['is_archived'] == False, "Conversation should be unarchived"
    print("   ✓ PASS")

    # 6. Verify it's back in active list
    print("\n6. Verifying conversation is back in active list...")
    active_req = urllib.request.urlopen('http://localhost:8000/api/conversations')
    active_convos = json.loads(active_req.read().decode())
    found_active = [c for c in active_convos if c['id'] == conv_id]
    print(f"   Found our conversation: {len(found_active) > 0}")
    assert len(found_active) == 1, "Unarchived conversation should appear in active list"
    print("   ✓ PASS")

    # 7. Cleanup
    print("\n7. Cleaning up...")
    delete_req = urllib.request.Request(f'http://localhost:8000/api/conversations/{conv_id}', method='DELETE')
    urllib.request.urlopen(delete_req)
    print("   Test conversation deleted")
    print("   ✓ PASS")

    print("\n=== All Tests Passed! ===")
    return True

if __name__ == '__main__':
    test_archive_feature()
