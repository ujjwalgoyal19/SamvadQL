# Quick Start Guide

Get started with SamvadQL in 5 minutes! This guide will walk you through your first text-to-SQL conversion.

## Step 1: Access the Interface

After [installation](./installation.md), open your browser and navigate to:

```
http://localhost:3000
```

You should see the SamvadQL interface with a query editor.

## Step 2: Connect a Database

Before generating SQL, you need to connect a database:

1. Click the **"Database Settings"** button in the top navigation
2. Choose your database type (PostgreSQL, MySQL, Snowflake, or BigQuery)
3. Enter your connection details:

```json
{
  "name": "My Database",
  "type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "username": "user",
  "password": "password"
}
```

4. Click **"Test Connection"** to verify
5. Click **"Save"** to store the configuration

## Step 3: Your First Query

Now let's generate your first SQL query:

1. In the query editor, type a natural language question:

   ```
   Show me all users who signed up in the last 30 days
   ```

2. Click **"Generate SQL"** or press `Ctrl+Enter`

3. Watch as SamvadQL streams the SQL generation in real-time:

   ```sql
   SELECT *
   FROM users
   WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
   ORDER BY created_at DESC;
   ```

4. Review the explanation provided below the SQL

## Step 4: Execute the Query

Once you're satisfied with the generated SQL:

1. Click **"Execute Query"** to run it against your database
2. View the results in the table below
3. Use the export options to download results as CSV, JSON, or Excel

## Step 5: Refine Your Query

SamvadQL supports conversational refinement:

1. Type a follow-up question:

   ```
   Only show users from the United States
   ```

2. The AI will modify the existing query:
   ```sql
   SELECT *
   FROM users
   WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
     AND country = 'United States'
   ORDER BY created_at DESC;
   ```

## Example Queries to Try

Here are some example natural language queries you can try:

### Basic Queries

- "Show me all products"
- "Count the number of orders"
- "Find users with email addresses containing 'gmail'"

### Aggregations

- "What's the average order value by month?"
- "Show me the top 10 customers by total spending"
- "Count orders grouped by status"

### Joins

- "Show me orders with customer names and email addresses"
- "List products with their category names"
- "Find customers who haven't placed any orders"

### Time-based Queries

- "Show sales for the last quarter"
- "Find orders placed yesterday"
- "What's the monthly revenue trend for this year?"

## Understanding the Interface

### Query Editor

- **Input Area**: Type your natural language questions
- **SQL Output**: Generated SQL appears here with syntax highlighting
- **Explanation**: AI-generated explanation of what the query does

### Result Viewer

- **Data Table**: Query results with sorting and filtering
- **Pagination**: Navigate through large result sets
- **Export Options**: Download results in various formats

### Schema Browser

- **Tables**: Browse available tables and their columns
- **Search**: Find specific tables or columns quickly
- **Metadata**: View table descriptions and column types

## Tips for Better Results

### Be Specific

Instead of: "Show me sales"
Try: "Show me total sales by product category for the last month"

### Use Domain Language

Instead of: "Show me the table with people"
Try: "Show me all customers" or "Show me all users"

### Provide Context

Instead of: "Show me recent data"
Try: "Show me orders from the last 7 days"

### Iterate and Refine

- Start with a simple query
- Add filters and conditions in follow-up questions
- Use the conversation history to build complex queries

## Common Patterns

### Filtering Data

```
Show me [table] where [condition]
Find [table] with [criteria]
List [table] that [condition]
```

### Aggregating Data

```
Count the number of [table]
What's the average [column] by [group]?
Show me the total [column] for each [group]
```

### Joining Tables

```
Show me [table1] with their [table2] information
List [table1] and their related [table2] data
Find [table1] that have [table2]
```

## Next Steps

Now that you've completed your first query:

- [Configuration Guide](./configuration.md) - Customize SamvadQL settings
- [Architecture Overview](../architecture/overview.md) - Learn how SamvadQL works
- [API Reference](../api/overview.md) - Integrate with your applications
- [Development Guide](../development/setup.md) - Contribute to SamvadQL

## Getting Help

If you run into issues:

- Check the [troubleshooting guide](../development/troubleshooting.md)
- Review [common error messages](../development/troubleshooting.md#common-errors)
- [Ask questions](https://github.com/your-org/samvadql/discussions) in our community
