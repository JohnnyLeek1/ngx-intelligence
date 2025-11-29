#!/usr/bin/env python3
"""
Test script for Paperless-NGX API client.

This script demonstrates the complete functionality of the PaperlessClient.
Run with actual Paperless credentials to test the integration.

Usage:
    python test_paperless_client.py
"""

import asyncio
import sys
from typing import Dict, Any

from app.services.paperless import (
    PaperlessClient,
    PaperlessAPIError,
    PaperlessAuthError,
    PaperlessNotFoundError,
    PaperlessRateLimitError,
)


async def test_health_check(client: PaperlessClient) -> bool:
    """Test basic connectivity."""
    print("\n=== Testing Health Check ===")
    is_healthy = await client.health_check()
    print(f"Health check: {'✓ PASS' if is_healthy else '✗ FAIL'}")
    return is_healthy


async def test_credentials(client: PaperlessClient) -> bool:
    """Test credential validation."""
    print("\n=== Testing Credential Validation ===")
    try:
        info = await client.validate_credentials()
        print(f"✓ Credentials valid")
        print(f"  API endpoints available: {len(info)}")
        return True
    except PaperlessAuthError as e:
        print(f"✗ Authentication failed: {e.message}")
        return False
    except PaperlessAPIError as e:
        print(f"✗ API error: {e.message}")
        return False


async def test_document_operations(client: PaperlessClient) -> bool:
    """Test document fetching and listing."""
    print("\n=== Testing Document Operations ===")

    # List documents
    try:
        result = await client.list_documents(page=1, page_size=5)
        total = result.get("count", 0)
        docs = result.get("results", [])

        print(f"✓ Listed documents: {len(docs)} of {total} total")

        if not docs:
            print("  No documents found to test with")
            return True

        # Test fetching individual document
        first_doc_id = docs[0]["id"]
        doc = await client.get_document(first_doc_id)

        print(f"✓ Fetched document {first_doc_id}")
        print(f"  Title: {doc.get('title', 'N/A')}")
        print(f"  Content length: {len(doc.get('content', ''))} chars")
        print(f"  Tags: {doc.get('tags', [])}")
        print(f"  Correspondent: {doc.get('correspondent', 'None')}")
        print(f"  Document Type: {doc.get('document_type', 'None')}")

        return True

    except PaperlessNotFoundError as e:
        print(f"✗ Document not found: {e.message}")
        return False
    except PaperlessAPIError as e:
        print(f"✗ API error: {e.message}")
        return False


async def test_metadata_operations(client: PaperlessClient) -> bool:
    """Test fetching tags, types, and correspondents."""
    print("\n=== Testing Metadata Operations ===")

    try:
        # Get document types
        doc_types = await client.get_document_types()
        print(f"✓ Fetched {len(doc_types)} document types")
        if doc_types:
            print(f"  Example: {doc_types[0]['name']} (ID: {doc_types[0]['id']})")

        # Get tags
        tags = await client.get_tags()
        print(f"✓ Fetched {len(tags)} tags")
        if tags:
            print(f"  Example: {tags[0]['name']} (ID: {tags[0]['id']}, Color: {tags[0].get('color', 'N/A')})")

        # Get correspondents
        correspondents = await client.get_correspondents()
        print(f"✓ Fetched {len(correspondents)} correspondents")
        if correspondents:
            print(f"  Example: {correspondents[0]['name']} (ID: {correspondents[0]['id']})")

        return True

    except PaperlessAPIError as e:
        print(f"✗ API error: {e.message}")
        return False


async def test_filtering(client: PaperlessClient) -> bool:
    """Test document filtering capabilities."""
    print("\n=== Testing Document Filtering ===")

    try:
        # Test ordering
        result = await client.list_documents(
            page=1,
            page_size=5,
            filters={"ordering": "-created"}
        )
        print(f"✓ Filtered by created date (newest first): {len(result.get('results', []))} docs")

        # Get a tag to filter by
        tags = await client.get_tags()
        if tags:
            tag_id = tags[0]['id']
            result = await client.list_documents(
                page=1,
                page_size=5,
                filters={"tags__id__in": str(tag_id)}
            )
            print(f"✓ Filtered by tag '{tags[0]['name']}': {len(result.get('results', []))} docs")

        return True

    except PaperlessAPIError as e:
        print(f"✗ API error: {e.message}")
        return False


async def test_error_handling(client: PaperlessClient) -> bool:
    """Test error handling for invalid operations."""
    print("\n=== Testing Error Handling ===")

    # Test 404 handling
    try:
        await client.get_document(999999999)
        print("✗ Should have raised PaperlessNotFoundError")
        return False
    except PaperlessNotFoundError:
        print("✓ Correctly handled 404 Not Found")

    # Test invalid token (if we can override it)
    try:
        await client.validate_credentials(token="invalid-token-12345")
        print("✗ Should have raised PaperlessAuthError")
        return False
    except PaperlessAuthError:
        print("✓ Correctly handled 401 Unauthorized")

    return True


async def run_all_tests(base_url: str, token: str):
    """Run all tests."""
    print("=" * 60)
    print("PAPERLESS-NGX API CLIENT TEST SUITE")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print(f"Token: {token[:10]}..." if len(token) > 10 else "Token: (short)")

    results = []

    async with PaperlessClient(base_url, token, timeout=30) as client:
        # Run tests
        results.append(("Health Check", await test_health_check(client)))

        if not results[-1][1]:
            print("\n✗ Health check failed - aborting further tests")
            return

        results.append(("Credentials", await test_credentials(client)))

        if not results[-1][1]:
            print("\n✗ Authentication failed - aborting further tests")
            return

        results.append(("Document Ops", await test_document_operations(client)))
        results.append(("Metadata Ops", await test_metadata_operations(client)))
        results.append(("Filtering", await test_filtering(client)))
        results.append(("Error Handling", await test_error_handling(client)))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20s} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


async def demo_ai_workflow(base_url: str, token: str):
    """Demonstrate a complete AI processing workflow."""
    print("\n" + "=" * 60)
    print("AI PROCESSING WORKFLOW DEMO")
    print("=" * 60)

    async with PaperlessClient(base_url, token, timeout=60) as client:
        # Check health
        if not await client.health_check():
            print("✗ Paperless not accessible")
            return

        # Fetch recent documents
        result = await client.list_documents(
            page=1,
            page_size=3,
            filters={"ordering": "-created"}
        )

        if not result.get("results"):
            print("No documents found")
            return

        print(f"\nProcessing {len(result['results'])} recent documents:\n")

        # Load metadata caches
        doc_types = await client.get_document_types()
        tags = await client.get_tags()
        correspondents = await client.get_correspondents()

        type_map = {dt["id"]: dt["name"] for dt in doc_types}
        tag_map = {t["id"]: t["name"] for t in tags}
        corr_map = {c["id"]: c["name"] for c in correspondents}

        for doc in result["results"]:
            full_doc = await client.get_document(doc["id"])

            print(f"Document {doc['id']}: {full_doc['title']}")
            print(f"  Created: {full_doc.get('created', 'N/A')}")
            print(f"  Type: {type_map.get(full_doc.get('document_type'), 'None')}")
            print(f"  Correspondent: {corr_map.get(full_doc.get('correspondent'), 'None')}")

            doc_tags = [tag_map.get(tid, f"Unknown-{tid}") for tid in full_doc.get("tags", [])]
            print(f"  Tags: {', '.join(doc_tags) if doc_tags else 'None'}")
            print(f"  Content: {len(full_doc.get('content', ''))} chars")

            # Simulate AI suggestions
            print(f"  → AI would analyze: {full_doc.get('content', '')[:100]}...")
            print()


def main():
    """Main entry point."""
    # Configuration - replace with your actual values
    PAPERLESS_URL = "http://localhost:8000"
    PAPERLESS_TOKEN = "your-api-token-here"

    # Check if we have valid config
    if PAPERLESS_TOKEN == "your-api-token-here":
        print("ERROR: Please configure PAPERLESS_URL and PAPERLESS_TOKEN")
        print("\nEdit this file and set:")
        print("  PAPERLESS_URL = 'http://your-paperless-instance:8000'")
        print("  PAPERLESS_TOKEN = 'your-actual-api-token'")
        print("\nYou can get your token from Paperless-NGX:")
        print("  Settings > Manage > Authentication Tokens")
        sys.exit(1)

    # Run tests
    print("Starting Paperless API Client tests...\n")

    try:
        asyncio.run(run_all_tests(PAPERLESS_URL, PAPERLESS_TOKEN))
        asyncio.run(demo_ai_workflow(PAPERLESS_URL, PAPERLESS_TOKEN))
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
