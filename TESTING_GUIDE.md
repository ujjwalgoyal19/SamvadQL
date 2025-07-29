# SamvadQL Testing Guide

This guide explains how to test all the components we've implemented for the SamvadQL text-to-SQL system.

## Overview

We've implemented comprehensive testing for:

- ✅ **Backend Python Components**: Data models, database utilities, repositories, migrations
- ✅ **Frontend TypeScript Types**: API interfaces, validation utilities, WebSocket types
- ✅ **Integration Testing**: End-to-end component interaction
- ✅ **Validation Logic**: Input sanitization, type safety, business rules

## Quick Start - Test Everything

### 1. Backend Testing (No Database Required)

```bash
cd backend
python test_runner.py
```

This comprehensive test runner will:

- Test all Pydantic data models and validation
- Test database connection utilities (mocked)
- Test repository implementations
- Test migration system
- Test async operations
- Test frontend type compatibility

### 2. Backend Unit Tests (With pytest)

```bash
cd backend
python -m pytest tests/ -v
```

This runs the full pytest suite with:

- `test_models.py` - 33 tests for data model validation
- `test_database.py` - Database connection and utilities tests
- `test_repositories.py` - Repository implementation tests
- `test_migrations.py` - Migration system tests

### 3. Frontend Validation Testing

```bash
cd frontend
node test-validation.js
```

This tests:

- Client-side validation utilities
- TypeScript interface compatibility
- Form validation logic
- WebSocket message types

## Detailed Testing Instructions

### Backend Components

#### 1. Data Models Testing

**What's tested:**

- Pydantic V2 validation for all models
- Input sanitization (XSS prevention)
- Format validation (UUIDs, table names, etc.)
- Business rule validation
- Type safety and consistency checks

**Run specific tests:**

```bash
cd backend
python -m pytest tests/test_models.py -v
```

**Key test cases:**

- ✅ Valid data model creation
- ✅ Invalid input rejection
- ✅ XSS content detection
- ✅ Primary key constraints
- ✅ Field length limits
- ✅ Consistency validation

#### 2. Database Utilities Testing

**What's tested:**

- Database URL parsing
- Connection configuration
- Connection pooling setup
- Health checks
- Query execution (mocked)

**Run specific tests:**

```bash
cd backend
python -m pytest tests/test_database.py -v
```

#### 3. Repository Testing

**What's tested:**

- CRUD operations for all entities
- Data conversion (to_dict/from_dict)
- Query methods with filters
- Statistics and analytics queries
- Error handling

**Run specific tests:**

```bash
cd backend
python -m pytest tests/test_repositories.py -v
```

#### 4. Migration System Testing

**What's tested:**

- Migration file creation and parsing
- Migration application and rollback
- Migration status tracking
- SQL execution (mocked)

**Run specific tests:**

```bash
cd backend
python -m pytest tests/test_migrations.py -v
```

### Frontend Components

#### 1. TypeScript Type Validation

**What's tested:**

- API interface compatibility
- WebSocket message types
- Form validation utilities
- Client-side input sanitization

**Run tests:**

```bash
cd frontend
node test-validation.js
```

#### 2. React Component Integration

The TypeScript files we created include:

- `QueryEditor.tsx` - Demonstrates form validation integration
- `useWebSocket.ts` - WebSocket connection management hook
- Complete type definitions for all API interactions

## Testing with Real Database

### Prerequisites

1. **PostgreSQL Database**

   ```bash
   # Using Docker
   docker run --name samvadql-postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=samvadql -p 5432:5432 -d postgres:15

   # Or install PostgreSQL locally
   ```

2. **Environment Setup**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env and set DATABASE_URL=postgresql://postgres:password@localhost:5432/samvadql
   ```

### Database Testing Steps

1. **Install Dependencies**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run Migrations**

   ```bash
   cd backend
   python migrations/cli.py status
   python migrations/cli.py up
   ```

3. **Test Database Connection**

   ```bash
   cd backend
   python -c "
   import asyncio
   from core.db.manager import get_database_manager

   async def test():
       db = await get_database_manager()
       healthy = await db.health_check()
       print(f'Database healthy: {healthy}')

   asyncio.run(test())
   "
   ```

4. **Test Repository Operations**

   ```bash
   cd backend
   python -c "
   import asyncio
   from repositories.user_feedback import UserFeedbackRepository
   from models.base import UserFeedback
   from uuid import uuid4

   async def test():
       repo = UserFeedbackRepository()
       feedback = UserFeedback(
           user_id='test_user',
           query_id=str(uuid4()),
           original_query='Show me all users',
           generated_sql='SELECT * FROM users',
           feedback_type='accept',
           rating=5
       )
       result = await repo.create(feedback)
       print(f'Created feedback: {result.id}')

   asyncio.run(test())
   "
   ```

5. **Test FastAPI Endpoints**

   ```bash
   cd backend
   uvicorn main:app --reload

   # In another terminal, test endpoints:
   curl http://localhost:8000/health
   curl http://localhost:8000/api/v1/status
   ```

## Integration Testing

### End-to-End Workflow Test

```bash
cd backend
python -c "
import asyncio
from uuid import uuid4
from models.base import QueryRequest, UserFeedback
from repositories.user_feedback import UserFeedbackRepository
from repositories.audit_log import AuditLogRepository

async def test_workflow():
    # 1. Create a query request
    request = QueryRequest(
        query='Show me all users from last month',
        user_id='test_user',
        database_id=str(uuid4()),
        selected_tables=['users']
    )
    print(f'✅ Created query request: {request.request_id}')

    # 2. Log the action
    audit_repo = AuditLogRepository()
    await audit_repo.log_action(
        user_id=request.user_id,
        action='query_submitted',
        resource_type='query',
        resource_id=request.request_id,
        details={'query': request.query}
    )
    print('✅ Logged audit entry')

    # 3. Create feedback
    feedback_repo = UserFeedbackRepository()
    feedback = UserFeedback(
        user_id=request.user_id,
        query_id=request.request_id,
        original_query=request.query,
        generated_sql='SELECT * FROM users WHERE created_at >= NOW() - INTERVAL \\'1 month\\'',
        feedback_type='accept',
        rating=5
    )
    await feedback_repo.create(feedback)
    print('✅ Created user feedback')

    print('🎉 End-to-end workflow test completed successfully!')

asyncio.run(test_workflow())
"
```

## Performance Testing

### Load Testing Data Models

```bash
cd backend
python -c "
import time
from models.base import QueryRequest
from uuid import uuid4

# Test validation performance
start_time = time.time()
for i in range(1000):
    request = QueryRequest(
        query=f'Show me data for user {i}',
        user_id=f'user_{i}',
        database_id=str(uuid4())
    )

end_time = time.time()
print(f'Created 1000 validated QueryRequest objects in {end_time - start_time:.3f} seconds')
print(f'Average: {(end_time - start_time) * 1000:.2f}ms per object')
"
```

## Troubleshooting

### Common Issues

1. **Import Errors**

   ```bash
   # Make sure you're in the backend directory
   cd backend
   export PYTHONPATH=$PWD:$PYTHONPATH
   ```

2. **Database Connection Issues**

   ```bash
   # Check if PostgreSQL is running
   docker ps  # if using Docker
   # or
   pg_isready -h localhost -p 5432
   ```

3. **Pydantic Validation Errors**

   - Check that you're using the correct field names
   - Ensure UUIDs are properly formatted
   - Verify that required fields are provided

4. **Migration Issues**

   ```bash
   # Check migration status
   python migrations/cli.py status

   # Reset migrations (careful - this drops data!)
   python migrations/cli.py down 20240101_000000
   ```

## Test Coverage

Our test suite covers:

- **Data Models**: 33 tests covering all validation scenarios
- **Database**: Connection management, pooling, health checks
- **Repositories**: CRUD operations, filtering, statistics
- **Migrations**: File parsing, application, rollback
- **Frontend Types**: Validation utilities, type compatibility
- **Integration**: End-to-end workflows

## Next Steps

After running all tests successfully:

1. **Set up continuous integration** with GitHub Actions
2. **Add performance benchmarks** for query generation
3. **Implement integration tests** with real LLM services
4. **Add frontend unit tests** with Jest/React Testing Library
5. **Set up monitoring** and logging for production

## Success Criteria

✅ All unit tests pass (33+ tests)
✅ Data validation works correctly
✅ Database operations are functional
✅ Migration system works
✅ Frontend types are compatible
✅ Integration workflow completes
✅ Performance is acceptable

If all tests pass, your SamvadQL implementation is ready for the next development phase!
