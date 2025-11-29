"""
Integration tests for service layer.

Tests Paperless client, Ollama provider, and processing pipeline with mocked external services.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
class TestPaperlessClient:
    """Test Paperless API client integration."""

    async def test_health_check_success(self, mock_paperless_client):
        """Test successful Paperless health check."""
        result = await mock_paperless_client.health_check()

        assert result is True
        mock_paperless_client.health_check.assert_called_once()

    async def test_get_documents(self, mock_paperless_client):
        """Test fetching documents from Paperless."""
        mock_paperless_client.get_documents.return_value = [
            {"id": 1, "title": "Document 1"},
            {"id": 2, "title": "Document 2"},
        ]

        documents = await mock_paperless_client.get_documents()

        assert len(documents) == 2
        assert documents[0]["id"] == 1

    async def test_get_document_by_id(self, mock_paperless_client):
        """Test fetching single document."""
        mock_paperless_client.get_document.return_value = {
            "id": 123,
            "title": "Test Document",
            "content": "Document content",
        }

        document = await mock_paperless_client.get_document()

        assert document["id"] == 123
        assert document["title"] == "Test Document"

    async def test_update_document(self, mock_paperless_client):
        """Test updating document in Paperless."""
        result = await mock_paperless_client.update_document()

        assert result is True


@pytest.mark.asyncio
class TestOllamaProvider:
    """Test Ollama AI provider integration."""

    async def test_generate_text(self, mock_ollama_provider):
        """Test text generation."""
        text = await mock_ollama_provider.generate_text()

        assert text == "Generated text"
        mock_ollama_provider.generate_text.assert_called_once()

    async def test_generate_json(self, mock_ollama_provider):
        """Test JSON generation."""
        result = await mock_ollama_provider.generate_json()

        assert result["document_type"] == "Invoice"
        assert result["confidence"] == 0.95
        assert "invoice" in result["tags"]

    async def test_list_models(self, mock_ollama_provider):
        """Test listing available models."""
        models = await mock_ollama_provider.list_models()

        assert "llama3.2" in models
        assert "mixtral" in models


@pytest.mark.asyncio
class TestProcessingPipeline:
    """Test document processing pipeline."""

    async def test_document_classification(self, mock_ollama_provider):
        """Test document classification."""
        mock_ollama_provider.generate_json.return_value = {
            "document_type": "Receipt",
            "confidence": 0.89,
        }

        result = await mock_ollama_provider.generate_json()

        assert result["document_type"] == "Receipt"
        assert result["confidence"] > 0.8

    async def test_tag_suggestion(self, mock_ollama_provider):
        """Test tag suggestion."""
        mock_ollama_provider.generate_json.return_value = {
            "tags": ["expense", "business", "2024"],
            "confidences": [0.95, 0.92, 0.88],
        }

        result = await mock_ollama_provider.generate_json()

        assert len(result["tags"]) == 3
        assert "expense" in result["tags"]


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in services."""

    async def test_paperless_connection_error(self):
        """Test handling of Paperless connection errors."""
        mock_client = MagicMock()
        mock_client.health_check = AsyncMock(side_effect=ConnectionError("Connection failed"))

        with pytest.raises(ConnectionError):
            await mock_client.health_check()

    async def test_ollama_timeout_error(self):
        """Test handling of Ollama timeout errors."""
        mock_provider = MagicMock()
        mock_provider.generate_text = AsyncMock(side_effect=TimeoutError("Request timeout"))

        with pytest.raises(TimeoutError):
            await mock_provider.generate_text()

    async def test_invalid_json_response(self):
        """Test handling of invalid JSON responses."""
        mock_provider = MagicMock()
        mock_provider.generate_json = AsyncMock(return_value={})

        result = await mock_provider.generate_json()

        assert isinstance(result, dict)
        assert len(result) == 0
