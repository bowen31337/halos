"""Simple test for batch API using existing database."""
import sys
sys.path.insert(0, '/media/DATA/projects/autonomous-coding-clone-cc/talos')

from src.api.routes.batch import BatchOperationRequest, BatchOperationResponse
from src.models.audit_log import AuditAction
import json

# Test that the models are properly defined
print("Testing Batch API Models\n")
print("=" * 60)

# Test 1: Check request model
print("\n1. Testing BatchOperationRequest model...")
try:
    req = BatchOperationRequest(
        conversation_ids=["12345678-1234-5678-1234-567812345678"],
        operation="archive"
    )
    print(f"✓ BatchOperationRequest created")
    print(f"  - Operation: {req.operation}")
    print(f"  - Conversation IDs: {len(req.conversation_ids)}")
except Exception as e:
    print(f"✗ Error creating request: {e}")

# Test 2: Check response model
print("\n2. Testing BatchOperationResponse model...")
try:
    from datetime import datetime
    resp = BatchOperationResponse(
        success=True,
        operation="archive",
        total_requested=1,
        total_processed=1,
        successful=["12345678-1234-5678-1234-567812345678"],
        failed=[],
        started_at=datetime.now(),
        completed_at=datetime.now(),
        processing_time_seconds=0.5
    )
    print(f"✓ BatchOperationResponse created")
    print(f"  - Success: {resp.success}")
    print(f"  - Operation: {resp.operation}")
except Exception as e:
    print(f"✗ Error creating response: {e}")

# Test 3: Check audit actions
print("\n3. Testing audit actions...")
try:
    batch_op = AuditAction.BATCH_OPERATION
    batch_export = AuditAction.BATCH_EXPORT
    print(f"✓ Audit actions exist")
    print(f"  - BATCH_OPERATION: {batch_op.value}")
    print(f"  - BATCH_EXPORT: {batch_export.value}")
except Exception as e:
    print(f"✗ Error with audit actions: {e}")

print("\n" + "=" * 60)
print("Model Tests Complete!")
