"""
LLM service abstraction for SamvadQL.

This module provides a unified interface for different LLM providers including
OpenAI, Llama, and DeepSeek with support for streaming responses, prompt template
management, and response optimization.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional, Dict, Any, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, Field
from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain.callbacks.base import BaseCallbackHandler
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama

from core.config import settings
from models import (
    QueryRequest,
    QueryResponse,
    TableSchema,
    ValidationStatus,
    DatabaseType,
)

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LLAMA = "llama"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"


class PromptTemplate(BaseModel):
    """Template for LLM prompts with variable substitution."""

    name: str
    system_template: str
    human_template: str
    variables: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StreamingResponse(BaseModel):
    """Streaming response chunk from LLM."""

    content: str
    is_complete: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""

    provider: LLMProvider
    model: str
    temperature: float = 0.1
    max_tokens: int = 2000
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    streaming: bool = True
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming LLM responses."""

    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.tokens = []

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Handle new token from LLM."""
        self.tokens.append(token)
        self.callback(token)

    def on_llm_end(self, response, **kwargs) -> None:
        """Handle LLM completion."""
        self.callback("")  # Signal completion


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._initialize_client()

    @abstractmethod
    def _initialize_client(self) -> None:
        """Initialize the LLM client."""
        pass

    @abstractmethod
    async def generate_stream(
        self, messages: List[BaseMessage], **kwargs
    ) -> AsyncIterator[StreamingResponse]:
        """Generate streaming response from messages."""
        pass

    @abstractmethod
    async def generate(self, messages: List[BaseMessage], **kwargs) -> str:
        """Generate non-streaming response from messages."""
        pass

    async def health_check(self) -> bool:
        """Check if the LLM client is healthy."""
        try:
            test_messages = [HumanMessage(content="Hello")]
            response = await self.generate(test_messages)
            return bool(response and len(response.strip()) > 0)
        except Exception as e:
            logger.error(f"Health check failed for {self.config.provider}: {e}")
            return False


class OpenAIClient(BaseLLMClient):
    """OpenAI LLM client implementation."""

    def _initialize_client(self) -> None:
        """Initialize OpenAI client."""
        self.client = ChatOpenAI(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            api_key=self.config.api_key,
            streaming=self.config.streaming,
            request_timeout=self.config.timeout,
        )

    async def generate_stream(
        self, messages: List[BaseMessage], **kwargs
    ) -> AsyncIterator[StreamingResponse]:
        """Generate streaming response from OpenAI."""
        try:
            content_buffer = ""
            async for chunk in self.client.astream(messages, **kwargs):
                if chunk.content:
                    content_buffer += chunk.content
                    yield StreamingResponse(
                        content=chunk.content,
                        is_complete=False,
                        metadata={"provider": "openai", "model": self.config.model},
                    )

            # Final response
            yield StreamingResponse(
                content="",
                is_complete=True,
                metadata={
                    "provider": "openai",
                    "model": self.config.model,
                    "total_content": content_buffer,
                },
            )
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield StreamingResponse(
                content=f"Error: {str(e)}",
                is_complete=True,
                metadata={"error": True, "provider": "openai"},
            )

    async def generate(self, messages: List[BaseMessage], **kwargs) -> str:
        """Generate non-streaming response from OpenAI."""
        try:
            response = await self.client.ainvoke(messages, **kwargs)
            return response.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return f"Error: {str(e)}"


class AnthropicClient(BaseLLMClient):
    """Anthropic LLM client implementation."""

    def _initialize_client(self) -> None:
        """Initialize Anthropic client."""
        self.client = ChatAnthropic(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            anthropic_api_key=self.config.api_key,
            streaming=self.config.streaming,
        )

    async def generate_stream(
        self, messages: List[BaseMessage], **kwargs
    ) -> AsyncIterator[StreamingResponse]:
        """Generate streaming response from Anthropic."""
        try:
            content_buffer = ""
            async for chunk in self.client.astream(messages, **kwargs):
                if chunk.content:
                    content_buffer += chunk.content
                    yield StreamingResponse(
                        content=chunk.content,
                        is_complete=False,
                        metadata={"provider": "anthropic", "model": self.config.model},
                    )

            yield StreamingResponse(
                content="",
                is_complete=True,
                metadata={
                    "provider": "anthropic",
                    "model": self.config.model,
                    "total_content": content_buffer,
                },
            )
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            yield StreamingResponse(
                content=f"Error: {str(e)}",
                is_complete=True,
                metadata={"error": True, "provider": "anthropic"},
            )

    async def generate(self, messages: List[BaseMessage], **kwargs) -> str:
        """Generate non-streaming response from Anthropic."""
        try:
            response = await self.client.ainvoke(messages, **kwargs)
            return response.content
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            return f"Error: {str(e)}"


class OllamaClient(BaseLLMClient):
    """Ollama LLM client implementation for local models like Llama."""

    def _initialize_client(self) -> None:
        """Initialize Ollama client."""
        self.client = ChatOllama(
            model=self.config.model,
            temperature=self.config.temperature,
            base_url=self.config.base_url or "http://localhost:11434",
        )

    async def generate_stream(
        self, messages: List[BaseMessage], **kwargs
    ) -> AsyncIterator[StreamingResponse]:
        """Generate streaming response from Ollama."""
        try:
            content_buffer = ""
            async for chunk in self.client.astream(messages, **kwargs):
                if chunk.content:
                    content_buffer += chunk.content
                    yield StreamingResponse(
                        content=chunk.content,
                        is_complete=False,
                        metadata={"provider": "ollama", "model": self.config.model},
                    )

            yield StreamingResponse(
                content="",
                is_complete=True,
                metadata={
                    "provider": "ollama",
                    "model": self.config.model,
                    "total_content": content_buffer,
                },
            )
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield StreamingResponse(
                content=f"Error: {str(e)}",
                is_complete=True,
                metadata={"error": True, "provider": "ollama"},
            )

    async def generate(self, messages: List[BaseMessage], **kwargs) -> str:
        """Generate non-streaming response from Ollama."""
        try:
            response = await self.client.ainvoke(messages, **kwargs)
            return response.content
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return f"Error: {str(e)}"


class PromptTemplateManager:
    """Manages prompt templates for different use cases."""

    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """Load default prompt templates."""
        # SQL Generation Template
        self.templates["sql_generation"] = PromptTemplate(
            name="sql_generation",
            system_template="""You are an expert SQL query generator. Your task is to convert natural language questions into precise SQL queries.

Available Tables and Schemas:
{table_schemas}

Guidelines:
1. Generate syntactically correct SQL for {database_type}
2. Use only the tables and columns provided in the schema
3. Include clear explanations for your SQL choices
4. Consider performance implications
5. Avoid destructive operations unless explicitly requested
6. Return response in JSON format with 'sql' and 'explanation' fields

Context: {context}""",
            human_template="""Convert this natural language question to SQL:

Question: {query}

Please provide a JSON response with:
1. "sql": The SQL query
2. "explanation": A clear explanation of what the query does
3. "selected_tables": List of tables used
4. "confidence": Confidence score (0.0-1.0)""",
            variables=["table_schemas", "database_type", "context", "query"],
        )

        # Query Refinement Template
        self.templates["query_refinement"] = PromptTemplate(
            name="query_refinement",
            system_template="""You are an expert SQL query refiner. Your task is to modify existing SQL queries based on user feedback.

Original SQL Query:
{original_sql}

User's Refinement Request:
{refinement_request}

Guidelines:
1. Understand what the user wants to change
2. Modify the SQL query accordingly
3. Maintain the original intent while incorporating the changes
4. Explain what changes were made and why
5. Ensure the refined query is syntactically correct
6. Return response in JSON format

Context: {context}""",
            human_template="""Please refine the SQL query based on the user's request. Provide a JSON response with:
1. "sql": The refined SQL query
2. "explanation": Explanation of changes made
3. "changes": List of specific modifications
4. "confidence": Confidence score (0.0-1.0)""",
            variables=["original_sql", "refinement_request", "context"],
        )

        # SQL Correction Template
        self.templates["sql_correction"] = PromptTemplate(
            name="sql_correction",
            system_template="""You are an expert SQL debugger. Your task is to fix broken SQL queries.

Invalid SQL Query:
{invalid_sql}

Error Message:
{error_message}

Guidelines:
1. Analyze the error message to understand the issue
2. Fix the SQL syntax or logic error
3. Ensure the corrected query maintains the original intent
4. Explain what was wrong and how it was fixed
5. Return response in JSON format

Context: {context}""",
            human_template="""Please fix this SQL query and provide a JSON response with:
1. "sql": The corrected SQL query
2. "explanation": What was wrong and how it was fixed
3. "error_type": Type of error that was corrected
4. "confidence": Confidence score (0.0-1.0)""",
            variables=["invalid_sql", "error_message", "context"],
        )

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name."""
        return self.templates.get(name)

    def add_template(self, template: PromptTemplate) -> None:
        """Add a new prompt template."""
        self.templates[template.name] = template

    def format_template(
        self, template_name: str, variables: Dict[str, Any]
    ) -> tuple[str, str]:
        """Format a template with variables."""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        system_prompt = template.system_template.format(**variables)
        human_prompt = template.human_template.format(**variables)

        return system_prompt, human_prompt


class LLMService:
    """Main LLM service with provider abstraction and streaming support."""

    def __init__(self):
        self.clients: Dict[LLMProvider, BaseLLMClient] = {}
        self.template_manager = PromptTemplateManager()
        self.current_provider = LLMProvider(settings.llm_provider)
        self._initialize_clients()

    def _initialize_clients(self) -> None:
        """Initialize all configured LLM clients."""
        # OpenAI
        if settings.openai_api_key:
            config = LLMConfig(
                provider=LLMProvider.OPENAI,
                model=(
                    settings.llm_model if settings.llm_provider == "openai" else "gpt-4"
                ),
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                api_key=settings.openai_api_key,
            )
            self.clients[LLMProvider.OPENAI] = OpenAIClient(config)

        # Anthropic
        if settings.anthropic_api_key:
            config = LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model=(
                    settings.llm_model
                    if settings.llm_provider == "anthropic"
                    else "claude-3-sonnet-20240229"
                ),
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                api_key=settings.anthropic_api_key,
            )
            self.clients[LLMProvider.ANTHROPIC] = AnthropicClient(config)

        # Ollama for local models (Llama, DeepSeek, etc.)
        config = LLMConfig(
            provider=LLMProvider.OLLAMA,
            model=(
                settings.llm_model
                if settings.llm_provider in ["llama", "deepseek", "ollama"]
                else "llama2"
            ),
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
        self.clients[LLMProvider.OLLAMA] = OllamaClient(config)

    def get_client(self, provider: Optional[LLMProvider] = None) -> BaseLLMClient:
        """Get LLM client for specified provider."""
        provider = provider or self.current_provider

        # Map provider names to actual clients
        if provider in [LLMProvider.LLAMA, LLMProvider.DEEPSEEK]:
            provider = LLMProvider.OLLAMA

        client = self.clients.get(provider)
        if not client:
            raise ValueError(f"No client configured for provider: {provider}")

        return client

    async def generate_sql_stream(
        self,
        query: str,
        tables: List[TableSchema],
        database_type: DatabaseType = DatabaseType.POSTGRESQL,
        context: Optional[Dict[str, Any]] = None,
        provider: Optional[LLMProvider] = None,
    ) -> AsyncIterator[QueryResponse]:
        """Generate SQL with streaming response."""
        try:
            client = self.get_client(provider)

            # Format table schemas
            table_schemas_text = self._format_table_schemas(tables)

            # Prepare template variables
            variables = {
                "query": query,
                "table_schemas": table_schemas_text,
                "database_type": database_type.value,
                "context": json.dumps(context) if context else "None",
            }

            # Get formatted prompts
            system_prompt, human_prompt = self.template_manager.format_template(
                "sql_generation", variables
            )

            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]

            # Stream response
            content_buffer = ""
            async for chunk in client.generate_stream(messages):
                content_buffer += chunk.content

                if chunk.is_complete:
                    # Parse final response
                    try:
                        response_data = json.loads(
                            chunk.metadata.get("total_content", content_buffer)
                        )
                        yield QueryResponse(
                            sql=response_data.get("sql", ""),
                            explanation=response_data.get("explanation", ""),
                            confidence_score=response_data.get("confidence", 0.8),
                            selected_tables=response_data.get(
                                "selected_tables", [table.name for table in tables]
                            ),
                            validation_status=ValidationStatus.VALID,
                            optimization_suggestions=[],
                            execution_time_estimate=0,
                        )
                    except json.JSONDecodeError:
                        # Fallback parsing
                        sql, explanation = self._parse_llm_response(content_buffer)
                        yield QueryResponse(
                            sql=sql,
                            explanation=explanation,
                            confidence_score=0.7,
                            selected_tables=[table.name for table in tables],
                            validation_status=ValidationStatus.VALID,
                            optimization_suggestions=[],
                            execution_time_estimate=0,
                        )
                else:
                    # Intermediate streaming response
                    yield QueryResponse(
                        sql="-- Generating SQL...",
                        explanation=f"Processing: {chunk.content}",
                        confidence_score=0.0,
                        selected_tables=[],
                        validation_status=ValidationStatus.PENDING,
                        optimization_suggestions=[],
                        execution_time_estimate=0,
                    )

        except Exception as e:
            logger.error(f"SQL generation error: {e}")
            yield QueryResponse(
                sql="-- Error generating SQL",
                explanation=f"Error: {str(e)}",
                confidence_score=0.0,
                selected_tables=[],
                validation_status=ValidationStatus.INVALID,
                optimization_suggestions=[],
                execution_time_estimate=0,
            )

    async def refine_query_stream(
        self,
        original_sql: str,
        refinement_request: str,
        context: Optional[Dict[str, Any]] = None,
        provider: Optional[LLMProvider] = None,
    ) -> AsyncIterator[QueryResponse]:
        """Refine SQL query with streaming response."""
        try:
            client = self.get_client(provider)

            variables = {
                "original_sql": original_sql,
                "refinement_request": refinement_request,
                "context": json.dumps(context) if context else "None",
            }

            system_prompt, human_prompt = self.template_manager.format_template(
                "query_refinement", variables
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]

            content_buffer = ""
            async for chunk in client.generate_stream(messages):
                content_buffer += chunk.content

                if chunk.is_complete:
                    try:
                        response_data = json.loads(
                            chunk.metadata.get("total_content", content_buffer)
                        )
                        yield QueryResponse(
                            sql=response_data.get("sql", original_sql),
                            explanation=response_data.get(
                                "explanation", "Query refined"
                            ),
                            confidence_score=response_data.get("confidence", 0.8),
                            selected_tables=[],
                            validation_status=ValidationStatus.VALID,
                            optimization_suggestions=[],
                            execution_time_estimate=0,
                        )
                    except json.JSONDecodeError:
                        sql, explanation = self._parse_llm_response(content_buffer)
                        yield QueryResponse(
                            sql=sql or original_sql,
                            explanation=explanation,
                            confidence_score=0.7,
                            selected_tables=[],
                            validation_status=ValidationStatus.VALID,
                            optimization_suggestions=[],
                            execution_time_estimate=0,
                        )
                else:
                    yield QueryResponse(
                        sql=original_sql,
                        explanation=f"Refining: {chunk.content}",
                        confidence_score=0.0,
                        selected_tables=[],
                        validation_status=ValidationStatus.PENDING,
                        optimization_suggestions=[],
                        execution_time_estimate=0,
                    )

        except Exception as e:
            logger.error(f"Query refinement error: {e}")
            yield QueryResponse(
                sql=original_sql,
                explanation=f"Error refining query: {str(e)}",
                confidence_score=0.0,
                selected_tables=[],
                validation_status=ValidationStatus.INVALID,
                optimization_suggestions=[],
                execution_time_estimate=0,
            )

    async def correct_sql(
        self,
        invalid_sql: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
        provider: Optional[LLMProvider] = None,
    ) -> str:
        """Correct invalid SQL query."""
        try:
            client = self.get_client(provider)

            variables = {
                "invalid_sql": invalid_sql,
                "error_message": error_message,
                "context": json.dumps(context) if context else "None",
            }

            system_prompt, human_prompt = self.template_manager.format_template(
                "sql_correction", variables
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]

            response = await client.generate(messages)

            try:
                response_data = json.loads(response)
                return response_data.get("sql", invalid_sql)
            except json.JSONDecodeError:
                # Fallback parsing
                sql, _ = self._parse_llm_response(response)
                return sql or invalid_sql

        except Exception as e:
            logger.error(f"SQL correction error: {e}")
            return f"-- Unable to correct SQL: {str(e)}\n{invalid_sql}"

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all configured LLM clients."""
        health_status = {}

        for provider, client in self.clients.items():
            try:
                health_status[provider.value] = await client.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {provider}: {e}")
                health_status[provider.value] = False

        return health_status

    def _format_table_schemas(self, tables: List[TableSchema]) -> str:
        """Format table schemas for prompt inclusion."""
        formatted_schemas = []

        for table in tables:
            schema_text = f"Table: {table.name}\n"
            if table.description:
                schema_text += f"Description: {table.description}\n"

            schema_text += "Columns:\n"
            for column in table.columns:
                col_info = f"  - {column.name} ({column.data_type})"
                if column.description:
                    col_info += f" - {column.description}"
                if hasattr(column, "is_primary_key") and column.is_primary_key:
                    col_info += " [PRIMARY KEY]"
                if hasattr(column, "is_foreign_key") and column.is_foreign_key:
                    col_info += " [FOREIGN KEY]"
                schema_text += col_info + "\n"

            if hasattr(table, "sample_queries") and table.sample_queries:
                schema_text += (
                    f"Sample queries: {', '.join(table.sample_queries[:3])}\n"
                )

            formatted_schemas.append(schema_text)

        return "\n".join(formatted_schemas)

    def _parse_llm_response(self, response: str) -> tuple[str, str]:
        """Parse LLM response to extract SQL and explanation."""
        lines = response.strip().split("\n")

        sql_lines = []
        explanation_lines = []
        in_sql_block = False

        for line in lines:
            if "```sql" in line.lower():
                in_sql_block = True
                continue
            elif "```" in line and in_sql_block:
                in_sql_block = False
                continue
            elif in_sql_block:
                sql_lines.append(line)
            else:
                explanation_lines.append(line)

        sql = "\n".join(sql_lines).strip() if sql_lines else response
        explanation = (
            "\n".join(explanation_lines).strip()
            if explanation_lines
            else "SQL query generated"
        )

        return sql, explanation
