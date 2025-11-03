"""Enhanced semantic search and re-ranking service for SamvadQL."""

import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import structlog

from core.config import settings
from services.vector_search_service import VectorSearchService
from services.summarization_service import SummarizationService
from services.embedding_service import EmbeddingService
from models import (
    TableSchema,
    TableRecommendation,
    VectorSearchResult,
    EmbeddingModel,
)

logger = structlog.get_logger(__name__)


class SemanticSearchService:
    """Enhanced semantic search service with advanced ranking and caching."""

    def __init__(self):
        self.vector_search_service: Optional[VectorSearchService] = None
        self.summarization_service: Optional[SummarizationService] = None
        self.embedding_service: Optional[EmbeddingService] = None
        self._initialized = False

        # Caching for frequent searches
        self._search_cache: Dict[str, Tuple[List[TableRecommendation], datetime]] = {}
        self._cache_ttl = timedelta(minutes=30)

        # Scoring weights for re-ranking
        self.scoring_weights = {
            "semantic_similarity": 0.4,
            "table_tier": 0.2,
            "usage_frequency": 0.15,
            "recency": 0.1,
            "column_match": 0.15,
        }

    async def initialize(self) -> None:
        """Initialize the semantic search service."""
        try:
            # Initialize vector search service
            self.vector_search_service = VectorSearchService()
            await self.vector_search_service.initialize()

            # Initialize summarization service
            self.summarization_service = SummarizationService()
            await self.summarization_service.initialize()

            # Initialize embedding service
            self.embedding_service = EmbeddingService()
            await self.embedding_service.initialize()

            self._initialized = True
            logger.info("Semantic search service initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize semantic search service", error=str(e))
            raise

    async def search_tables_with_ranking(
        self,
        query: str,
        database_id: str,
        limit: int = 10,
        use_cache: bool = True,
        include_similar_queries: bool = True,
    ) -> List[TableRecommendation]:
        """
        Perform semantic search with advanced ranking and caching.

        Args:
            query: Natural language query
            database_id: Database identifier
            limit: Maximum number of results
            use_cache: Whether to use cached results
            include_similar_queries: Whether to include similar query analysis

        Returns:
            List of ranked table recommendations
        """
        if not self._initialized:
            raise RuntimeError("Semantic search service not initialized")

        try:
            # Check cache first
            cache_key = f"{database_id}:{query}:{limit}"
            if use_cache and cache_key in self._search_cache:
                cached_results, cached_time = self._search_cache[cache_key]
                if datetime.utcnow() - cached_time < self._cache_ttl:
                    logger.debug("Returning cached search results", query=query)
                    return cached_results

            # Perform initial semantic search
            initial_results = await self.vector_search_service.search_tables(
                query=query,
                database_id=database_id,
                limit=limit * 2,  # Get more results for better re-ranking
            )

            # Enhance results with additional scoring
            enhanced_results = await self._enhance_search_results(
                query, initial_results, include_similar_queries
            )

            # Re-rank results using multiple factors
            ranked_results = await self._rerank_results(query, enhanced_results)

            # Limit to requested number
            final_results = ranked_results[:limit]

            # Cache results
            if use_cache:
                self._search_cache[cache_key] = (final_results, datetime.utcnow())
                # Clean old cache entries
                await self._cleanup_cache()

            logger.info(
                "Completed semantic search with ranking",
                query_length=len(query),
                database_id=database_id,
                initial_results=len(initial_results),
                final_results=len(final_results),
            )

            return final_results

        except Exception as e:
            logger.error("Failed to perform semantic search", query=query, error=str(e))
            return []

    async def find_similar_queries(
        self,
        query: str,
        limit: int = 5,
        min_similarity: float = 0.7,
    ) -> List[VectorSearchResult]:
        """Find similar historical queries for context."""
        if not self._initialized:
            raise RuntimeError("Semantic search service not initialized")

        try:
            similar_queries = await self.vector_search_service.search_similar_queries(
                query=query,
                limit=limit,
            )

            # Filter by minimum similarity
            filtered_queries = [
                result for result in similar_queries if result.score >= min_similarity
            ]

            logger.debug(
                "Found similar queries",
                query_length=len(query),
                total_found=len(similar_queries),
                filtered_count=len(filtered_queries),
            )

            return filtered_queries

        except Exception as e:
            logger.error("Failed to find similar queries", query=query, error=str(e))
            return []

    async def get_query_suggestions(
        self,
        partial_query: str,
        database_id: str,
        limit: int = 5,
    ) -> List[str]:
        """Get query suggestions based on partial input."""
        if not self._initialized:
            raise RuntimeError("Semantic search service not initialized")

        try:
            # Find similar queries
            similar_queries = await self.find_similar_queries(
                partial_query, limit=limit * 2, min_similarity=0.5
            )

            # Extract and rank suggestions
            suggestions = []
            for result in similar_queries:
                if hasattr(result.document, "metadata"):
                    original_query = result.document.metadata.get("original_query")
                    if original_query and original_query not in suggestions:
                        suggestions.append(original_query)

            # Limit results
            return suggestions[:limit]

        except Exception as e:
            logger.error("Failed to get query suggestions", error=str(e))
            return []

    async def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze query intent to improve search results."""
        try:
            # Generate embedding for intent analysis
            query_embedding = await self.embedding_service.generate_embedding(
                query, EmbeddingModel.OPENAI_ADA_002
            )

            # Basic intent analysis based on keywords
            intent = {
                "query_type": self._classify_query_type(query),
                "entities": self._extract_entities(query),
                "operations": self._extract_operations(query),
                "time_references": self._extract_time_references(query),
                "aggregations": self._extract_aggregations(query),
            }

            logger.debug("Analyzed query intent", query=query, intent=intent)
            return intent

        except Exception as e:
            logger.error("Failed to analyze query intent", query=query, error=str(e))
            return {}

    async def _enhance_search_results(
        self,
        query: str,
        initial_results: List[TableRecommendation],
        include_similar_queries: bool,
    ) -> List[Dict[str, Any]]:
        """Enhance search results with additional metadata for ranking."""
        enhanced_results = []

        for result in initial_results:
            enhanced = {
                "recommendation": result,
                "semantic_score": result.relevance_score,
                "tier_score": self._calculate_tier_score(result.table_schema.tier),
                "column_match_score": await self._calculate_column_match_score(
                    query, result.table_schema
                ),
                "usage_frequency_score": 0.5,  # Placeholder - would come from usage analytics
                "recency_score": 0.5,  # Placeholder - would come from table metadata
            }

            # Add similar query context if requested
            if include_similar_queries:
                enhanced["similar_queries_score"] = (
                    await self._calculate_similar_queries_score(
                        query, result.table_schema.name
                    )
                )
            else:
                enhanced["similar_queries_score"] = 0.0

            enhanced_results.append(enhanced)

        return enhanced_results

    async def _rerank_results(
        self,
        query: str,
        enhanced_results: List[Dict[str, Any]],
    ) -> List[TableRecommendation]:
        """Re-rank results using weighted scoring."""
        # Calculate composite scores
        for result in enhanced_results:
            composite_score = (
                result["semantic_score"] * self.scoring_weights["semantic_similarity"]
                + result["tier_score"] * self.scoring_weights["table_tier"]
                + result["usage_frequency_score"]
                * self.scoring_weights["usage_frequency"]
                + result["recency_score"] * self.scoring_weights["recency"]
                + result["column_match_score"] * self.scoring_weights["column_match"]
            )
            result["composite_score"] = composite_score

        # Sort by composite score
        enhanced_results.sort(key=lambda x: x["composite_score"], reverse=True)

        # Update recommendations with new scores and reasons
        ranked_recommendations = []
        for result in enhanced_results:
            recommendation = result["recommendation"]

            # Update relevance score with composite score
            recommendation.relevance_score = result["composite_score"]

            # Update match reason with detailed explanation
            factors = []
            if result["semantic_score"] > 0.8:
                factors.append("high semantic similarity")
            if result["tier_score"] > 0.8:
                factors.append("high-tier table")
            if result["column_match_score"] > 0.7:
                factors.append("strong column match")

            recommendation.match_reason = f"Composite score: {result['composite_score']:.3f} ({', '.join(factors)})"

            ranked_recommendations.append(recommendation)

        return ranked_recommendations

    def _calculate_tier_score(self, tier: Optional[str]) -> float:
        """Calculate score based on table tier."""
        tier_scores = {
            "gold": 1.0,
            "silver": 0.7,
            "bronze": 0.4,
            "deprecated": 0.1,
        }
        return tier_scores.get(tier.lower() if tier else "", 0.5)

    async def _calculate_column_match_score(
        self,
        query: str,
        table_schema: TableSchema,
    ) -> float:
        """Calculate score based on column name matches."""
        try:
            # Extract potential column references from query
            query_words = set(query.lower().split())

            # Get column names
            column_names = set(col.name.lower() for col in table_schema.columns)

            # Calculate overlap
            matches = query_words.intersection(column_names)
            if not column_names:
                return 0.0

            # Score based on percentage of columns mentioned
            score = len(matches) / len(column_names)
            return min(score, 1.0)

        except Exception as e:
            logger.error("Failed to calculate column match score", error=str(e))
            return 0.0

    async def _calculate_similar_queries_score(
        self,
        query: str,
        table_name: str,
    ) -> float:
        """Calculate score based on similar historical queries."""
        try:
            # Find similar queries
            similar_queries = await self.find_similar_queries(query, limit=5)

            # Count how many similar queries used this table
            table_mentions = 0
            for result in similar_queries:
                if hasattr(result.document, "metadata"):
                    tables_used = result.document.metadata.get("tables_used", [])
                    if table_name in tables_used:
                        table_mentions += 1

            # Score based on frequency of table usage in similar queries
            if similar_queries:
                return table_mentions / len(similar_queries)
            return 0.0

        except Exception as e:
            logger.error("Failed to calculate similar queries score", error=str(e))
            return 0.0

    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query based on keywords."""
        query_lower = query.lower()

        # Check temporal first as it's more specific
        if any(
            word in query_lower for word in ["trend", "over time", "change", "growth"]
        ):
            return "temporal"
        elif any(
            word in query_lower
            for word in ["count", "sum", "average", "total", "aggregate"]
        ):
            return "aggregation"
        elif any(
            word in query_lower for word in ["compare", "difference", "vs", "versus"]
        ):
            return "comparison"
        elif any(
            word in query_lower for word in ["find", "get", "show", "list", "select"]
        ):
            return "retrieval"
        else:
            return "general"

    def _extract_entities(self, query: str) -> List[str]:
        """Extract potential entity names from query."""
        # Simple entity extraction based on capitalized words
        words = query.split()
        entities = []

        for word in words:
            # Remove punctuation
            clean_word = word.strip(".,!?;:")
            # Check if word is capitalized (potential entity)
            if clean_word and clean_word[0].isupper() and len(clean_word) > 2:
                entities.append(clean_word.lower())

        return entities

    def _extract_operations(self, query: str) -> List[str]:
        """Extract database operations from query."""
        query_lower = query.lower()
        operations = []

        operation_keywords = {
            "join": ["join", "combine", "merge", "relate"],
            "filter": ["where", "filter", "only", "specific"],
            "sort": ["sort", "order", "arrange", "rank"],
            "group": ["group", "categorize", "segment"],
            "aggregate": ["count", "sum", "average", "total", "max", "min"],
        }

        for operation, keywords in operation_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                operations.append(operation)

        return operations

    def _extract_time_references(self, query: str) -> List[str]:
        """Extract time references from query."""
        query_lower = query.lower()
        time_refs = []

        time_keywords = [
            "today",
            "yesterday",
            "tomorrow",
            "week",
            "month",
            "year",
            "recent",
            "latest",
            "current",
            "past",
            "future",
            "since",
            "before",
            "after",
            "during",
            "between",
        ]

        for keyword in time_keywords:
            if keyword in query_lower:
                time_refs.append(keyword)

        return time_refs

    def _extract_aggregations(self, query: str) -> List[str]:
        """Extract aggregation functions from query."""
        query_lower = query.lower()
        aggregations = []

        agg_keywords = ["count", "sum", "average", "avg", "max", "min", "total"]

        for keyword in agg_keywords:
            if keyword in query_lower:
                aggregations.append(keyword)

        return aggregations

    async def _cleanup_cache(self) -> None:
        """Clean up expired cache entries."""
        current_time = datetime.utcnow()
        expired_keys = [
            key
            for key, (_, cached_time) in self._search_cache.items()
            if current_time - cached_time > self._cache_ttl
        ]

        for key in expired_keys:
            del self._search_cache[key]

        if expired_keys:
            logger.debug("Cleaned up expired cache entries", count=len(expired_keys))

    async def clear_cache(self) -> None:
        """Clear all cached search results."""
        self._search_cache.clear()
        logger.info("Cleared search cache")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = datetime.utcnow()
        active_entries = 0
        expired_entries = 0

        for _, (_, cached_time) in self._search_cache.items():
            if current_time - cached_time < self._cache_ttl:
                active_entries += 1
            else:
                expired_entries += 1

        return {
            "total_entries": len(self._search_cache),
            "active_entries": active_entries,
            "expired_entries": expired_entries,
            "cache_ttl_minutes": self._cache_ttl.total_seconds() / 60,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on semantic search service."""
        status = {
            "initialized": self._initialized,
            "vector_search_service": None,
            "summarization_service": None,
            "embedding_service": None,
            "cache_stats": await self.get_cache_stats(),
        }

        try:
            if self.vector_search_service:
                status["vector_search_service"] = (
                    await self.vector_search_service.health_check()
                )

            if self.summarization_service:
                status["summarization_service"] = (
                    await self.summarization_service.health_check()
                )

            if self.embedding_service:
                status["embedding_service"] = (
                    await self.embedding_service.health_check()
                )

        except Exception as e:
            status["health_check_error"] = str(e)

        return status
