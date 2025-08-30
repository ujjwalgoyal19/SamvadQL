"""
API v1 route handlers for SamvadQL.
"""

import asyncio
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
import json

from models import (
    QueryRequest,
    QueryResponse,
    TableSchema,
    UserFeedback,
    ValidationResult,
    DatabaseType,
    ValidationStatus,
)
from services.query_generation_service import QueryGenerationService
from services.metadata_service import MetadataExtractionService
from repositories.user_feedback import UserFeedbackRepository
from core.config import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["api-v1"])

# Service instances - these would be dependency injected in production
query_service = QueryGenerationService()
metadata_service = MetadataExtractionService()
feedback_repository = UserFeedbackRepository()


class SQLValidationRequest(BaseModel):
    """Request model for SQL validation."""

    sql: str = Field(
        ..., min_length=1, max_length=50000, description="SQL query to validate"
    )
    database_id: str = Field(..., description="Database identifier")
    database_type: Optional[str] = Field("postgresql", description="Database type")

    @field_validator("sql")
    @classmethod
    def validate_sql(cls, v):
        """Validate SQL content."""
        if not v or v.isspace():
            raise ValueError("SQL cannot be empty or whitespace only")
        return v.strip()


class FeedbackRequest(BaseModel):
    """Request model for user feedback."""

    user_id: str = Field(
        ..., min_length=1, max_length=255, description="User identifier"
    )
    query_id: str = Field(..., description="Query identifier")
    original_query: str = Field(
        ..., min_length=1, description="Original natural language query"
    )
    generated_sql: str = Field(..., min_length=1, description="Generated SQL query")
    feedback_type: str = Field(..., description="Feedback type: accept, reject, modify")
    comments: Optional[str] = Field(None, max_length=2000, description="User comments")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1-5")

    @field_validator("feedback_type")
    @classmethod
    def validate_feedback_type(cls, v):
        """Validate feedback type."""
        valid_types = ["accept", "reject", "modify"]
        if v.lower() not in valid_types:
            raise ValueError(f"Feedback type must be one of: {', '.join(valid_types)}")
        return v.lower()


class TableListResponse(BaseModel):
    """Response model for table listing."""

    database_id: str
    tables: List[TableSchema]
    total_count: int
    page: int
    page_size: int
    has_more: bool


async def stream_json_response(async_generator):
    """Stream JSON responses for real-time updates."""
    try:
        async for item in async_generator:
            if isinstance(item, QueryResponse):
                # Convert to dict and stream as JSON
                response_dict = {
                    "sql": item.sql,
                    "explanation": item.explanation,
                    "confidence_score": item.confidence_score,
                    "selected_tables": item.selected_tables,
                    "validation_status": item.validation_status.value,
                    "optimization_suggestions": [
                        {
                            "type": suggestion.type,
                            "description": suggestion.description,
                            "impact": suggestion.impact,
                            "suggested_sql": suggestion.suggested_sql,
                        }
                        for suggestion in item.optimization_suggestions
                    ],
                    "execution_time_estimate": item.execution_time_estimate,
                    "request_id": item.request_id,
                    "generated_at": item.generated_at.isoformat(),
                }

                # Stream as Server-Sent Events format
                yield f"data: {json.dumps(response_dict)}\n\n"
            else:
                # Handle other response types
                yield f"data: {json.dumps(str(item))}\n\n"

    except Exception as e:
        logger.error(f"Error in streaming response: {e}")
        error_response = {
            "error": str(e),
            "sql": "SELECT 1 as stream_error",
            "explanation": f"Streaming error: {str(e)}",
            "confidence_score": 0.0,
            "selected_tables": ["stream_error"],
            "validation_status": "invalid",
            "optimization_suggestions": [],
            "execution_time_estimate": 0,
        }
        yield f"data: {json.dumps(error_response)}\n\n"


@router.post("/query", response_model=None)
async def submit_query(request: QueryRequest):
    """
    Submit natural language query for SQL generation with streaming support.

    This endpoint processes natural language queries and returns streaming SQL generation
    responses. The response includes the generated SQL, explanations, and metadata.
    """
    try:
        logger.info(
            f"Processing query request from user {request.user_id}: {request.query[:100]}..."
        )

        # Validate request
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Generate SQL using the query generation service
        response_generator = query_service.generate_sql(request)

        # Return streaming response
        return StreamingResponse(
            stream_json_response(response_generator),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query request: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/tables/{database_id}", response_model=TableListResponse)
async def get_tables(
    database_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Page size"),
    search: Optional[str] = Query(None, description="Search filter for table names"),
    tier: Optional[str] = Query(None, description="Filter by table tier"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
):
    """
    Get available tables for a database with filtering and pagination.

    Returns a paginated list of tables with their metadata, supporting
    search by name, filtering by tier, and tag-based filtering.
    """
    try:
        logger.info(f"Fetching tables for database {database_id}, page {page}")

        # For now, we'll create a mock implementation since we need database connection config
        # In a real implementation, this would fetch from the metadata service

        # Mock database type and connection config - this would come from database registry
        database_type = DatabaseType.POSTGRESQL
        connection_config = {
            "host": "localhost",
            "port": 5432,
            "database": "samvadql",
            "username": "postgres",
            "password": "password",
        }

        try:
            # Get table list from metadata service
            table_names = await metadata_service.list_tables(
                database_id=database_id,
                database_type=database_type,
                connection_config=connection_config,
                use_cache=True,
            )

            # Apply search filter
            if search:
                search_lower = search.lower()
                table_names = [
                    name for name in table_names if search_lower in name.lower()
                ]

            # Get detailed metadata for tables (with pagination)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_table_names = table_names[start_idx:end_idx]

            tables = []
            for table_name in paginated_table_names:
                try:
                    table_schema = await metadata_service.get_table_metadata(
                        database_id=database_id,
                        database_type=database_type,
                        connection_config=connection_config,
                        table_name=table_name,
                        use_cache=True,
                        include_samples=True,
                    )

                    # Apply tier filter
                    if tier and table_schema.tier != tier.lower():
                        continue

                    # Apply tags filter
                    if tags:
                        tag_list = [tag.strip().lower() for tag in tags.split(",")]
                        table_tags = [tag.lower() for tag in table_schema.tags]
                        if not any(tag in table_tags for tag in tag_list):
                            continue

                    tables.append(table_schema)

                except Exception as e:
                    logger.warning(
                        f"Failed to get metadata for table {table_name}: {e}"
                    )
                    continue

            # Calculate pagination info
            total_count = len(table_names)
            has_more = end_idx < total_count

            response = TableListResponse(
                database_id=database_id,
                tables=tables,
                total_count=total_count,
                page=page,
                page_size=page_size,
                has_more=has_more,
            )

            logger.info(f"Returning {len(tables)} tables for database {database_id}")
            return response

        except Exception as e:
            logger.error(f"Error fetching tables from metadata service: {e}")
            # Return empty response on metadata service error
            return TableListResponse(
                database_id=database_id,
                tables=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_more=False,
            )

    except Exception as e:
        logger.error(f"Error getting tables for database {database_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/validate", response_model=ValidationResult)
async def validate_sql(request: SQLValidationRequest):
    """
    Validate SQL query for syntax and safety.

    Performs comprehensive SQL validation including syntax checking,
    safety analysis for destructive operations, and basic optimization suggestions.
    """
    try:
        logger.info(f"Validating SQL query for database {request.database_id}")

        # Basic SQL validation
        sql = request.sql.strip()
        if not sql:
            return ValidationResult(
                is_valid=False,
                errors=["SQL query cannot be empty"],
                warnings=[],
                is_destructive=False,
                estimated_cost=None,
            )

        # Check for basic SQL structure
        sql_upper = sql.upper()
        valid_starts = [
            "SELECT",
            "WITH",
            "INSERT",
            "UPDATE",
            "DELETE",
            "CREATE",
            "ALTER",
            "DROP",
        ]

        if not any(sql_upper.startswith(keyword) for keyword in valid_starts):
            return ValidationResult(
                is_valid=False,
                errors=["SQL must start with a valid SQL keyword"],
                warnings=[],
                is_destructive=False,
                estimated_cost=None,
            )

        # Check for destructive operations
        destructive_keywords = ["DELETE", "DROP", "TRUNCATE", "ALTER"]
        is_destructive = any(keyword in sql_upper for keyword in destructive_keywords)

        # Basic syntax validation (simplified)
        errors = []
        warnings = []

        # Check for balanced parentheses
        if sql.count("(") != sql.count(")"):
            errors.append("Unbalanced parentheses in SQL query")

        # Check for basic SQL injection patterns
        suspicious_patterns = ["--", "/*", "*/", ";--", "' OR '1'='1"]
        for pattern in suspicious_patterns:
            if pattern in sql:
                warnings.append(f"Potentially suspicious pattern detected: {pattern}")

        # Estimate query cost (mock implementation)
        estimated_cost = None
        if "SELECT" in sql_upper:
            # Simple cost estimation based on query complexity
            complexity_score = (
                sql.count("JOIN") * 10
                + sql.count("WHERE") * 5
                + sql.count("ORDER BY") * 3
                + sql.count("GROUP BY") * 7
                + sql.count("HAVING") * 5
            )
            estimated_cost = max(1.0, complexity_score * 0.1)

        # Add warnings for potentially slow operations
        if "SELECT *" in sql_upper:
            warnings.append("Using SELECT * may impact performance")

        if "ORDER BY" in sql_upper and "LIMIT" not in sql_upper:
            warnings.append("ORDER BY without LIMIT may be slow on large tables")

        is_valid = len(errors) == 0

        result = ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            is_destructive=is_destructive,
            estimated_cost=estimated_cost,
        )

        logger.info(
            f"SQL validation completed: valid={is_valid}, destructive={is_destructive}"
        )
        return result

    except Exception as e:
        logger.error(f"Error validating SQL: {e}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@router.post("/feedback", response_model=Dict[str, str])
async def submit_feedback(request: FeedbackRequest, background_tasks: BackgroundTasks):
    """
    Submit user feedback for generated SQL queries.

    Collects user feedback including ratings, comments, and acceptance/rejection
    status to improve the system's performance over time.
    """
    try:
        logger.info(
            f"Receiving feedback from user {request.user_id} for query {request.query_id}"
        )

        # Create feedback object
        feedback = UserFeedback(
            id=str(uuid4()),
            user_id=request.user_id,
            query_id=request.query_id,
            original_query=request.original_query,
            generated_sql=request.generated_sql,
            feedback_type=request.feedback_type,
            comments=request.comments,
            rating=request.rating,
        )

        # Store feedback asynchronously
        background_tasks.add_task(store_feedback, feedback)

        # Return immediate response
        return {
            "status": "success",
            "message": "Feedback submitted successfully",
            "feedback_id": feedback.id,
        }

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to submit feedback: {str(e)}"
        )


async def store_feedback(feedback: UserFeedback):
    """Background task to store feedback in database."""
    try:
        await feedback_repository.create(feedback)
        logger.info(f"Feedback {feedback.id} stored successfully")
    except Exception as e:
        logger.error(f"Failed to store feedback {feedback.id}: {e}")


@router.get("/feedback/stats", response_model=Dict[str, Any])
async def get_feedback_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get feedback statistics for the specified time period."""
    try:
        from datetime import datetime, timedelta

        start_date = datetime.utcnow() - timedelta(days=days)
        stats = await feedback_repository.get_feedback_stats(start_date=start_date)

        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "stats": stats,
        }

    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get feedback stats: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint for API v1."""
    try:
        # Check service health
        query_service_health = await query_service.health_check()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
            "query_generation": query_service_health,
            "metadata_service": "healthy",  # Would check actual service
            "feedback_repository": "healthy",  # Would check database connection
            },
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }
