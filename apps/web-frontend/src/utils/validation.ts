/**
 * Client-side validation utilities for form data and API requests
 */

import { QueryRequest, TableSchema, UserFeedback } from '../types/api';

// Validation error interface
export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

// Validation result interface
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

// Query validation
export function validateQuery(query: string): ValidationResult {
  const errors: ValidationError[] = [];

  // Check if query is empty or whitespace only
  if (!query || query.trim().length === 0) {
    errors.push({
      field: 'query',
      message: 'Query cannot be empty',
      code: 'QUERY_EMPTY'
    });
  }

  // Check query length
  if (query.length > 10000) {
    errors.push({
      field: 'query',
      message: 'Query is too long (maximum 10,000 characters)',
      code: 'QUERY_TOO_LONG'
    });
  }

  // NOTE: Client-side XSS validation using regex is not reliable and may be bypassed.
  // For robust protection, use a library like DOMPurify for sanitizing user input,
  // and always enforce server-side validation as the primary defense mechanism.
  // Example (if DOMPurify is installed):
  // import DOMPurify from 'dompurify';
  // if (DOMPurify.sanitize(query) !== query) {
  //   errors.push({
  //     field: 'query',
  //     message: 'Query contains potentially unsafe content',
  //     code: 'QUERY_UNSAFE_CONTENT'
  //   });
  // }

  return {
    isValid: errors.length === 0,
    errors
  };
}

// User ID validation
export function validateUserId(userId: string): ValidationResult {
  const errors: ValidationError[] = [];

  if (!userId || userId.trim().length === 0) {
    errors.push({
      field: 'user_id',
      message: 'User ID is required',
      code: 'USER_ID_REQUIRED'
    });
  } else {
    // Check format (alphanumeric, underscores, hyphens only)
    if (!/^[a-zA-Z0-9_-]+$/.test(userId)) {
      errors.push({
        field: 'user_id',
        message:
          'User ID can only contain letters, numbers, underscores, and hyphens',
        code: 'USER_ID_INVALID_FORMAT'
      });
    }

    // Check length
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

// Database ID validation (UUID format)
export function validateDatabaseId(databaseId: string): ValidationResult {
  const errors: ValidationError[] = [];

  if (!databaseId || databaseId.trim().length === 0) {
    errors.push({
      field: 'database_id',
      message: 'Database ID is required',
      code: 'DATABASE_ID_REQUIRED'
    });
  } else {
    // Check UUID format
    const uuidRegex =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
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

// Selected tables validation
export function validateSelectedTables(tables: string[]): ValidationResult {
  const errors: ValidationError[] = [];

  if (tables.length > 50) {
    errors.push({
      field: 'selected_tables',
      message: 'Too many selected tables (maximum 50)',
      code: 'SELECTED_TABLES_TOO_MANY'
    });
  }

  // Validate each table name format
  const tableNameRegex = /^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$/;
  for (const table of tables) {
    if (!tableNameRegex.test(table)) {
      errors.push({
        field: 'selected_tables',
        message: `Invalid table name format: ${table}`,
        code: 'SELECTED_TABLES_INVALID_FORMAT'
      });
      break; // Only show first invalid table name
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

// Query request validation
export function validateQueryRequest(
  request: Partial<QueryRequest>
): ValidationResult {
  const allErrors: ValidationError[] = [];

  // Validate query
  if (request.query !== undefined) {
    const queryValidation = validateQuery(request.query);
    allErrors.push(...queryValidation.errors);
  }

  // Validate user_id
  if (request.user_id !== undefined) {
    const userIdValidation = validateUserId(request.user_id);
    allErrors.push(...userIdValidation.errors);
  }

  // Validate database_id
  if (request.database_id !== undefined) {
    const databaseIdValidation = validateDatabaseId(request.database_id);
    allErrors.push(...databaseIdValidation.errors);
  }

  // Validate selected_tables
  if (request.selected_tables !== undefined) {
    const tablesValidation = validateSelectedTables(request.selected_tables);
    allErrors.push(...tablesValidation.errors);
  }

  return {
    isValid: allErrors.length === 0,
    errors: allErrors
  };
}

// Feedback validation
export function validateFeedback(
  feedback: Partial<UserFeedback>
): ValidationResult {
  const errors: ValidationError[] = [];

  // Validate feedback type
  if (feedback.feedback_type !== undefined) {
    const validTypes = ['accept', 'reject', 'modify'];
    if (!validTypes.includes(feedback.feedback_type)) {
      errors.push({
        field: 'feedback_type',
        message: 'Invalid feedback type',
        code: 'FEEDBACK_TYPE_INVALID'
      });
    }
  }

  // Validate rating
  if (feedback.rating !== undefined) {
    if (feedback.rating < 1 || feedback.rating > 5) {
      errors.push({
        field: 'rating',
        message: 'Rating must be between 1 and 5',
        code: 'RATING_OUT_OF_RANGE'
      });
    }
  }

  // Validate comments length
  if (feedback.comments !== undefined && feedback.comments.length > 2000) {
    errors.push({
      field: 'comments',
      message: 'Comments are too long (maximum 2000 characters)',
      code: 'COMMENTS_TOO_LONG'
    });
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

// Table schema validation
export function validateTableSchema(
  schema: Partial<TableSchema>
): ValidationResult {
  const errors: ValidationError[] = [];

  // Validate table name
  if (schema.name !== undefined) {
    if (!schema.name || schema.name.trim().length === 0) {
      errors.push({
        field: 'name',
        message: 'Table name is required',
        code: 'TABLE_NAME_REQUIRED'
      });
    } else {
      const nameRegex = /^[a-zA-Z_][a-zA-Z0-9_]*$/;
      if (!nameRegex.test(schema.name)) {
        errors.push({
          field: 'name',
          message:
            'Table name must start with a letter or underscore and contain only alphanumeric characters and underscores',
          code: 'TABLE_NAME_INVALID_FORMAT'
        });
      }
    }
  }

  // Validate database_id
  if (schema.database_id !== undefined) {
    const databaseIdValidation = validateDatabaseId(schema.database_id);
    errors.push(...databaseIdValidation.errors);
  }

  // Validate columns
  if (schema.columns !== undefined) {
    if (schema.columns.length === 0) {
      errors.push({
        field: 'columns',
        message: 'Table must have at least one column',
        code: 'COLUMNS_REQUIRED'
      });
    }
  }

  // Validate tier
  if (schema.tier !== undefined) {
    const validTiers = ['gold', 'silver', 'bronze', 'deprecated'];
    if (!validTiers.includes(schema.tier.toLowerCase())) {
      errors.push({
        field: 'tier',
        message: 'Invalid table tier',
        code: 'TIER_INVALID'
      });
    }
  }

  // Validate tags
  if (schema.tags !== undefined) {
    if (schema.tags.length > 20) {
      errors.push({
        field: 'tags',
        message: 'Too many tags (maximum 20)',
        code: 'TAGS_TOO_MANY'
      });
    }

    for (const tag of schema.tags) {
      if (tag.length > 50) {
        errors.push({
          field: 'tags',
          message: 'Tag is too long (maximum 50 characters)',
          code: 'TAG_TOO_LONG'
        });
        break;
      }

      if (!/^[a-zA-Z0-9_-]+$/.test(tag)) {
        errors.push({
          field: 'tags',
          message:
            'Tags can only contain letters, numbers, underscores, and hyphens',
          code: 'TAG_INVALID_FORMAT'
        });
        break;
      }
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

// Utility function to format validation errors for display
export function formatValidationErrors(errors: ValidationError[]): string[] {
  return errors.map((error) => error.message);
}

// Utility function to get errors for a specific field
export function getFieldErrors(
  errors: ValidationError[],
  field: string
): ValidationError[] {
  return errors.filter((error) => error.field === field);
}

// Utility function to check if a field has errors
export function hasFieldError(
  errors: ValidationError[],
  field: string
): boolean {
  return errors.some((error) => error.field === field);
}
