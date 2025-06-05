# Messaging App API Documentation

## Authentication

The API uses JWT (JSON Web Token) authentication. To access protected endpoints, you need to include the JWT token in the Authorization header of your requests.

### Obtaining a JWT Token

```
POST /api/token/
```

**Request Body:**
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Refreshing a JWT Token

```
POST /api/token/refresh/
```

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Conversations

### Get All Conversations

```
GET /api/conversations/
```

**Response:**
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Test Conversation",
            "display_title": "Test Conversation",
            "participants": [...],
            "messages": [...],
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "conversation_summary": "Latest: Hello, this is a test message!",
            "unread_count": 0
        }
    ]
}
```

### Create a Conversation

```
POST /api/conversations/
```

**Request Body:**
```json
{
    "title": "New Conversation",
    "participant_ids": ["550e8400-e29b-41d4-a716-446655440001"]
}
```

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "title": "New Conversation",
    "display_title": "New Conversation",
    "participants": [...],
    "messages": [],
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z",
    "conversation_summary": "No messages yet",
    "unread_count": 0
}
```

## Messages

### Get Messages for a Conversation

```
GET /api/conversations/{conversation_id}/messages/
```

**Response:**
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440003",
            "sender": "550e8400-e29b-41d4-a716-446655440000",
            "sender_username": "testuser",
            "conversation": "550e8400-e29b-41d4-a716-446655440002",
            "message_body": "Hello, this is a test message!",
            "sent_at": "2023-01-01T00:00:00Z",
            "is_read": false,
            "message_preview": "Hello, this is a test message!",
            "time_since_sent": "Just now"
        }
    ]
}
```

### Send a Message

```
POST /api/messages/
```

**Request Body:**
```json
{
    "conversation": "550e8400-e29b-41d4-a716-446655440002",
    "message_body": "Hello, this is a test message!"
}
```

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "sender": "550e8400-e29b-41d4-a716-446655440000",
    "sender_username": "testuser",
    "conversation": "550e8400-e29b-41d4-a716-446655440002",
    "message_body": "Hello, this is a test message!",
    "sent_at": "2023-01-01T00:00:00Z",
    "is_read": false,
    "message_preview": "Hello, this is a test message!",
    "time_since_sent": "Just now"
}
```

## Filtering and Pagination

### Filter Messages by Time Range

```
GET /api/messages/?conversation={conversation_id}&sent_after=2023-01-01T00:00:00Z&sent_before=2023-12-31T23:59:59Z
```

### Filter Conversations by Participant

```
GET /api/conversations/?participant={user_id}
```

### Pagination

All list endpoints support pagination with 20 items per page by default.

```
GET /api/messages/?page=2
```

You can also change the page size (up to a maximum of 100 items per page):

```
GET /api/messages/?page=2&page_size=50
```

