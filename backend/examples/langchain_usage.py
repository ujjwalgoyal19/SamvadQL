"""
Example usage of LangChain service for SamvadQL.
"""

import asyncio
from services.langchain_service import LangChainLLMService
from models.base import TableSchema, ColumnSchema


async def example_sql_generation():
    """Example of generating SQL from natural language."""

    # Initialize the service
    llm_service = LangChainLLMService()

    # Create sample table schemas
    users_table = TableSchema(
        name="users",
        database_id="sample_db",
        columns=[
            ColumnSchema(
                name="id",
                data_type="INTEGER",
                description="User ID",
                is_primary_key=True,
                is_nullable=False,
            ),
            ColumnSchema(
                name="email",
                data_type="VARCHAR(255)",
                description="User email address",
                is_nullable=False,
            ),
            ColumnSchema(
                name="created_at",
                data_type="TIMESTAMP",
                description="Account creation date",
                is_nullable=False,
            ),
            ColumnSchema(
                name="is_active",
                data_type="BOOLEAN",
                description="Whether the user account is active",
                is_nullable=False,
            ),
        ],
        description="User accounts table",
        sample_queries=["SELECT * FROM users WHERE is_active = true"],
    )

    orders_table = TableSchema(
        name="orders",
        database_id="sample_db",
        columns=[
            ColumnSchema(
                name="id",
                data_type="INTEGER",
                description="Order ID",
                is_primary_key=True,
                is_nullable=False,
            ),
            ColumnSchema(
                name="user_id",
                data_type="INTEGER",
                description="ID of the user who placed the order",
                is_foreign_key=True,
                is_nullable=False,
            ),
            ColumnSchema(
                name="total_amount",
                data_type="DECIMAL(10,2)",
                description="Total order amount",
                is_nullable=False,
            ),
            ColumnSchema(
                name="order_date",
                data_type="TIMESTAMP",
                description="Date when the order was placed",
                is_nullable=False,
            ),
            ColumnSchema(
                name="status",
                data_type="VARCHAR(50)",
                description="Order status (pending, completed, cancelled)",
                is_nullable=False,
            ),
        ],
        description="Customer orders table",
        sample_queries=["SELECT * FROM orders WHERE status = 'completed'"],
    )

    tables = [users_table, orders_table]

    # Example queries
    queries = [
        "Show me all active users",
        "Find the total revenue from completed orders",
        "Get the top 10 customers by order value",
        "Show me orders placed in the last 30 days",
    ]

    print("🚀 LangChain SQL Generation Examples\n")

    for i, query in enumerate(queries, 1):
        print(f"📝 Query {i}: {query}")
        print("-" * 50)

        try:
            # Generate SQL using LangChain
            response_iterator = await llm_service.generate_sql(
                query=query,
                tables=tables,
                context={"database_type": "postgresql", "request_id": f"example_{i}"},
            )
            async for response in response_iterator:
                print(f"🔍 Generated SQL:")
                print(response.sql)
                print(f"\n💡 Explanation:")
                print(response.explanation)
                print(f"\n📊 Confidence Score: {response.confidence_score}")
                print(f"🏷️  Selected Tables: {', '.join(response.selected_tables)}")
                print(f"✅ Validation Status: {response.validation_status.value}")

                if response.optimization_suggestions:
                    print(f"\n🚀 Optimization Suggestions:")
                    for suggestion in response.optimization_suggestions:
                        print(
                            f"  - {suggestion.description} (Impact: {suggestion.impact})"
                        )

                print("\n" + "=" * 80 + "\n")

        except Exception as e:
            print(f"❌ Error generating SQL: {str(e)}\n")


async def example_query_refinement():
    """Example of refining an existing SQL query."""

    llm_service = LangChainLLMService()

    original_sql = """
    SELECT u.email, COUNT(o.id) as order_count
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    GROUP BY u.email
    ORDER BY order_count DESC
    """

    refinement_requests = [
        "Only include active users",
        "Add the total amount spent by each user",
        "Filter to orders from the last year only",
    ]

    print("🔧 Query Refinement Examples\n")
    print(f"📝 Original SQL:")
    print(original_sql)
    print("\n" + "=" * 80 + "\n")

    current_sql = original_sql

    for i, refinement in enumerate(refinement_requests, 1):
        print(f"🔄 Refinement {i}: {refinement}")
        print("-" * 50)

        try:
            response_iterator = await llm_service.refine_query(
                original_sql=current_sql,
                refinement_request=refinement,
                context={"request_id": f"refinement_{i}"},
            )
            async for response in response_iterator:
                print(f"🔍 Refined SQL:")
                print(response.sql)
                print(f"\n💡 Changes Made:")
                print(response.explanation)
                print("\n" + "=" * 80 + "\n")

                current_sql = response.sql  # Use refined query for next iteration

        except Exception as e:
            print(f"❌ Error refining query: {str(e)}\n")


async def example_sql_correction():
    """Example of correcting invalid SQL."""

    llm_service = LangChainLLMService()

    invalid_queries = [
        {
            "sql": "SELECT * FROM user WHERE email = 'test@example.com'",
            "error": "Table 'user' doesn't exist. Did you mean 'users'?",
        },
        {
            "sql": "SELECT COUNT(*) FROM orders GROUP BY user_id HAVING COUNT > 5",
            "error": "Invalid use of aggregate function COUNT in HAVING clause",
        },
        {
            "sql": "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id",
            "error": "Column 'name' doesn't exist in table 'users'",
        },
    ]

    print("🔧 SQL Correction Examples\n")

    for i, example in enumerate(invalid_queries, 1):
        print(f"❌ Invalid SQL {i}:")
        print(example["sql"])
        print(f"\n🚨 Error: {example['error']}")
        print("-" * 50)

        try:
            corrected_sql = await llm_service.correct_sql(
                invalid_sql=example["sql"],
                error_message=example["error"],
                context={"request_id": f"correction_{i}"},
            )

            print(f"✅ Corrected SQL:")
            print(corrected_sql)
            print("\n" + "=" * 80 + "\n")

        except Exception as e:
            print(f"❌ Error correcting SQL: {str(e)}\n")


async def main():
    """Run all examples."""
    print("🎯 SamvadQL LangChain Service Examples")
    print("=" * 80 + "\n")

    try:
        await example_sql_generation()
        await example_query_refinement()
        await example_sql_correction()

        print("✅ All examples completed successfully!")

    except Exception as e:
        print(f"❌ Error running examples: {str(e)}")


if __name__ == "__main__":
    # Note: Make sure to set your environment variables before running
    # export OPENAI_API_KEY=your-api-key-here
    # or
    # export ANTHROPIC_API_KEY=your-api-key-here

    asyncio.run(main())
