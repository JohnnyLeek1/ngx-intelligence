#!/usr/bin/env python3
"""
Test script to verify datetime serialization includes UTC 'Z' suffix.

This script tests that all datetime fields in Pydantic schemas are properly
serialized with the 'Z' suffix to indicate UTC timezone.
"""

import json
from datetime import datetime, timezone
from uuid import uuid4

# Import the schemas to test
from app.database.models import ProcessingStatus, QueueStatus, ApprovalStatus
from app.schemas.queue import QueueItemResponse
from app.schemas.document import ProcessedDocumentResponse
from app.schemas.approval import ApprovalQueueResponse


def test_queue_item_serialization():
    """Test that QueueItemResponse serializes datetimes with 'Z' suffix."""
    print("\n=== Testing QueueItemResponse ===")

    # Create a sample queue item
    queue_item = QueueItemResponse(
        id=uuid4(),
        user_id=uuid4(),
        paperless_document_id=123,
        priority=1,
        status=QueueStatus.QUEUED,
        queued_at=datetime.now(),  # Timezone-naive datetime
        started_at=None,
        completed_at=None,
        retry_count=0,
        last_error=None,
    )

    # Serialize to JSON
    json_data = queue_item.model_dump_json()
    parsed = json.loads(json_data)

    print(f"queued_at: {parsed['queued_at']}")

    # Check if 'Z' suffix is present
    assert parsed['queued_at'].endswith('Z'), "queued_at should end with 'Z'"
    print("✓ QueueItemResponse correctly serializes datetime with 'Z' suffix")

    return True


def test_processed_document_serialization():
    """Test that ProcessedDocumentResponse serializes datetimes with 'Z' suffix."""
    print("\n=== Testing ProcessedDocumentResponse ===")

    # Create a sample processed document
    doc = ProcessedDocumentResponse(
        id=uuid4(),
        user_id=uuid4(),
        paperless_document_id=456,
        processed_at=datetime.now(),  # Timezone-naive datetime
        status=ProcessingStatus.SUCCESS,
        confidence_score=0.95,
        original_data=None,
        suggested_data=None,
        applied_data=None,
        error_message=None,
        processing_time_ms=1500,
        reprocess_count=0,
    )

    # Serialize to JSON
    json_data = doc.model_dump_json()
    parsed = json.loads(json_data)

    print(f"processed_at: {parsed['processed_at']}")

    # Check if 'Z' suffix is present
    assert parsed['processed_at'].endswith('Z'), "processed_at should end with 'Z'"
    print("✓ ProcessedDocumentResponse correctly serializes datetime with 'Z' suffix")

    return True


def test_approval_queue_serialization():
    """Test that ApprovalQueueResponse serializes datetimes with 'Z' suffix."""
    print("\n=== Testing ApprovalQueueResponse ===")

    # Create a sample approval queue item
    approval = ApprovalQueueResponse(
        id=uuid4(),
        document_id=uuid4(),
        user_id=uuid4(),
        suggestions={"correspondent": "Test Corp", "tags": ["invoice"]},
        created_at=datetime.now(),  # Timezone-naive datetime
        approved_at=datetime.now(),  # Timezone-naive datetime
        feedback=None,
        status=ApprovalStatus.APPROVED,
    )

    # Serialize to JSON
    json_data = approval.model_dump_json()
    parsed = json.loads(json_data)

    print(f"created_at: {parsed['created_at']}")
    print(f"approved_at: {parsed['approved_at']}")

    # Check if 'Z' suffix is present
    assert parsed['created_at'].endswith('Z'), "created_at should end with 'Z'"
    assert parsed['approved_at'].endswith('Z'), "approved_at should end with 'Z'"
    print("✓ ApprovalQueueResponse correctly serializes datetime with 'Z' suffix")

    return True


def test_timezone_aware_datetime():
    """Test that timezone-aware datetimes are also handled correctly."""
    print("\n=== Testing timezone-aware datetime ===")

    # Create with timezone-aware datetime
    queue_item = QueueItemResponse(
        id=uuid4(),
        user_id=uuid4(),
        paperless_document_id=789,
        priority=2,
        status=QueueStatus.PROCESSING,
        queued_at=datetime.now(timezone.utc),  # Timezone-aware UTC datetime
        started_at=datetime.now(timezone.utc),
        completed_at=None,
        retry_count=1,
        last_error=None,
    )

    # Serialize to JSON
    json_data = queue_item.model_dump_json()
    parsed = json.loads(json_data)

    print(f"queued_at: {parsed['queued_at']}")
    print(f"started_at: {parsed['started_at']}")

    # Should still have timezone indicator (either 'Z' or '+00:00')
    assert parsed['queued_at'].endswith('Z') or parsed['queued_at'].endswith('+00:00'), \
        "Timezone-aware datetime should include timezone indicator"
    print("✓ Timezone-aware datetimes are correctly serialized")

    return True


def main():
    """Run all datetime serialization tests."""
    print("=" * 60)
    print("Datetime Serialization Test Suite")
    print("=" * 60)

    tests = [
        test_queue_item_serialization,
        test_processed_document_serialization,
        test_approval_queue_serialization,
        test_timezone_aware_datetime,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
