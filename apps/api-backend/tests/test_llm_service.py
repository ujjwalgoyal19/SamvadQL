"""
Unit tests for LLM service abstraction.
"""

import pytest
import json
import uuid
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import AsyncIterator, List

from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage

from services.llm_service import (
    LLMService,
    LLMProvider,
    LLMConfig,
    OpenAIClient,
    AnthropicClient,
    OllamaClient,
    PromptTemplateManager,
    PromptTemplate,
    StreamingResponse,
    StreamingCallbackHandler,
)
from models import (
    QueryResponse,
    TableSchema,
    ColumnSchema,
    DatabaseType,
    ValidationStatus,
)


# Test constants
TEST_DB_ID = str(uuid.uuid4())


class TestLLMConfig:
    """Test LLM configuration."""

    def test_llm_config_creation(self):
        """Test LLM config creation with defaults."""
        config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4")

        assert config.provider == LLMProvider.OPENAI
        assert config.model == "gpt-4"
        assert config.temperature == 0.1
        assert config.max_tokens == 2000
        assert config.streaming is True
        assert config.timeout == 30


class TestPromptTemplateManager:
    """Test prompt template manager."""

    def test_template_manager_initialization(self):
        """Test template manager loads default templates."""
        manager = PromptTemplateManager()

        assert "sql_generation" in manager.templates
        assert "query_refinement" in manager.templates
        assert "sql_correction" in manager.templates

    def test_format_template(self):
        """Test template formatting with variables."""
        manager = PromptTemplateManager()

        variables = {
            "query": "SELECT * FROM users",
            "table_schemas": "Table: users\nColumns: id, name",
            "database_type": "postgresql",
            "context": "test context",
        }

        system_prompt, human_prompt = manager.format_template(
            "sql_generation", variables
        )

        assert "SELECT * FROM users" in human_prompt
        assert "Table: users" in system_prompt
        assert "postgresql" in system_prompt


class TestOpenAIClient:
    """Test OpenAI client implementation."""

    @patch("services.llm_service.ChatOpenAI")
    def test_openai_client_initialization(self, mock_chat_openai):
        """Test OpenAI client initialization."""
        config = LLMConfig(
            provider=LLMProvider.OPENAI, model="gpt-4", api_key="test-key"
        )

        client = OpenAIClient(config)

        mock_chat_openai.assert_called_once_with(
            model="gpt-4",
            temperature=0.1,
            max_tokens=2000,
            api_key="test-key",
            streaming=True,
            request_timeout=30,
        )

    @patch("services.llm_service.ChatOpenAI")
    @pytest.mark.asyncio
    async def test_openai_generate_stream(self, mock_chat_openai):
        """Test OpenAI streaming generation."""
        # Mock the streaming response
        mock_chunk1 = Mock()
        mock_chunk1.content = "SELECT"
        mock_chunk2 = Mock()
        mock_chunk2.content = " * FROM users"

        async def mock_astream(*args, **kwargs):
            yield mock_chunk1
            yield mock_chunk2

        mock_client = AsyncMock()
        mock_client.astream = mock_astream
        mock_chat_openai.return_value = mock_client

        config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4")
        client = OpenAIClient(config)

        messages = [HumanMessage(content="Test query")]
        responses = []

        async for response in client.generate_stream(messages):
            responses.append(response)

        assert len(responses) == 3  # 2 chunks + 1 completion
        assert responses[0].content == "SELECT"
        assert responses[1].content == " * FROM users"
        assert responses[2].is_complete is True
        assert responses[2].metadata["total_content"] == "SELECT * FROM users"


class TestLLMService:
    """Test main LLM service."""

    @patch("services.llm_service.OpenAIClient")
    @patch("services.llm_service.settings")
    def test_llm_service_initialization(self, mock_settings, mock_openai_client):
        """Test LLM service initialization."""
        mock_settings.llm_provider = "openai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.1
        mock_settings.llm_max_tokens = 2000
        mock_settings.openai_api_key = "test-key"
        mock_settings.anthropic_api_key = None

        service = LLMService()

        assert service.current_provider == LLMProvider.OPENAI
        assert LLMProvider.OPENAI in service.clients
        mock_openai_client.assert_called_once()

    @patch("services.llm_service.OpenAIClient")
    @patch("services.llm_service.settings")
    @pytest.mark.asyncio
    async def test_generate_sql_stream(self, mock_settings, mock_openai_client):
        """Test SQL generation with streaming."""
        # Setup mocks
        mock_settings.llm_provider = "openai"
        mock_settings.openai_api_key = "test-key"
        mock_settings.anthropic_api_key = None

        # Create mock table schema
        table = TableSchema(
            name="users",
            database_id=TEST_DB_ID,
            columns=[
                ColumnSchema(name="id", data_type="INTEGER"),
                ColumnSchema(name="name", data_type="VARCHAR(100)"),
            ],
        )

        # Mock streaming response
        mock_response = StreamingResponse(
            content='{"sql": "SELECT * FROM users", "explanation": "Select all users", "confidence": 0.9}',
            is_complete=True,
            metadata={
                "total_content": '{"sql": "SELECT * FROM users", "explanation": "Select all users", "confidence": 0.9}'
            },
        )

        async def mock_generate_stream(*args, **kwargs):
            yield mock_response

        mock_client = AsyncMock()
        mock_client.generate_stream = mock_generate_stream
        mock_openai_client.return_value = mock_client

        service = LLMService()

        responses = []
        async for response in service.generate_sql_stream(
            query="Show all users", tables=[table]
        ):
            responses.append(response)

        assert len(responses) == 1
        assert responses[0].sql == "SELECT * FROM users"
        assert responses[0].explanation == "Select all users"
        assert responses[0].confidence_score == 0.9

    @patch("services.llm_service.settings")
    def test_format_table_schemas(self, mock_settings):
        """Test table schema formatting."""
        mock_settings.llm_provider = "openai"
        mock_settings.openai_api_key = "test-key"
        mock_settings.anthropic_api_key = None

        tables = [
            TableSchema(
                name="users",
                database_id=TEST_DB_ID,
                description="User information",
                columns=[
                    ColumnSchema(name="id", data_type="INTEGER", description="User ID"),
                    ColumnSchema(
                        name="name", data_type="VARCHAR(100)", description="User name"
                    ),
                ],
            )
        ]

        with patch("services.llm_service.OllamaClient"):
            service = LLMService()
            formatted = service._format_table_schemas(tables)

            assert "Table: users" in formatted
            assert "Description: User information" in formatted
            assert "id (INTEGER) - User ID" in formatted


@pytest.fixture
def sample_table_schema():
    """Sample table schema for testing."""
    return TableSchema(
        name="users",
        database_id=TEST_DB_ID,
        description="User information table",
        columns=[
            ColumnSchema(name="id", data_type="INTEGER", description="Primary key"),
            ColumnSchema(
                name="name", data_type="VARCHAR(100)", description="User full name"
            ),
        ],
    )
