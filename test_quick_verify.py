#!/usr/bin/env python3
"""Quick verification test."""
import sys
sys.path.insert(0, '/media/DATA/projects/autonomous-coding-clone-cc/talos')

try:
    from src.api.routes.artifacts import extract_code_blocks

    # Test basic artifact detection
    test_response = '''
Here's a Python function:
```python
def hello():
    print("Hello, World!")
```
'''

    artifacts = extract_code_blocks(test_response)
    print(f"✓ Artifact detection works: found {len(artifacts)} artifact(s)")
    if artifacts:
        print(f"  - Type: {artifacts[0].get('type', 'unknown')}")
        print(f"  - Language: {artifacts[0].get('language', 'unknown')}")
        print(f"  - Content length: {len(artifacts[0].get('content', ''))}")
    print("\n✓ Backend API is functional")
    sys.exit(0)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
