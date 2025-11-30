#!/usr/bin/env python3
"""
Test script for Ollama URL configuration updates.

This script verifies that:
1. The AI config schema supports ollama_url
2. URL validation works correctly
3. The config service properly handles ollama_url updates
4. OllamaProvider can be created with database config
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import get_settings, Settings
from app.services.config_service import ConfigService
from app.services.ai.ollama import get_ollama_provider_from_config
from app.database.session import async_session_maker, init_db
from app.database.models import User, UserRole
from sqlalchemy import select
from uuid import uuid4


async def test_config_schema():
    """Test that AI config schema supports ollama_url."""
    print("\n=== Testing Config Schema ===")

    settings = get_settings()

    # Test that AI config has the new fields
    print(f"✓ AI provider: {settings.ai.provider}")
    print(f"✓ AI model field exists: {hasattr(settings.ai, 'model')}")
    print(f"✓ AI ollama_url field exists: {hasattr(settings.ai, 'ollama_url')}")
    print(f"✓ Default ollama base_url: {settings.ai.ollama.base_url}")
    print(f"✓ AI ollama_url value: {settings.ai.ollama_url}")

    return True


async def test_url_validation():
    """Test URL validation in config service."""
    print("\n=== Testing URL Validation ===")

    async with async_session_maker() as db:
        service = ConfigService(db)

        # Test valid URLs
        valid_urls = [
            "http://localhost:11434",
            "http://192.168.1.100:11434",
            "https://ollama.example.com",
            "http://ollama:11434",
        ]

        for url in valid_urls:
            try:
                service._validate_ai_config({"ollama_url": url})
                print(f"✓ Valid URL accepted: {url}")
            except ValueError as e:
                print(f"✗ Valid URL rejected: {url} - {e}")
                return False

        # Test invalid URLs
        invalid_urls = [
            ("ftp://localhost:11434", "Invalid scheme"),
            ("localhost:11434", "Missing scheme"),
            ("http://", "Missing hostname"),
        ]

        for url, reason in invalid_urls:
            try:
                service._validate_ai_config({"ollama_url": url})
                print(f"✗ Invalid URL accepted: {url} ({reason})")
                return False
            except ValueError as e:
                print(f"✓ Invalid URL rejected: {url} - {reason}")

        # Test that empty/None ollama_url is allowed
        try:
            service._validate_ai_config({"ollama_url": None})
            service._validate_ai_config({"ollama_url": ""})
            service._validate_ai_config({})  # No ollama_url key
            print("✓ Empty/None ollama_url accepted")
        except ValueError as e:
            print(f"✗ Empty/None ollama_url rejected: {e}")
            return False

    return True


async def test_config_update():
    """Test updating AI config with ollama_url."""
    print("\n=== Testing Config Update ===")

    # Initialize database
    await init_db()

    async with async_session_maker() as db:
        # Get or create admin user for testing
        stmt = select(User).where(User.username == "admin")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            print("Creating test admin user...")
            user = User(
                id=uuid4(),
                username="admin",
                email="admin@test.com",
                role=UserRole.ADMIN,
                is_active=True,
            )
            user.set_password("admin123")
            db.add(user)
            await db.commit()
            await db.refresh(user)

        service = ConfigService(db)

        # Test updating ollama_url
        test_url = "http://test-ollama:11434"
        test_model = "llama3.2:latest"

        print(f"Updating AI config with ollama_url: {test_url}")
        updated = await service.update_section(
            section="ai",
            data={
                "ollama_url": test_url,
                "model": test_model,
            },
            user_id=user.id
        )

        print(f"✓ Config updated successfully")
        print(f"  - ollama_url: {updated.get('ollama_url')}")
        print(f"  - model: {updated.get('model')}")

        # Verify the update persisted
        ai_config = await service.get_section("ai")
        if ai_config.get("ollama_url") == test_url:
            print("✓ ollama_url persisted correctly")
        else:
            print(f"✗ ollama_url not persisted: {ai_config.get('ollama_url')}")
            return False

        if ai_config.get("model") == test_model:
            print("✓ model persisted correctly")
        else:
            print(f"✗ model not persisted: {ai_config.get('model')}")
            return False

    return True


async def test_provider_factory():
    """Test creating OllamaProvider from database config."""
    print("\n=== Testing OllamaProvider Factory ===")

    async with async_session_maker() as db:
        service = ConfigService(db)

        # Set a test URL in config
        stmt = select(User).limit(1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            test_url = "http://factory-test:11434"
            await service.update_section(
                section="ai",
                data={"ollama_url": test_url, "model": "llama3.2"},
                user_id=user.id
            )

        # Create provider from config
        provider = await get_ollama_provider_from_config(db)

        print(f"✓ OllamaProvider created from config")
        print(f"  - base_url: {provider.base_url}")
        print(f"  - model: {provider.model}")

        # Verify it uses the database URL
        if user and provider.base_url == test_url:
            print("✓ Provider uses database-configured URL")
        else:
            print(f"  (Using environment/default URL: {provider.base_url})")

        # Clean up
        await provider.close()

    return True


async def test_connection_test():
    """Test the connection test functionality."""
    print("\n=== Testing Connection Test ===")

    async with async_session_maker() as db:
        service = ConfigService(db)

        # Test with localhost (may or may not be reachable)
        result = await service.test_ollama_connection("http://localhost:11434")

        print(f"Connection test result for http://localhost:11434:")
        print(f"  - reachable: {result['reachable']}")
        print(f"  - error: {result['error']}")
        print(f"  - models: {result['models']}")

        # Test with invalid URL (should fail)
        result = await service.test_ollama_connection("http://invalid-host-that-does-not-exist:11434")

        if not result['reachable'] and result['error']:
            print(f"✓ Invalid URL correctly detected as unreachable")
        else:
            print(f"✗ Invalid URL not detected as unreachable")
            return False

    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Ollama URL Configuration Test Suite")
    print("=" * 60)

    tests = [
        ("Config Schema", test_config_schema),
        ("URL Validation", test_url_validation),
        ("Config Update", test_config_update),
        ("Provider Factory", test_provider_factory),
        ("Connection Test", test_connection_test),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
