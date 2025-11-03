"""
Basic tests for LLM service to verify functionality.
"""

import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch

from services.llm_service import LLMProvider, LLMConfig, PromptTemplateManager


def test_llm_provider_enum():
    """Test LLM provider enum values."""
    assert LLMProvider.OPENAI == "openai"
    assert LLMProvider.ANTHROPIC == "anthropic"
    assert LLMProvider.LLAMA == "llama"
    assert LLMProvider.DEEPSEEK == "deepseek"


def test_llm_config_creation():
    """Test LLM config creation with defaults."""
    config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4")

    assert config.provider == LLMProvider.OPENAI
    assert config.model == "gpt-4"
    assert config.temperature == 0.1
    assert config.max_tokens == 2000
    assert config.streaming is True
    assert config.timeout == 30


def test_prompt_template_manager():
    """Test prompt template manager initialization."""
    manager = PromptTemplateManager()

    assert "sql_generation" in manager.templates
    assert "query_refinement" in manager.templates
    assert "sql_correction" in manager.templates

    # Test getting a template
    template = manager.get_template("sql_generation")
    assert template is not None
    assert template.name == "sql_generation"


def test_template_formatting():
    """Test template formatting with variables."""
    manager = PromptTemplateManager()

    variables = {
        "query": "SELECT * FROM users",
        "table_schemas": "Table: users\nColumns: id, name",
        "database_type": "postgresql",
        "context": "test context",
    }

    system_prompt, human_prompt = manager.format_template("sql_generation", variables)

    assert "SELECT * FROM users" in human_prompt
    assert "Table: users" in system_prompt
    assert "postgresql" in system_prompt


@patch("services.llm_service.settings")
def test_llm_service_import(mock_settings):
    """Test that LLM service can be imported and initialized."""
    mock_settings.llm_provider = "openai"
    mock_settings.openai_api_key = None
    mock_settings.anthropic_api_key = None

    # Import should work
    from services.llm_service import LLMService

    # Basic initialization should work (even without API keys)
    with patch("services.llm_service.OllamaClient"):
        service = LLMService()
        assert service.current_provider == LLMProvider.OPENAI
        assert service.template_manager is not None
