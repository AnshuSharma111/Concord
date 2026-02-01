# User Management API

This API provides user management functionality for our application.

## API Endpoints

### Get User
The `GET /users/{id}` endpoint retrieves a user by ID. 
- Returns HTTP 200 with user data when user exists
- Returns HTTP 404 when user not found
- Requires authentication

### Create User
The `POST /users` endpoint creates a new user.
- Returns HTTP 201 when user is created successfully
- Returns HTTP 400 for invalid input data
- Returns HTTP 409 if user already exists

### Update User
Use `PUT /users/{id}` to update user information.
- Returns HTTP 200 on successful update
- Returns HTTP 404 if user doesn't exist
- Returns HTTP 403 if user lacks permission

## Error Handling

All endpoints return HTTP 401 for unauthenticated requests.
Invalid JSON in request body results in HTTP 400 status code.

## Usage Examples

```bash
curl -X GET "https://api.example.com/users/123"
```

The above request will return user data or 404 if not found.