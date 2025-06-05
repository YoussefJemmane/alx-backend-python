# Django Middleware Implementation

This project demonstrates the implementation of custom middleware in a Django messaging application. Middleware serves as a bridge between the request and response phases of the application cycle, allowing for cross-cutting concerns to be handled in a clean and modular way.

## Middleware Components

### 1. Request Logging Middleware

The `RequestLoggingMiddleware` logs each user's requests to a file, including timestamp, user, and request path.

- Location: `chats/middleware.py`
- Log file: `requests.log`

### 2. Time-based Access Restriction

The `RestrictAccessByTimeMiddleware` restricts access to the messaging app during certain hours (between 9PM and 6AM).

- Location: `chats/middleware.py`
- Returns 403 Forbidden if accessed outside allowed hours

### 3. Rate Limiting for Messages

The `OffensiveLanguageMiddleware` limits the number of chat messages a user can send within a time window (5 messages per minute), based on their IP address.

- Location: `chats/middleware.py`
- Applies to: POST requests to the `/api/messages/` endpoint

### 4. Role-based Permission Middleware

The `RolePermissionMiddleware` checks the user's role (admin, moderator) before allowing access to admin-only actions.

- Location: `chats/middleware.py`
- Protected endpoints: `/api/admin/`, `/api/users/manage/`, etc.

## Configuration

The middleware is configured in `messaging_app/settings.py` in the `MIDDLEWARE` setting. The order of middleware is important - they are executed top-to-bottom for requests and bottom-to-top for responses.

## Testing

To test the middleware:

1. Run the Django development server: `python manage.py runserver`
2. Use Postman or the browser to access various endpoints
3. Check the `requests.log` file to see logged requests
4. Try accessing the app after 9PM to see the time restriction in action
5. Send multiple messages quickly to test the rate limiting
6. Access admin endpoints without admin privileges to test role permissions

## Middleware Lifecycle

Each middleware follows this pattern:

1. `__init__(self, get_response)`: Store the next middleware or view in the chain
2. `__call__(self, request)`: Process the request, optionally short-circuit by returning a response
3. If not short-circuited, call the next middleware/view using `self.get_response(request)`
4. Process the response (if needed) before returning it

# Messaging App API

## Overview

This Django REST Framework-based API provides a secure messaging platform with authentication, permissions, and filtering capabilities. Users can create conversations, send messages, and manage their communications in a secure and efficient manner.

## Features

- **JWT Authentication**: Secure token-based authentication using JSON Web Tokens
- **Custom Permissions**: Only participants in a conversation can access, send, and manage messages
- **Pagination**: 20 messages per page with customizable page size
- **Filtering**: Filter messages by time range, sender, or content
- **Object-level Permissions**: Fine-grained access control for conversations and messages

## Installation

1. Clone the repository
2. Install requirements:
   ```
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```
   python manage.py migrate
   ```
4. Create a superuser:
   ```
   python manage.py createsuperuser
   ```
5. Run the server:
   ```
   python manage.py runserver
   ```

## API Usage

Detailed API documentation is available in the `API_DOCUMENTATION.md` file.

### Authentication

Obtain a JWT token by sending your credentials to `/api/token/`:

```json
{
    "username": "your_username",
    "password": "your_password"
}
```

Include the token in your Authorization header for all protected endpoints:

```
Authorization: Bearer <your_token>
```

### Key Endpoints

- `/api/conversations/` - List and create conversations
- `/api/conversations/{id}/` - Retrieve, update, or delete a conversation
- `/api/conversations/{id}/messages/` - List messages in a conversation
- `/api/messages/` - Create messages
- `/api/messages/unread/` - List unread messages

## Testing

A Postman collection is included in the `post_man-Collections` directory for testing all API endpoints.

## Implementation Details

### Authentication

The app uses djangorestframework-simplejwt for JWT authentication. Tokens are issued with a 1-hour lifetime for access tokens and 1-day lifetime for refresh tokens.

### Permissions

Custom permission class `IsParticipantOfConversation` ensures that only participants in a conversation can view and interact with it and its messages.

### Pagination and Filtering

The API includes pagination with 20 items per page and extensive filtering options using django-filter.

