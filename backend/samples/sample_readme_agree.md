# User API

## GET /users/{id}

Returns user information.

- Returns **200 OK** when the user exists
- Returns **404 Not Found** when the user does not exist

## PUT /users/{id}

Updates an existing user.

- Returns **200 OK** when update succeeds
- Returns **404 Not Found** when the user does not exist
- Returns **403 Forbidden** when the user is not authorized
