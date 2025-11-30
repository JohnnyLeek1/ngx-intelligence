#!/usr/bin/env python3
"""
Test script for the AI models endpoint.

This script verifies that:
1. The endpoint properly fetches models from Ollama
2. Model information includes size and availability
3. Error handling works correctly
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ai.ollama import get_ollama_provider_from_config, OllamaProvider
from app.services.config_service import ConfigService
from app.database.session import async_session_maker, init_db


async def test_list_models_basic():
    """Test basic model listing."""
    print("\n=== Testing Basic Model Listing ===")

    # Create a provider with default settings
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.2"
    )

    try:
        models = await provider.list_models()
        print(f"✓ Found {len(models)} models:")
        for model in models:
            print(f"  - {model}")
        return True
    except Exception as e:
        print(f"✗ Failed to list models: {e}")
        return False
    finally:
        await provider.close()


async def test_list_models_detailed():
    """Test detailed model listing."""
    print("\n=== Testing Detailed Model Listing ===")

    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.2"
    )

    try:
        models = await provider.list_models_detailed()
        print(f"✓ Found {len(models)} models with details:")
        for model in models:
            name = model.get("name", "Unknown")
            size = model.get("size", 0)
            size_gb = size / (1024 ** 3) if size else 0
            modified = model.get("modified_at", "Unknown")
            print(f"  - {name}")
            print(f"    Size: {size_gb:.2f} GB")
            print(f"    Modified: {modified}")
        return True
    except Exception as e:
        print(f"✗ Failed to list detailed models: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await provider.close()


async def test_with_database_config():
    """Test listing models using database configuration."""
    print("\n=== Testing with Database Configuration ===")

    await init_db()

    async with async_session_maker() as db:
        try:
            provider = await get_ollama_provider_from_config(db)

            print(f"Provider configuration:")
            print(f"  - Base URL: {provider.base_url}")
            print(f"  - Model: {provider.model}")

            models = await provider.list_models_detailed()
            print(f"\n✓ Found {len(models)} models:")

            for model in models:
                name = model.get("name", "Unknown")
                size = model.get("size", 0)
                size_gb = size / (1024 ** 3) if size else 0
                print(f"  - {name}: {size_gb:.2f} GB")

            await provider.close()
            return True

        except Exception as e:
            print(f"✗ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_endpoint_logic():
    """Simulate the endpoint logic."""
    print("\n=== Testing Endpoint Logic ===")

    await init_db()

    async with async_session_maker() as db:
        service = ConfigService(db)
        ai_config = await service.get_section("ai")
        current_model = ai_config.get("model", "llama3.2:latest")

        print(f"Current configured model: {current_model}")

        from app.services.ai.ollama import get_ollama_provider_from_config, OllamaConnectionError

        try:
            ollama = await get_ollama_provider_from_config(db)

            try:
                # Fetch detailed model information
                models_data = await ollama.list_models_detailed()

                # Format models for response
                models = []
                model_names = []

                for model_info in models_data:
                    model_name = model_info.get("name", "")
                    if not model_name:
                        continue

                    model_names.append(model_name)

                    # Format size for display (convert bytes to human-readable)
                    size_bytes = model_info.get("size", 0)
                    if size_bytes:
                        size_gb = size_bytes / (1024 ** 3)
                        size_str = f"{size_gb:.2f} GB"
                    else:
                        size_str = None

                    models.append({
                        "name": model_name,
                        "size": size_str,
                        "modified_at": model_info.get("modified_at"),
                        "is_available": True
                    })

                # If current model not in list, add it as unavailable
                if current_model not in model_names:
                    models.insert(0, {
                        "name": current_model,
                        "is_available": False
                    })

                print(f"\n✓ Successfully processed {len(models)} models:")
                for model in models:
                    avail = "available" if model.get("is_available") else "NOT AVAILABLE"
                    size = f" ({model.get('size')})" if model.get('size') else ""
                    print(f"  - {model['name']}: {avail}{size}")

                return True

            finally:
                await ollama.close()

        except OllamaConnectionError as e:
            print(f"✗ Cannot connect to Ollama: {e}")
            print("  This would return HTTP 503 with connection error details")
            return False
        except Exception as e:
            print(f"✗ Failed to fetch AI models: {e}")
            print("  This would return HTTP 500 with error details")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("AI Models Endpoint Test Suite")
    print("=" * 60)

    tests = [
        ("Basic Model Listing", test_list_models_basic),
        ("Detailed Model Listing", test_list_models_detailed),
        ("Database Configuration", test_with_database_config),
        ("Endpoint Logic", test_endpoint_logic),
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
        print("\nAll tests passed!")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
