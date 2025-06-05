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

