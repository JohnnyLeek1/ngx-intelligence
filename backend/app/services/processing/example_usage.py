"""
Example usage of the document processing pipeline and queue manager.

This file demonstrates how to integrate and use the processing services.
"""

import asyncio
from uuid import UUID

from app.config import get_settings
from app.services.ai.ollama import OllamaProvider
from app.services.paperless import PaperlessClient
from app.services.processing import (
    DocumentProcessor,
    QueueManager,
    init_queue_manager,
    get_queue_manager,
)


async def example_single_document_processing():
    """
    Example: Process a single document directly without queue.

    Use case: Manual, on-demand processing triggered by user action.
    """
    print("\n=== Example: Single Document Processing ===\n")

    # Initialize services
    settings = get_settings()

    # Create AI provider
    ai_provider = OllamaProvider(
        base_url=settings.ai.ollama.base_url,
        model=settings.ai.ollama.model,
        timeout=settings.ai.ollama.timeout,
    )

    # Create Paperless client (using user's credentials)
    paperless_client = PaperlessClient(
        base_url="http://localhost:8000",  # User's Paperless URL
        auth_token="your-token-here",  # User's Paperless token
    )

    # Create processor
    processor = DocumentProcessor(
        ai_provider=ai_provider,
        paperless_client=paperless_client,
    )

    try:
        # Process a single document
        user_id = UUID("12345678-1234-5678-1234-567812345678")
        document_id = 123

        print(f"Processing document {document_id}...")

        result = await processor.process_document(
            document_id=document_id,
            user_id=user_id,
            approval_mode=False,  # Apply changes directly
        )

        print(f"\nProcessing completed!")
        print(f"  Success: {result['success']}")
        print(f"  Confidence: {result['confidence_score']:.2%}")
        print(f"  Processing time: {result['processing_time_ms']}ms")
        print(f"\nSuggested metadata:")
        print(f"  Title: {result['suggested_data']['title']}")
        print(f"  Type: {result['suggested_data']['document_type']}")
        print(f"  Correspondent: {result['suggested_data']['correspondent']}")
        print(f"  Tags: {', '.join(result['suggested_data']['tags'])}")
        print(f"  Date: {result['suggested_data']['document_date']}")

    finally:
        await ai_provider.close()
        await paperless_client.close()


async def example_queue_based_processing_manual():
    """
    Example: Manual mode - Add documents to queue and process explicitly.

    Use case: User manually selects documents to process.
    """
    print("\n=== Example: Manual Queue Processing ===\n")

    settings = get_settings()

    # Initialize services
    ai_provider = OllamaProvider(
        base_url=settings.ai.ollama.base_url,
        model=settings.ai.ollama.model,
    )

    paperless_client = PaperlessClient(
        base_url="http://localhost:8000",
        auth_token="your-token-here",
    )

    processor = DocumentProcessor(ai_provider, paperless_client)

    # Initialize queue manager
    queue_manager = init_queue_manager(
        processor=processor,
        paperless_client=paperless_client,
        max_workers=2,  # 2 concurrent workers
    )

    try:
        # Start queue manager (in manual mode, workers wait for queue items)
        print("Starting queue manager...")
        await queue_manager.start()

        # Add documents to queue
        user_id = UUID("12345678-1234-5678-1234-567812345678")

        print("\nAdding documents to queue...")
        await queue_manager.add_document(user_id, 100, priority=1)
        await queue_manager.add_document(user_id, 101, priority=0)
        await queue_manager.add_document(user_id, 102, priority=2)  # High priority

        # Wait for processing to complete
        print("\nProcessing queue...")
        await asyncio.sleep(30)  # Give workers time to process

        # Get statistics
        stats = await queue_manager.get_stats()
        print(f"\nQueue Statistics:")
        print(f"  Queued: {stats['queue']['queued']}")
        print(f"  Processing: {stats['queue']['processing']}")
        print(f"  Completed: {stats['queue']['completed']}")
        print(f"  Failed: {stats['queue']['failed']}")
        print(f"  Total processed: {stats['lifetime']['total_processed']}")
        print(f"  Success rate: {stats['lifetime']['total_success']}/{stats['lifetime']['total_processed']}")

        # Stop queue manager
        print("\nStopping queue manager...")
        await queue_manager.stop()

    finally:
        await ai_provider.close()
        await paperless_client.close()


async def example_realtime_polling():
    """
    Example: Real-time polling mode - automatically detect new documents.

    Use case: Continuous monitoring of Paperless for new documents.
    """
    print("\n=== Example: Real-time Polling Mode ===\n")

    settings = get_settings()

    # Initialize services
    ai_provider = OllamaProvider(
        base_url=settings.ai.ollama.base_url,
        model=settings.ai.ollama.model,
    )

    paperless_client = PaperlessClient(
        base_url="http://localhost:8000",
        auth_token="your-token-here",
    )

    processor = DocumentProcessor(ai_provider, paperless_client)

    # Initialize queue manager with polling
    queue_manager = init_queue_manager(
        processor=processor,
        paperless_client=paperless_client,
        max_workers=3,
        polling_interval=30,  # Poll every 30 seconds
    )

    try:
        print("Starting queue manager in real-time polling mode...")
        print("Polling Paperless every 30 seconds for new documents...\n")

        await queue_manager.start()

        # Let it run for a while
        print("Queue manager running. Press Ctrl+C to stop.\n")

        # Monitor stats periodically
        for i in range(10):  # Monitor for 5 minutes
            await asyncio.sleep(30)
            stats = await queue_manager.get_stats()
            print(f"[{i+1}] Processed: {stats['lifetime']['total_processed']}, "
                  f"Queued: {stats['queue']['queued']}, "
                  f"Success: {stats['lifetime']['total_success']}")

        await queue_manager.stop()

    except KeyboardInterrupt:
        print("\n\nStopping queue manager...")
        await queue_manager.stop()

    finally:
        await ai_provider.close()
        await paperless_client.close()


async def example_batch_processing():
    """
    Example: Batch processing mode - process in scheduled batches.

    Use case: Process documents in batches (e.g., every 100 documents or 1 hour).
    """
    print("\n=== Example: Batch Processing Mode ===\n")

    settings = get_settings()

    # Update settings for batch mode (in production, this would be in config)
    settings.processing.mode = "batch"
    settings.processing.batch_rules.document_threshold = 10  # Process every 10 docs
    settings.processing.batch_rules.time_threshold = 300  # Or every 5 minutes
    settings.processing.batch_rules.rule_type = "either"  # Whichever comes first

    # Initialize services
    ai_provider = OllamaProvider(
        base_url=settings.ai.ollama.base_url,
        model=settings.ai.ollama.model,
    )

    paperless_client = PaperlessClient(
        base_url="http://localhost:8000",
        auth_token="your-token-here",
    )

    processor = DocumentProcessor(ai_provider, paperless_client)

    queue_manager = init_queue_manager(
        processor=processor,
        paperless_client=paperless_client,
        max_workers=5,  # More workers for batch processing
    )

    try:
        print("Starting queue manager in batch mode...")
        print(f"Batch rules: Process every {settings.processing.batch_rules.document_threshold} "
              f"documents OR {settings.processing.batch_rules.time_threshold} seconds\n")

        await queue_manager.start()

        # Simulate adding documents over time
        user_id = UUID("12345678-1234-5678-1234-567812345678")

        for i in range(25):
            await queue_manager.add_document(user_id, 200 + i, priority=0)
            print(f"Added document {200 + i} to queue")
            await asyncio.sleep(2)  # Add one every 2 seconds

            # Check if batch triggered
            stats = await queue_manager.get_stats()
            if i > 0 and i % 5 == 0:
                print(f"  Queue status: {stats['queue']['queued']} queued, "
                      f"{stats['queue']['completed']} completed")

        # Wait for final batch
        await asyncio.sleep(60)

        # Final stats
        stats = await queue_manager.get_stats()
        print(f"\nFinal statistics:")
        print(f"  Total processed: {stats['lifetime']['total_processed']}")
        print(f"  Success: {stats['lifetime']['total_success']}")
        print(f"  Failed: {stats['lifetime']['total_failed']}")

        await queue_manager.stop()

    finally:
        await ai_provider.close()
        await paperless_client.close()


async def example_approval_workflow():
    """
    Example: Approval workflow - queue suggestions for user review.

    Use case: User wants to review AI suggestions before applying.
    """
    print("\n=== Example: Approval Workflow ===\n")

    settings = get_settings()
    settings.approval_workflow.enabled = True  # Enable approval mode

    # Initialize services
    ai_provider = OllamaProvider(
        base_url=settings.ai.ollama.base_url,
        model=settings.ai.ollama.model,
    )

    paperless_client = PaperlessClient(
        base_url="http://localhost:8000",
        auth_token="your-token-here",
    )

    processor = DocumentProcessor(ai_provider, paperless_client)

    try:
        user_id = UUID("12345678-1234-5678-1234-567812345678")
        document_id = 150

        print(f"Processing document {document_id} in approval mode...")

        result = await processor.process_document(
            document_id=document_id,
            user_id=user_id,
            approval_mode=True,  # Enable approval workflow
        )

        print(f"\nDocument processed - awaiting approval:")
        print(f"  Confidence: {result['confidence_score']:.2%}")
        print(f"\nSuggested changes:")
        print(f"  Title: {result['suggested_data']['title']}")
        print(f"  Type: {result['suggested_data']['document_type']}")
        print(f"  Correspondent: {result['suggested_data']['correspondent']}")
        print(f"  Tags: {', '.join(result['suggested_data']['tags'])}")

        print(f"\nChanges NOT applied - waiting for user approval")
        print(f"Document tagged with '{settings.approval_workflow.pending_tag}'")

        # In a real application:
        # 1. User reviews suggestions in UI
        # 2. User approves or rejects
        # 3. API endpoint applies approved changes to Paperless

    finally:
        await ai_provider.close()
        await paperless_client.close()


async def example_error_handling_and_retry():
    """
    Example: Error handling and retry logic.

    Use case: Handle failures gracefully with automatic retries.
    """
    print("\n=== Example: Error Handling & Retry ===\n")

    settings = get_settings()

    ai_provider = OllamaProvider(
        base_url=settings.ai.ollama.base_url,
        model=settings.ai.ollama.model,
    )

    paperless_client = PaperlessClient(
        base_url="http://localhost:8000",
        auth_token="your-token-here",
    )

    processor = DocumentProcessor(ai_provider, paperless_client)

    queue_manager = init_queue_manager(
        processor=processor,
        paperless_client=paperless_client,
        max_workers=2,
    )

    try:
        await queue_manager.start()

        user_id = UUID("12345678-1234-5678-1234-567812345678")

        # Add some documents (some may fail)
        print("Adding documents to queue...")
        await queue_manager.add_document(user_id, 999999, priority=0)  # Invalid ID - will fail
        await queue_manager.add_document(user_id, 100, priority=0)  # Valid

        # Wait for processing
        await asyncio.sleep(10)

        # Check for failures
        stats = await queue_manager.get_stats()
        print(f"\nProcessing results:")
        print(f"  Success: {stats['lifetime']['total_success']}")
        print(f"  Failed: {stats['lifetime']['total_failed']}")

        if stats['queue']['failed'] > 0:
            print(f"\nRetrying failed documents...")
            retried = await queue_manager.retry_failed(max_retries=3)
            print(f"  Re-queued {retried} documents for retry")

            # Wait for retry processing
            await asyncio.sleep(10)

            # Check final stats
            stats = await queue_manager.get_stats()
            print(f"\nFinal results:")
            print(f"  Success: {stats['lifetime']['total_success']}")
            print(f"  Failed: {stats['lifetime']['total_failed']}")
            print(f"  Total retries: {stats['lifetime']['total_retries']}")

        await queue_manager.stop()

    finally:
        await ai_provider.close()
        await paperless_client.close()


async def main():
    """Run all examples."""
    examples = [
        ("Single Document Processing", example_single_document_processing),
        ("Manual Queue Processing", example_queue_based_processing_manual),
        ("Real-time Polling", example_realtime_polling),
        ("Batch Processing", example_batch_processing),
        ("Approval Workflow", example_approval_workflow),
        ("Error Handling & Retry", example_error_handling_and_retry),
    ]

    print("=" * 60)
    print("Document Processing Pipeline - Example Usage")
    print("=" * 60)

    for i, (name, example_func) in enumerate(examples, 1):
        print(f"\n\n[{i}/{len(examples)}] {name}")
        print("-" * 60)

        try:
            # Uncomment the example you want to run
            # await example_func()
            pass
        except Exception as e:
            print(f"Error in example: {e}")

        print("-" * 60)

    print("\n\nAll examples completed!")
    print("\nTo run a specific example, uncomment the await line in the main() function.")


if __name__ == "__main__":
    # To run examples, uncomment the desired example function call
    # asyncio.run(example_single_document_processing())
    # asyncio.run(example_queue_based_processing_manual())
    # asyncio.run(example_realtime_polling())
    # asyncio.run(example_batch_processing())
    # asyncio.run(example_approval_workflow())
    # asyncio.run(example_error_handling_and_retry())

    asyncio.run(main())
