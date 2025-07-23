"""
LangChain-based LLM service implementation for SamvadQL.
"""

from typing import AsyncIterator, List, Optional, Dict, Any, Coroutine
from pydantic.v1 import SecretStr
from langchain.schema import BaseMessage, HumanMessage
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatAnthropic
from langchain.chains import LLMChain
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.memory import ConversationBufferMemory

from core.interfaces import LLMServiceInterface
from core.config import settings
from models.base import (
    QueryRequest,
    QueryResponse,
    TableSchema,
    ValidationStatus,
)


class LangChainLLMService(LLMServiceInterface):
    """LangChain-based implementation of LLM service."""

    def __init__(self):
        self.llm = self._initialize_llm()
        self.memory = ConversationBufferMemory(return_messages=True)

    def _initialize_llm(self):
        """Initialize the appropriate LLM based on configuration."""
        if settings.llm_provider == "openai":

            return ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                api_key=(
                    SecretStr(settings.openai_api_key)
                    if settings.openai_api_key is not None
                    else None
                ),
                streaming=True,
            )
        elif settings.llm_provider == "anthropic":
            return ChatAnthropic(
                model_name=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                anthropic_api_key=(
                    SecretStr(settings.anthropic_api_key)
                    if settings.anthropic_api_key is not None
                    else None
                ),
                streaming=True,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

    async def generate_sql(
        self,
        query: str,
        tables: List[TableSchema],
        context: Optional[Dict[str, Any]] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None,
    ) -> AsyncIterator[QueryResponse]:
        """Generate SQL from natural language query using LangChain."""

        system_template = """You are an expert SQL query generator. Your task is to convert natural language questions into precise SQL queries.

Available Tables and Schemas:
{table_schemas}

Guidelines:
1. Generate syntactically correct SQL for the specified database type
2. Use only the tables and columns provided in the schema
3. Include clear explanations for your SQL choices
4. Consider performance implications
5. Avoid destructive operations unless explicitly requested

Database Type: {database_type}
Context: {context}"""

        human_template = """Convert this natural language question to SQL:

Question: {query}

Please provide:
1. The SQL query
2. A clear explanation of what the query does
3. Which tables and columns you selected and why"""

        system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        table_schemas_text = self._format_table_schemas(tables)

        chain = LLMChain(llm=self.llm, prompt=chat_prompt, memory=self.memory)

        chain_input = {
            "query": query,
            "table_schemas": table_schemas_text,
            "database_type": (
                context.get("database_type", "postgresql") if context else "postgresql"
            ),
            "context": str(context) if context else "None",
        }

        if callbacks is None:
            callbacks = [StreamingStdOutCallbackHandler()]

        try:
            response = await chain.arun(**chain_input, callbacks=callbacks)
            sql_query, explanation = self._parse_llm_response(response)

            query_response = QueryResponse(
                sql=sql_query,
                explanation=explanation,
                confidence_score=0.8,
                selected_tables=[table.name for table in tables],
                validation_status=ValidationStatus.VALID,
                optimization_suggestions=[],
                request_id=context.get("request_id") if context else None,
            )

            # Instead of yielding, return an async iterator that yields once
            async def single_response():
                yield query_response

            return single_response()
        except Exception as e:
            error_response = QueryResponse(
                sql="-- Error generating SQL",
                explanation=f"Error: {str(e)}",
                confidence_score=0.0,
                selected_tables=[],
                validation_status=ValidationStatus.INVALID,
                optimization_suggestions=[],
                request_id=context.get("request_id") if context else None,
            )

            async def error_response_gen():
                yield error_response

            return error_response_gen()

    async def refine_query(
        self,
        original_sql: str,
        refinement_request: str,
        context: Optional[Dict[str, Any]] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None,
    ) -> AsyncIterator[QueryResponse]:
        """Refine existing SQL query based on user feedback."""

        system_template = """You are an expert SQL query refiner. Your task is to modify existing SQL queries based on user feedback.

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

Context: {context}"""

        human_template = """Please refine the SQL query based on the user's request. Provide:
1. The refined SQL query
2. Explanation of changes made
3. Reasoning for the modifications"""

        # Create and execute chain similar to generate_sql
        system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        chain = LLMChain(llm=self.llm, prompt=chat_prompt)

        chain_input = {
            "original_sql": original_sql,
            "refinement_request": refinement_request,
            "context": str(context) if context else "None",
        }

        try:
            response = await chain.arun(**chain_input, callbacks=callbacks or [])
            sql_query, explanation = self._parse_llm_response(response)

            query_response = QueryResponse(
                sql=sql_query,
                explanation=explanation,
                confidence_score=0.8,
                selected_tables=[],  # Would extract from SQL
                validation_status=ValidationStatus.VALID,
                optimization_suggestions=[],
                request_id=context.get("request_id") if context else None,
            )

            async def single_response():
                yield query_response

            return single_response()

        except Exception as e:
            error_response = QueryResponse(
                sql=original_sql,  # Return original on error
                explanation=f"Error refining query: {str(e)}",
                confidence_score=0.0,
                selected_tables=[],
                validation_status=ValidationStatus.INVALID,
                optimization_suggestions=[],
                request_id=context.get("request_id") if context else None,
            )

            async def error_response_gen():
                yield error_response

            return error_response_gen()

    async def correct_sql(
        self,
        invalid_sql: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Attempt to correct invalid SQL using LangChain."""

        system_template = """You are an expert SQL debugger. Your task is to fix broken SQL queries.

Invalid SQL Query:
{invalid_sql}

Error Message:
{error_message}

Guidelines:
1. Analyze the error message to understand the issue
2. Fix the SQL syntax or logic error
3. Return only the corrected SQL query
4. Ensure the corrected query maintains the original intent

Context: {context}"""

        human_template = (
            """Please fix this SQL query and return only the corrected SQL."""
        )

        system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        chain = LLMChain(llm=self.llm, prompt=chat_prompt)

        chain_input = {
            "invalid_sql": invalid_sql,
            "error_message": error_message,
            "context": str(context) if context else "None",
        }

        try:
            corrected_sql = await chain.arun(**chain_input)
            return corrected_sql.strip()
        except Exception as e:
            return f"-- Unable to correct SQL: {str(e)}\n{invalid_sql}"

    async def create_chain(self, chain_type: str, **kwargs) -> Any:
        """Create a LangChain chain for specific use cases."""

        if chain_type == "sql_generation":
            return self._create_sql_generation_chain(**kwargs)
        elif chain_type == "query_explanation":
            return self._create_query_explanation_chain(**kwargs)
        elif chain_type == "schema_analysis":
            return self._create_schema_analysis_chain(**kwargs)
        else:
            raise ValueError(f"Unknown chain type: {chain_type}")

    async def invoke_with_history(
        self,
        messages: List[BaseMessage],
        callbacks: Optional[List[BaseCallbackHandler]] = None,
    ) -> BaseMessage:
        """Invoke LLM with conversation history."""

        try:
            response = await self.llm.agenerate([messages], callbacks=callbacks or [])
            return HumanMessage(content=response.generations[0][0].text)
        except Exception as e:
            return HumanMessage(content=f"Error: {str(e)}")

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
                if column.is_primary_key:
                    col_info += " [PRIMARY KEY]"
                if column.is_foreign_key:
                    col_info += " [FOREIGN KEY]"
                schema_text += col_info + "\n"

            if table.sample_queries:
                schema_text += (
                    f"Sample queries: {', '.join(table.sample_queries[:3])}\n"
                )

            formatted_schemas.append(schema_text)

        return "\n".join(formatted_schemas)

    def _parse_llm_response(self, response: str) -> tuple[str, str]:
        """Parse LLM response to extract SQL and explanation."""
        # This is a simple parser - in practice, you'd want more robust parsing
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

    def _create_sql_generation_chain(self, **kwargs) -> LLMChain:
        """Create a specialized chain for SQL generation."""
        # Implementation would depend on specific requirements
        pass

    def _create_query_explanation_chain(self, **kwargs) -> LLMChain:
        """Create a specialized chain for query explanation."""
        # Implementation would depend on specific requirements
        pass

    def _create_schema_analysis_chain(self, **kwargs) -> LLMChain:
        """Create a specialized chain for schema analysis."""
        # Implementation would depend on specific requirements
        pass

    # Removed duplicate generate_sql method to avoid obscuring the actual implementation.
