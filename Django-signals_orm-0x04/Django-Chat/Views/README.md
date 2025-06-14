# Django User Deletion with Signal-Based Cleanup

This implementation provides a comprehensive user account deletion system with automatic cleanup of related data using Django signals.

## Features

### 1. User Deletion View (`delete_user`)
- **Confirmation Interface**: Users must type their username to confirm deletion
- **Data Statistics**: Shows how much data will be deleted
- **Export Option**: Users can export their data before deletion
- **Transaction Safety**: Uses database transactions for data consistency
- **Security**: Users can only delete their own accounts

### 2. Post-Delete Signal Implementation
- **Automatic Cleanup**: Removes all user-related data automatically
- **CASCADE Relationships**: Leverages Django's CASCADE for efficient deletion
- **Comprehensive Logging**: Logs all deletion activities for audit trails
- **Error Handling**: Graceful error handling without disrupting deletion

### 3. Data Types Automatically Cleaned Up
When a user is deleted, the following data is automatically removed:
- ✅ **Messages** (sent and received) - CASCADE
- ✅ **Notifications** - CASCADE  
- ✅ **Message Edit History** - CASCADE
- ✅ **Edited Message References** - SET_NULL
- ✅ **User Profile Data** - Inherent deletion

## File Structure

```
Django-Chat/Views/
├── __init__.py                 # Package initialization
├── views.py                   # Main view functions
├── urls.py                    # URL patterns
├── test_user_deletion.py      # Test/demo script
├── README.md                  # This documentation
└── templates/chat/
    ├── delete_user_confirm.html   # Deletion confirmation page
    └── account_deleted.html       # Success page
```

## Installation & Setup

### 1. Include URLs in your main project

```python
# urls.py (main project)
from django.urls import path, include

urlpatterns = [
    path('chat/', include('Django-Chat.Views.urls')),
    # ... your other URLs
]
```

### 2. Ensure signals are loaded

Make sure the signals in `messaging/signals.py` are loaded by importing them in your app's `apps.py`:

```python
# messaging/apps.py
from django.apps import AppConfig

class MessagingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messaging'
    
    def ready(self):
        import messaging.signals  # Import signals when app is ready
```

### 3. Update INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'messaging',
    # ... other apps
]
```

## Usage

### Web Interface

1. **View Deletion Stats**: `/chat/deletion-stats/`
2. **Export User Data**: `/chat/export-data/`
3. **Delete Account**: `/chat/delete-account/`
4. **Success Page**: `/chat/account-deleted/`

### API Usage

```javascript
// Delete user account via API
fetch('/chat/api/delete-account/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify({
        confirmation: 'delete username'
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('Account deleted:', data.message);
        console.log('Data removed:', data.deleted_data);
    }
});
```

## Signal Implementation Details

### Foreign Key Relationships

The models are designed with appropriate CASCADE relationships:

```python
# Message model
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)      # ✅ CASCADE
    receiver = models.ForeignKey(User, on_delete=models.CASCADE)    # ✅ CASCADE
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL)  # ✅ SET_NULL

# MessageHistory model  
class MessageHistory(models.Model):
    edited_by = models.ForeignKey(User, on_delete=models.CASCADE)   # ✅ CASCADE
    message = models.ForeignKey(Message, on_delete=models.CASCADE)  # ✅ CASCADE

# Notification model
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)        # ✅ CASCADE
    message = models.ForeignKey(Message, on_delete=models.CASCADE)  # ✅ CASCADE
```

### Signal Handlers

1. **`cleanup_user_related_data`**: Main post_delete handler for User model
2. **`cleanup_message_related_data`**: Handler for Message deletion
3. **`log_message_history_deletion`**: Logs MessageHistory deletions
4. **`log_notification_deletion`**: Logs Notification deletions

## Testing

Run the test script to verify functionality:

```bash
# In Django shell
python manage.py shell < Django-Chat/Views/test_user_deletion.py

# Or manually in shell
python manage.py shell
>>> exec(open('Django-Chat/Views/test_user_deletion.py').read())
```

## Security Features

1. **Confirmation Required**: Users must type exact confirmation text
2. **Authentication Required**: Only logged-in users can delete accounts
3. **Self-Deletion Only**: Users can only delete their own accounts
4. **Transaction Safety**: Uses atomic transactions
5. **CSRF Protection**: All forms include CSRF tokens
6. **Logging**: Comprehensive audit trail

## Error Handling

- **Database Errors**: Wrapped in try-catch with rollback
- **Signal Errors**: Don't interrupt deletion process
- **User Errors**: Clear error messages and redirects
- **API Errors**: Proper HTTP status codes and JSON responses

## Compliance Features

- **GDPR Compliance**: Complete data removal
- **Data Export**: Users can download their data
- **Audit Trail**: Comprehensive logging
- **Right to be Forgotten**: Complete account erasure

## Performance Considerations

- **Bulk Operations**: CASCADE handles bulk deletions efficiently
- **Transaction Atomicity**: Ensures data consistency
- **Optimized Queries**: Uses select_related and prefetch_related
- **Minimal Signal Overhead**: Signals only log, don't duplicate CASCADE work

## Monitoring & Debugging

Check logs for deletion events:

```python
import logging
logger = logging.getLogger('messaging.signals')

# Look for these log entries:
# - "Post-delete signal triggered for user: ..."
# - "User deletion cleanup completed successfully for: ..."
# - "Message deleted: ID ... from ... to ..."
```

## Customization

To add custom cleanup logic, modify the signal handlers:

```python
@receiver(post_delete, sender=User)
def cleanup_user_related_data(sender, instance, **kwargs):
    # ... existing code ...
    
    # Add your custom cleanup here:
    # - Delete uploaded files
    # - Remove external service accounts
    # - Clean up cached data
    # - Notify external systems
```

## Troubleshooting

### Common Issues

1. **Signals not firing**: Ensure `apps.py` imports signals in `ready()` method
2. **CASCADE not working**: Check foreign key `on_delete` parameters
3. **Permission errors**: Verify user authentication and ownership
4. **Transaction errors**: Check database constraints and relationships

### Debug Mode

Enable debug logging:

```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'messaging.signals': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## License

This implementation is part of the ALX Backend Python curriculum.

