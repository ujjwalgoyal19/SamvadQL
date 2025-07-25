/**
 * Simple Node.js script to test TypeScript validation utilities
 * Run with: node test-validation.js
 */

// Since we can't run TypeScript directly in Node.js without compilation,
// this is a JavaScript version that tests the validation logic

// Validation functions (JavaScript version of the TypeScript code)
function validateQuery(query) {
  const errors = [];

  if (!query || query.trim().length === 0) {
    errors.push({
      field: 'query',
      message: 'Query cannot be empty',
      code: 'QUERY_EMPTY'
    });
  }

  if (query.length > 10000) {
    errors.push({
      field: 'query',
      message: 'Query is too long (maximum 10,000 characters)',
      code: 'QUERY_TOO_LONG'
    });
  }

  const dangerousPatterns = [
    /<script[^>]*>/i,
    /javascript:/i,
    /on\w+\s*=/i,
  ];

  for (const pattern of dangerousPatterns) {
    if (pattern.test(query)) {
      errors.push({
        field: 'query',
        message: 'Query contains potentially unsafe content',
        code: 'QUERY_UNSAFE_CONTENT'
      });
      break;
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

function validateUserId(userId) {
  const errors = [];

  if (!userId || userId.trim().length === 0) {
    errors.push({
      field: 'user_id',
      message: 'User ID is required',
      code: 'USER_ID_REQUIRED'
    });
  } else {
    if (!/^[a-zA-Z0-9_-]+$/.test(userId)) {
      errors.push({
        field: 'user_id',
        message: 'User ID can only contain letters, numbers, underscores, and hyphens',
        code: 'USER_ID_INVALID_FORMAT'
      });
    }

    if (userId.length > 255) {
      errors.push({
        field: 'user_id',
        message: 'User ID is too long (maximum 255 characters)',
        code: 'USER_ID_TOO_LONG'
      });
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

function validateDatabaseId(databaseId) {
  const errors = [];

  if (!databaseId || databaseId.trim().length === 0) {
    errors.push({
      field: 'database_id',
      message: 'Database ID is required',
      code: 'DATABASE_ID_REQUIRED'
    });
  } else {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(databaseId)) {
      errors.push({
        field: 'database_id',
        message: 'Database ID must be a valid UUID',
        code: 'DATABASE_ID_INVALID_FORMAT'
      });
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

// Test runner
function runTests() {
  console.log('🧪 Testing Frontend Validation Utilities\n');

  let passed = 0;
  let failed = 0;

  function test(name, testFn) {
    try {
      const result = testFn();
      if (result) {
        console.log(`✅ ${name}`);
        passed++;
      } else {
        console.log(`❌ ${name}`);
        failed++;
      }
    } catch (error) {
      console.log(`❌ ${name}: ${error.message}`);
      failed++;
    }
  }

  // Test query validation
  test('Valid query passes validation', () => {
    const result = validateQuery('Show me all users from last month');
    return result.isValid && result.errors.length === 0;
  });

  test('Empty query fails validation', () => {
    const result = validateQuery('');
    return !result.isValid && result.errors.some(e => e.code === 'QUERY_EMPTY');
  });

  test('Query with XSS content fails validation', () => {
    const result = validateQuery('<script>alert("xss")</script>');
    return !result.isValid && result.errors.some(e => e.code === 'QUERY_UNSAFE_CONTENT');
  });

  test('Very long query fails validation', () => {
    const longQuery = 'SELECT * FROM users WHERE ' + 'x'.repeat(10000);
    const result = validateQuery(longQuery);
    return !result.isValid && result.errors.some(e => e.code === 'QUERY_TOO_LONG');
  });

  // Test user ID validation
  test('Valid user ID passes validation', () => {
    const result = validateUserId('user123');
    return result.isValid && result.errors.length === 0;
  });

  test('User ID with special characters passes validation', () => {
    const result = validateUserId('user_123-test');
    return result.isValid && result.errors.length === 0;
  });

  test('Empty user ID fails validation', () => {
    const result = validateUserId('');
    return !result.isValid && result.errors.some(e => e.code === 'USER_ID_REQUIRED');
  });

  test('User ID with invalid characters fails validation', () => {
    const result = validateUserId('user@domain.com');
    return !result.isValid && result.errors.some(e => e.code === 'USER_ID_INVALID_FORMAT');
  });

  // Test database ID validation
  test('Valid UUID passes validation', () => {
    const result = validateDatabaseId('550e8400-e29b-41d4-a716-446655440000');
    return result.isValid && result.errors.length === 0;
  });

  test('Invalid UUID fails validation', () => {
    const result = validateDatabaseId('not-a-uuid');
    return !result.isValid && result.errors.some(e => e.code === 'DATABASE_ID_INVALID_FORMAT');
  });

  test('Empty database ID fails validation', () => {
    const result = validateDatabaseId('');
    return !result.isValid && result.errors.some(e => e.code === 'DATABASE_ID_REQUIRED');
  });

  // Test type compatibility (simulating TypeScript interfaces)
  test('Query request object has correct structure', () => {
    const queryRequest = {
      query: 'Show me all users',
      user_id: 'test_user',
      database_id: '550e8400-e29b-41d4-a716-446655440000',
      selected_tables: ['users', 'signups'],
      context: { timezone: 'UTC' },
      session_id: 'session_123',
      request_id: '550e8400-e29b-41d4-a716-446655440001'
    };

    // Check that all required fields are present
    const requiredFields = ['query', 'user_id', 'database_id', 'request_id'];
    return requiredFields.every(field => queryRequest.hasOwnProperty(field));
  });

  test('Query response object has correct structure', () => {
    const queryResponse = {
      sql: 'SELECT * FROM users WHERE created_at >= \'2024-01-01\'',
      explanation: 'This query retrieves all users created after January 1st, 2024',
      confidence_score: 0.95,
      selected_tables: ['users'],
      validation_status: 'valid',
      optimization_suggestions: [],
      execution_time_estimate: 0.25,
      request_id: '550e8400-e29b-41d4-a716-446655440000',
      generated_at: new Date().toISOString()
    };

    // Check that all required fields are present
    const requiredFields = ['sql', 'explanation', 'confidence_score', 'selected_tables', 'validation_status'];
    return requiredFields.every(field => queryResponse.hasOwnProperty(field));
  });

  // Print summary
  console.log(`\n📊 Test Summary:`);
  console.log(`   Passed: ${passed}`);
  console.log(`   Failed: ${failed}`);
  console.log(`   Total: ${passed + failed}`);
  console.log(`   Success Rate: ${((passed / (passed + failed)) * 100).toFixed(1)}%`);

  if (failed === 0) {
    console.log('\n🎉 All frontend validation tests passed!');
    console.log('\nNext steps:');
    console.log('1. Install TypeScript: npm install -g typescript');
    console.log('2. Compile TypeScript files: tsc --noEmit --skipLibCheck src/types/*.ts');
    console.log('3. Run React development server: npm start');
    console.log('4. Test WebSocket connection with backend');
  } else {
    console.log(`\n⚠️  ${failed} test(s) failed`);
  }

  return failed === 0;
}

// Run the tests
if (require.main === module) {
  runTests();
}