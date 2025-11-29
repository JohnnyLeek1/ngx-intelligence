"""
Example usage of the Ollama AI provider.

This script demonstrates how to use the OllamaProvider for various tasks
including text generation, JSON generation, and model management.

Requirements:
- Ollama must be running: `ollama serve`
- A model must be available: `ollama pull llama3.2`
"""

import asyncio
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ai.ollama import OllamaProvider, OllamaError, OllamaTimeoutError


async def example_basic_generation():
    """Example: Basic text generation."""
    print("\n=== Example 1: Basic Text Generation ===")

    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.2",
        timeout=120
    )

    try:
        # Check if Ollama is running
        if not await provider.health_check():
            print("ERROR: Ollama is not running. Start it with: ollama serve")
            return

        # Generate a response
        response = await provider.generate(
            prompt="What are the three main types of business documents?",
            system_prompt="You are a helpful assistant specialized in business documentation.",
            temperature=0.7
        )

        print(f"Response: {response.content}")
        print(f"Model: {response.model}")
        print(f"Tokens: {response.total_tokens} (prompt: {response.prompt_tokens}, completion: {response.completion_tokens})")
        print(f"Metadata: {response.metadata}")

    except OllamaError as e:
        print(f"Error: {e}")
    finally:
        await provider.close()


async def example_json_generation():
    """Example: Generate structured JSON output."""
    print("\n=== Example 2: JSON Generation ===")

    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.2",
        temperature=0.3  # Lower temperature for more consistent JSON
    )

    try:
        # Define a schema
        schema = {
            "type": "object",
            "properties": {
                "document_type": {
                    "type": "string",
                    "enum": ["invoice", "contract", "receipt", "letter", "report"]
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "reasoning": {
                    "type": "string"
                }
            },
            "required": ["document_type", "confidence"]
        }

        # Simulate document classification
        document_content = """
        INVOICE

        Invoice #: INV-2024-001
        Date: 2024-01-15

        Bill To:
        Acme Corporation
        123 Business Street

        Items:
        - Widget A: $100.00
        - Widget B: $150.00

        Total: $250.00
        """

        result = await provider.generate_json(
            prompt=f"Classify this document:\n\n{document_content}",
            system_prompt="You are a document classifier. Analyze the document and return classification results.",
            schema=schema,
            temperature=0.3
        )

        print(f"Classification Result:")
        print(json.dumps(result, indent=2))

    except OllamaError as e:
        print(f"Error: {e}")
    finally:
        await provider.close()


async def example_model_management():
    """Example: List and manage models."""
    print("\n=== Example 3: Model Management ===")

    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.2"
    )

    try:
        # List available models
        models = await provider.list_models()
        print(f"Available models ({len(models)}):")
        for model in models:
            print(f"  - {model}")

        # Check specific model availability
        if "llama3.2" in models:
            print("\nllama3.2 is available ✓")
        else:
            print("\nllama3.2 is not available. Pull it with: ollama pull llama3.2")

    except OllamaError as e:
        print(f"Error: {e}")
    finally:
        await provider.close()


async def example_with_options():
    """Example: Using advanced Ollama options."""
    print("\n=== Example 4: Advanced Options ===")

    # Create provider with custom options
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.2",
        temperature=0.8,
        top_p=0.9,
        top_k=40,
        repeat_penalty=1.1,
        seed=42  # For reproducible results
    )

    try:
        # Generate with the configured options
        response = await provider.generate(
            prompt="Generate a creative title for a document about sustainable energy.",
            system_prompt="You are a creative writer.",
            max_tokens=50
        )

        print(f"Generated title: {response.content}")
        print(f"Settings used: temp={provider.temperature}, top_p={provider.top_p}, seed={provider.seed}")

    except OllamaError as e:
        print(f"Error: {e}")
    finally:
        await provider.close()


async def example_document_tagging():
    """Example: Document tagging use case."""
    print("\n=== Example 5: Document Tagging ===")

    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.2",
        temperature=0.5
    )

    try:
        document = """
        Project Status Report - Q1 2024

        Executive Summary:
        The solar panel installation project is proceeding on schedule.
        We have completed 75% of the planned installations and are
        within budget. Environmental impact assessments show positive
        results with 30% reduction in carbon emissions.

        Next Steps:
        - Complete remaining installations by end of Q2
        - Submit final environmental report
        - Begin maintenance training program
        """

        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Relevant tags for the document"
                },
                "confidences": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Confidence score for each tag (0-1)"
                }
            }
        }

        result = await provider.generate_json(
            prompt=f"Suggest relevant tags for this document:\n\n{document}",
            system_prompt="You are a document tagging system. Suggest 3-5 relevant tags.",
            schema=schema
        )

        print("Suggested tags:")
        tags = result.get("tags", [])
        confidences = result.get("confidences", [])

        for i, tag in enumerate(tags):
            confidence = confidences[i] if i < len(confidences) else 0.0
            print(f"  - {tag} (confidence: {confidence:.2f})")

    except OllamaError as e:
        print(f"Error: {e}")
    finally:
        await provider.close()


async def example_error_handling():
    """Example: Error handling scenarios."""
    print("\n=== Example 6: Error Handling ===")

    # Test 1: Invalid model
    print("\nTest 1: Invalid model")
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="nonexistent-model"
    )

    try:
        await provider.generate("Test prompt")
    except OllamaError as e:
        print(f"Caught expected error: {e}")
    finally:
        await provider.close()

    # Test 2: Connection error
    print("\nTest 2: Connection error")
    provider = OllamaProvider(
        base_url="http://localhost:99999",  # Invalid port
        model="llama3.2"
    )
    provider.timeout = 5  # Short timeout

    try:
        await provider.generate("Test prompt")
    except OllamaError as e:
        print(f"Caught expected error: {e}")
    finally:
        await provider.close()


async def example_model_aliases():
    """Example: Using model aliases."""
    print("\n=== Example 7: Model Aliases ===")

    # You can use aliases like "llama3" instead of "llama3.2"
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3"  # Will be resolved to "llama3.2"
    )

    print(f"Requested model: 'llama3'")
    print(f"Resolved to: '{provider.model}'")

    await provider.close()


async def main():
    """Run all examples."""
    print("=" * 60)
    print("Ollama Provider Examples")
    print("=" * 60)

    examples = [
        ("Basic Generation", example_basic_generation),
        ("JSON Generation", example_json_generation),
        ("Model Management", example_model_management),
        ("Advanced Options", example_with_options),
        ("Document Tagging", example_document_tagging),
        ("Error Handling", example_error_handling),
        ("Model Aliases", example_model_aliases),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nRunning all examples...\n")

    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\nExample '{name}' failed with error: {e}")

        # Small delay between examples
        await asyncio.sleep(1)

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
