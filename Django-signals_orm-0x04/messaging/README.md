# Django Signals for User Notifications

This implementation demonstrates how to use Django signals to automatically notify users when they receive new messages.

## Overview

The messaging system consists of two main models:
- **Message**: Represents messages sent between users
- **Notification**: Represents notifications sent to users about new messages

When a new message is created, a Django `post_save` signal automatically creates a corresponding notification for the receiving user.

## Features

### Models

#### Message Model
- `sender`: ForeignKey to User (who sent the message)
- `receiver`: ForeignKey to User (who receives the message)
- `content`: TextField for the message content
- `timestamp`: DateTimeField for when the message was created
- `is_read`: BooleanField to track if the message has been read

#### Notification Model
- `user`: ForeignKey to User (who receives the notification)
- `message`: ForeignKey to Message (the related message)
- `notification_text`: CharField for the notification message
- `is_read`: BooleanField to track if the notification has been read
- `created_at`: DateTimeField for when the notification was created

### Django Signals

The system uses Django's `post_save` signal to automatically create notifications:

```python
@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if created:
        # Create notification for the receiver
        notification_text = f"You have a new message from {instance.sender.username}"
        
        Notification.objects.create(
            user=instance.receiver,
            message=instance,
            notification_text=notification_text
        )
```

## File Structure

```
messaging/
├── __init__.py          # Package initialization with app config
├── models.py            # Message and Notification models
├── signals.py           # Signal handlers for automatic notifications
├── apps.py              # App configuration to register signals
├── admin.py             # Django admin configuration
├── tests.py             # Comprehensive test suite
├── demo.py              # Demonstration script
└── README.md            # This documentation
```

## Usage

### 1. Add to Django Settings

Add 'messaging' to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... other apps
    'messaging',
]
```

### 2. Run Migrations

```bash
python manage.py makemigrations messaging
python manage.py migrate
```

### 3. Create Messages

```python
from django.contrib.auth.models import User
from messaging.models import Message

# Create users
sender = User.objects.create_user('alice', 'alice@example.com', 'password')
receiver = User.objects.create_user('bob', 'bob@example.com', 'password')

# Create a message (notification will be created automatically)
message = Message.objects.create(
    sender=sender,
    receiver=receiver,
    content="Hello! This is a test message."
)

# Check notifications
print(f"Bob has {receiver.notifications.count()} notifications")
```

### 4. Run the Demo

```bash
python manage.py shell
exec(open('messaging/demo.py').read())
```

## Testing

Run the comprehensive test suite:

```bash
python manage.py test messaging
```

The test suite includes:
- Model creation and validation tests
- Signal functionality tests
- Integration tests for complete message flows
- Edge case testing

## Admin Interface

The models are registered in Django admin with custom configurations:
- Message admin shows sender, receiver, content preview, timestamp, and read status
- Notification admin shows user, notification text, message sender, creation time, and read status

## Key Implementation Details

### Signal Registration

Signals are registered in `apps.py` using the `ready()` method to ensure they're loaded when the app starts:

```python
class MessagingConfig(AppConfig):
    name = 'messaging'
    
    def ready(self):
        import messaging.signals
```

### Automatic Notification Creation

The signal handler only creates notifications for **new** messages (when `created=True`), preventing duplicate notifications when existing messages are updated.

### Related Names

The models use descriptive `related_name` attributes for reverse relationships:
- `User.sent_messages` - messages sent by the user
- `User.received_messages` - messages received by the user
- `User.notifications` - notifications for the user
- `Message.notifications` - notifications related to the message

## Extensibility

This implementation can be extended with:
- Email notifications
- Push notifications
- Real-time WebSocket notifications
- Notification preferences
- Message threading
- File attachments
- Message encryption

## Error Handling

The signal handlers include basic error handling and logging. In production, you might want to add:
- Try-catch blocks for database errors
- Logging for debugging
- Async task queues for heavy operations
- Rate limiting for notification creation

## Performance Considerations

- Notifications are created synchronously when messages are saved
- For high-volume applications, consider using async tasks (Celery)
- Database indexes on frequently queried fields
- Pagination for notification lists
- Cleanup of old notifications

