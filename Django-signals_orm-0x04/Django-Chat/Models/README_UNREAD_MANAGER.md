# Custom ORM Manager for Unread Messages

This document describes the implementation of a custom ORM manager for filtering unread messages in the Django Chat application.

## 📋 Requirements Fulfilled

✅ **Read Boolean Field**: Added `is_read` boolean field to the Message model  
✅ **Custom Manager**: Implemented `UnreadMessagesManager` for filtering unread messages  
✅ **Query Optimization**: Used `.only()` method to retrieve only necessary fields  
✅ **View Integration**: Created views that use the manager to display unread messages  

## 🏗️ Implementation Overview

### 1. Message Model Enhancement

The `Message` model already includes the required `is_read` field:

```python
class Message(models.Model):
    # ... other fields ...
    is_read = models.BooleanField(default=False)
    
    # Custom managers
    objects = ThreadedMessageManager()  # Default manager
    unread = UnreadMessagesManager()    # Custom manager for unread messages
    read = ReadMessagesManager()        # Manager for read messages
```

### 2. Custom Manager Implementation

The `UnreadMessagesManager` provides specialized methods for handling unread messages:

```python
class UnreadMessagesManager(models.Manager):
    """Custom manager for filtering and optimizing unread message queries."""
    
    def for_user(self, user):
        """Get all unread messages for a specific user."""
        return self.get_queryset().unread_for_user(user)
    
    def optimized_inbox(self, user, limit=50):
        """Get optimized unread messages for inbox display."""
        return self.get_queryset().inbox_optimized(user)[:limit]
```

### 3. Query Optimization with .only()

The manager uses Django's `.only()` method to fetch only necessary fields:

```python
def inbox_optimized(self, user):
    """Optimized query for inbox display with minimal fields."""
    return self.unread_for_user(user).only(
        'id', 'sender__username', 'content', 'timestamp',
        'thread_depth', 'parent_message__id'
    ).select_related(
        'sender', 'parent_message'
    ).order_by('-timestamp')
```

## 🎯 Available Manager Methods

### Core Methods
- `for_user(user)` - Get all unread messages for a user
- `optimized_inbox(user, limit=50)` - Optimized inbox display
- `recent_unread(user, hours=24)` - Recent unread messages
- `unread_by_sender(user, sender)` - Unread from specific sender
- `unread_count_by_sender(user)` - Count by sender
- `unread_threads(user)` - Organized by conversation threads

### Utility Methods
- `has_unread(user)` - Quick boolean check
- `unread_count(user)` - Total count
- `latest_unread(user, count=5)` - Latest N messages
- `get_unread_summary(user)` - Comprehensive statistics

### Bulk Operations
- `mark_as_read(user, message_ids)` - Mark specific messages as read
- `batch_mark_read_by_sender(user, sender)` - Mark all from sender as read
- `auto_mark_old_as_read(user, days=30)` - Auto-mark old messages

## 🌐 View Integration

### Views Created

1. **Unread Messages Inbox** (`/inbox/`)
   ```python
   def unread_messages_inbox(request):
       unread_messages = Message.unread.optimized_inbox(request.user, limit=50)
       # ... display logic
   ```

2. **Unread by Thread** (`/inbox/threads/`)
   ```python
   def unread_messages_by_thread(request):
       unread_threads = Message.unread.unread_threads(request.user)
       # ... thread organization logic
   ```

3. **Recent Unread** (`/inbox/recent/`)
   ```python
   def recent_unread_messages(request):
       recent_unread = Message.unread.recent_unread(request.user, hours=24)
       # ... display logic
   ```

### API Endpoints

- `POST /api/mark-read/` - Mark specific messages as read
- `POST /api/mark-sender-read/` - Mark all from sender as read

## 🚀 Usage Examples

### Basic Usage
```python
# Get all unread messages for a user
unread_messages = Message.unread.for_user(user)

# Get optimized inbox view
inbox_messages = Message.unread.optimized_inbox(user, limit=20)

# Check if user has unread messages (fast)
has_unread = Message.unread.has_unread(user)
```

### Advanced Filtering
```python
# Recent unread messages
recent = Message.unread.recent_unread(user, hours=24)

# Unread from specific sender
from_sender = Message.unread.unread_by_sender(user, sender)

# Unread count by sender
sender_counts = Message.unread.unread_count_by_sender(user)
```

### Bulk Operations
```python
# Mark specific messages as read
Message.unread.mark_as_read(user, [msg_id1, msg_id2])

# Mark all from sender as read
Message.unread.batch_mark_read_by_sender(user, sender)
```

## ⚡ Performance Optimizations

### Field Optimization
- Uses `.only()` to fetch minimal fields
- Selective use of `.select_related()` for foreign keys
- Indexes on key filtering fields

### Query Efficiency
- Bulk operations for marking as read
- Aggregation queries for statistics
- Optimized exists() checks

### Example Optimized Query
```python
# Instead of fetching all fields:
Message.objects.filter(receiver=user, is_read=False)

# Fetch only necessary fields:
Message.unread.optimized_inbox(user).only(
    'id', 'sender__username', 'content', 'timestamp'
)
```

## 🧪 Testing and Demo

### Run Demo Script
```bash
python manage.py shell < Models/demo_unread_manager.py
```

### Demo Features
- Creates sample data
- Demonstrates all manager methods
- Shows query optimization benefits
- Displays SQL queries generated

## 📊 Performance Benefits

1. **Reduced Memory Usage**: Only loads necessary fields
2. **Faster Queries**: Optimized field selection and indexing
3. **Bulk Operations**: Efficient batch updates
4. **Smart Caching**: Related object optimization

## 🔗 URL Configuration

```python
urlpatterns = [
    # Unread messages functionality
    path('inbox/', views.unread_messages_inbox, name='unread_messages_inbox'),
    path('inbox/threads/', views.unread_messages_by_thread, name='unread_messages_by_thread'),
    path('inbox/recent/', views.recent_unread_messages, name='recent_unread_messages'),
    
    # API endpoints
    path('api/mark-read/', views.mark_messages_as_read, name='mark_messages_as_read'),
    path('api/mark-sender-read/', views.mark_all_from_sender_as_read, name='mark_all_from_sender_as_read'),
]
```

## 📈 Statistics and Analytics

The manager provides comprehensive statistics:

```python
summary = Message.unread.get_unread_summary(user)
# Returns:
# {
#     'total_unread': 15,
#     'unique_senders': 3,
#     'unread_threads': 5,
#     'oldest_unread': datetime,
#     'newest_unread': datetime
# }
```

## 🎉 Conclusion

This implementation provides:
- ✅ Complete fulfillment of all requirements
- ⚡ High-performance query optimization
- 🔧 Flexible and extensible design
- 📱 Ready-to-use view integration
- 🧪 Comprehensive testing and demonstration

The custom `UnreadMessagesManager` offers a powerful, optimized solution for handling unread messages in Django applications with excellent performance characteristics and clean API design.

