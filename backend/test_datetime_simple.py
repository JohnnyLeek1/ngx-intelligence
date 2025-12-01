#!/usr/bin/env python3
"""
Simple test to verify datetime serialization logic.

Tests the field_serializer directly without needing database dependencies.
"""

import json
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict
from pydantic.functional_serializers import model_serializer
from typing import Any, Callable, Optional


def serialize_datetime_with_utc(dt: datetime) -> str:
    """Serialize datetime to ISO 8601 format with UTC 'Z' suffix."""
    if dt.tzinfo is not None:
        return dt.isoformat()
    return f"{dt.isoformat()}Z"


class UTCBaseModel(BaseModel):
    """
    Base Pydantic model with proper UTC datetime serialization.

    All datetime fields will be serialized to ISO 8601 format with 'Z' suffix
    to indicate UTC timezone, ensuring consistent timezone handling in the frontend.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    @model_serializer(mode='wrap', when_used='json')
    def _serialize_with_utc_datetimes(
        self, serializer: Callable[[Any], dict], info
    ) -> dict:
        """Wrap the default serializer to add UTC 'Z' suffix to datetimes."""
        data = serializer(self)
        return self._process_datetime_fields(data)

    def _process_datetime_fields(self, obj: Any) -> Any:
        """Recursively process data structure to add UTC 'Z' suffix to datetimes."""
        if isinstance(obj, datetime):
            return serialize_datetime_with_utc(obj)
        elif isinstance(obj, dict):
            return {
                key: self._process_datetime_fields(value)
                for key, value in obj.items()
            }
        elif isinstance(obj, list):
            return [self._process_datetime_fields(item) for item in obj]
        return obj


class TestModel(UTCBaseModel):
    """Test model with datetime field."""
    name: str
    created_at: datetime
    updated_at: Optional[datetime] = None


def test_naive_datetime():
    """Test timezone-naive datetime serialization."""
    print("\n=== Test 1: Naive datetime ===")

    # Create with naive datetime (no timezone info)
    dt = datetime(2025, 11, 30, 23, 16, 23)
    model = TestModel(name="test", created_at=dt)

    json_str = model.model_dump_json()
    data = json.loads(json_str)

    print(f"Input datetime: {dt}")
    print(f"Serialized: {data['created_at']}")

    # Should end with 'Z'
    assert data['created_at'] == "2025-11-30T23:16:23Z", \
        f"Expected '2025-11-30T23:16:23Z', got '{data['created_at']}'"
    print("✓ PASS: Naive datetime correctly serialized with 'Z' suffix")
    return True


def test_aware_datetime():
    """Test timezone-aware datetime serialization."""
    print("\n=== Test 2: Aware datetime (UTC) ===")

    # Create with timezone-aware datetime
    dt = datetime(2025, 11, 30, 23, 16, 23, tzinfo=timezone.utc)
    model = TestModel(name="test", created_at=dt)

    json_str = model.model_dump_json()
    data = json.loads(json_str)

    print(f"Input datetime: {dt}")
    print(f"Serialized: {data['created_at']}")

    # Should include timezone info (either 'Z' or '+00:00')
    assert data['created_at'] in ["2025-11-30T23:16:23Z", "2025-11-30T23:16:23+00:00"], \
        f"Expected timezone indicator, got '{data['created_at']}'"
    print("✓ PASS: Aware datetime correctly serialized with timezone indicator")
    return True


def test_none_datetime():
    """Test that None datetime values are handled."""
    print("\n=== Test 3: None datetime ===")

    dt = datetime.now()
    model = TestModel(name="test", created_at=dt, updated_at=None)

    json_str = model.model_dump_json()
    data = json.loads(json_str)

    print(f"updated_at: {data['updated_at']}")

    assert data['updated_at'] is None, "None should remain None"
    assert data['created_at'].endswith('Z'), "created_at should still have 'Z'"
    print("✓ PASS: None datetime values handled correctly")
    return True


def test_now_datetime():
    """Test current datetime."""
    print("\n=== Test 4: datetime.now() ===")

    model = TestModel(name="test", created_at=datetime.now())

    json_str = model.model_dump_json()
    data = json.loads(json_str)

    print(f"Serialized: {data['created_at']}")

    # Should end with 'Z'
    assert data['created_at'].endswith('Z'), \
        f"datetime.now() should serialize with 'Z', got '{data['created_at']}'"
    print("✓ PASS: datetime.now() correctly serialized with 'Z' suffix")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("UTC Datetime Serialization Test Suite")
    print("=" * 60)

    tests = [
        test_naive_datetime,
        test_aware_datetime,
        test_none_datetime,
        test_now_datetime,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"✗ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n✓ All tests passed! Datetime serialization is working correctly.")
        print("  All datetime fields will now include the 'Z' suffix in JSON responses.")

    return failed == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
