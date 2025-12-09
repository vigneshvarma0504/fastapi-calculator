# BREAD Operations Implementation Guide

This document describes the BREAD (Browse, Read, Edit, Add, Delete) operations implementation for the FastAPI Calculator application.

## Overview

The calculator now supports full BREAD operations for managing calculations, with user authentication and authorization. Each user can only access their own calculations.

## API Endpoints

### 1. Browse (GET /calculations)
Retrieve all calculations belonging to the logged-in user.

**Request:**
```bash
GET /calculations?skip=0&limit=100
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "a": 10.0,
    "b": 5.0,
    "type": "Add",
    "result": 15.0,
    "created_at": "2025-12-08T10:30:00Z"
  }
]
```

### 2. Read (GET /calculations/{id})
Retrieve details of a specific calculation by its ID.

**Request:**
```bash
GET /calculations/1
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "a": 10.0,
  "b": 5.0,
  "type": "Add",
  "result": 15.0,
  "created_at": "2025-12-08T10:30:00Z"
}
```

### 3. Add (POST /calculations)
Create a new calculation.

**Request:**
```bash
POST /calculations
Authorization: Bearer <token>
Content-Type: application/json

{
  "a": 10.0,
  "b": 5.0,
  "type": "Add"
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "a": 10.0,
  "b": 5.0,
  "type": "Add",
  "result": 15.0,
  "created_at": "2025-12-08T10:30:00Z"
}
```

### 4. Edit - Full Update (PUT /calculations/{id})
Replace an existing calculation with new data.

**Request:**
```bash
PUT /calculations/1
Authorization: Bearer <token>
Content-Type: application/json

{
  "a": 20.0,
  "b": 4.0,
  "type": "Multiply"
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "a": 20.0,
  "b": 4.0,
  "type": "Multiply",
  "result": 80.0,
  "created_at": "2025-12-08T10:30:00Z"
}
```

### 5. Edit - Partial Update (PATCH /calculations/{id})
Update specific fields of an existing calculation.

**Request:**
```bash
PATCH /calculations/1
Authorization: Bearer <token>
Content-Type: application/json

{
  "b": 10.0
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "a": 20.0,
  "b": 10.0,
  "type": "Multiply",
  "result": 200.0,
  "created_at": "2025-12-08T10:30:00Z"
}
```

### 6. Delete (DELETE /calculations/{id})
Remove a calculation by its ID.

**Request:**
```bash
DELETE /calculations/1
Authorization: Bearer <token>
```

**Response:**
```
HTTP 204 No Content
```

## Supported Operations

- **Add**: Addition (a + b)
- **Sub**: Subtraction (a - b)
- **Multiply**: Multiplication (a × b)
- **Divide**: Division (a ÷ b)

## Validations

### Server-side Validations
- Division by zero is prevented
- All calculations must have valid numeric operands
- Users can only access their own calculations
- Authentication token is required for all operations

### Client-side Validations
- Numeric input validation
- Division by zero check before submission
- Valid operation type selection
- Form field requirements

## Front-end Usage

### Accessing the Calculator
1. Navigate to `http://localhost:8081/login.html`
2. Log in with your credentials
3. You'll be redirected to `calculator.html`

### Using the Calculator Interface

#### Add New Calculation
1. Enter the first number (a)
2. Enter the second number (b)
3. Select the operation type
4. Click "Create Calculation"
5. The result will be displayed and added to the list

#### Browse All Calculations
- Click "Refresh List" to load all your calculations
- View all calculations in a table format
- See ID, operation, operands, result, and creation date

#### Read Specific Calculation
1. Enter the calculation ID
2. Click "Get Calculation"
3. View detailed information in a table

#### Edit Calculation
**Method 1: From the form**
1. Enter the calculation ID
2. Enter new values for a, b, and operation type
3. Click "Update Calculation"

**Method 2: From the table**
1. Click the "Edit" button on any calculation in the list
2. The form will be pre-filled with current values
3. Modify the values as needed
4. Click "Update Calculation"

#### Delete Calculation
**Method 1: From the form**
1. Enter the calculation ID
2. Click "Delete Calculation"
3. Confirm the deletion

**Method 2: From the table**
1. Click the "Delete" button on any calculation in the list
2. Confirm the deletion

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Division by zero is not allowed"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Invalid authentication credentials"
}
```

#### 404 Not Found
```json
{
  "detail": "Calculation not found"
}
```

## Testing

### Running E2E Tests

The project includes comprehensive Playwright E2E tests covering all BREAD operations.

**Prerequisites:**
```bash
# Install Playwright
pip install playwright
playwright install
```

**Start the servers:**
```bash
# Terminal 1: Start backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start frontend
python frontend/serve.py

# Terminal 3: Run tests
pytest tests/e2e/test_calculator_bread.py -v
```

### Test Coverage

The E2E tests cover:

**Positive Scenarios:**
- Creating calculations with all operation types
- Browsing all calculations
- Reading specific calculations
- Editing calculations (PUT and inline edit)
- Deleting calculations (form and inline delete)
- Working with decimal numbers
- Working with negative numbers

**Negative Scenarios:**
- Division by zero prevention
- Invalid number inputs
- Reading non-existent calculations
- Editing non-existent calculations
- Deleting non-existent calculations
- Unauthorized access attempts
- User isolation (users cannot access other users' calculations)
- Expired token handling

**Edge Cases:**
- Decimal numbers
- Negative numbers
- Large numbers
- Zero as operands
- Empty calculation lists

## Database Migration

To add the `user_id` column to existing installations:

```bash
# Run the migration
alembic upgrade head
```

The migration file is located at:
`alembic/versions/0002_add_user_id.py`

## Security Features

1. **JWT Authentication**: All calculation endpoints require valid JWT tokens
2. **User Isolation**: Users can only access their own calculations
3. **Token Validation**: Expired or invalid tokens are rejected
4. **CORS Configuration**: Frontend is allowed from localhost:8081
5. **Password Hashing**: User passwords are securely hashed

## Development Notes

### Model Changes
- `Calculation` model now includes `user_id` foreign key
- Relationship established between `User` and `Calculation`

### Schema Updates
- `CalculationCreate`: For creating new calculations
- `CalculationUpdate`: For partial updates (PATCH)
- `CalculationRead`: Includes `user_id` in response

### API Improvements
- All calculation endpoints now filter by `current_user.id`
- Added PATCH endpoint for partial updates
- Enhanced error messages and status codes
- Proper HTTP status codes for all operations

## Usage Examples

### cURL Examples

**Create a calculation:**
```bash
curl -X POST "http://localhost:8000/calculations" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"a": 10, "b": 5, "type": "Add"}'
```

**Get all calculations:**
```bash
curl -X GET "http://localhost:8000/calculations" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Update a calculation:**
```bash
curl -X PUT "http://localhost:8000/calculations/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"a": 20, "b": 4, "type": "Divide"}'
```

**Delete a calculation:**
```bash
curl -X DELETE "http://localhost:8000/calculations/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting

### Issue: "Calculation not found"
- Verify the calculation ID exists
- Ensure you're logged in as the user who created it
- Check that your authentication token is valid

### Issue: "Invalid authentication credentials"
- Your token may have expired - log in again
- Ensure the Authorization header is properly formatted
- Check that the token is not corrupted

### Issue: "Division by zero is not allowed"
- Both server and client validate against division by zero
- Choose a non-zero value for the divisor

### Issue: Frontend not loading
- Ensure the backend is running on port 8000
- Ensure the frontend server is running on port 8081
- Check CORS configuration if accessing from a different origin

## Future Enhancements

Potential improvements for future versions:
- Batch operations (create/update/delete multiple calculations)
- Export calculations to CSV/JSON
- Calculation history and versioning
- Undo/redo functionality
- Calculation categories or tags
- Search and filter capabilities
- Calculation sharing between users
- API rate limiting
- Calculation caching for performance

## Support

For issues or questions:
1. Check the error message in the browser console
2. Review the server logs
3. Verify authentication tokens
4. Ensure all services are running
5. Check the database connection
