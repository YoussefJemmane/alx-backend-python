#!/usr/bin/env python
"""
Demonstration script for the message edit tracking system.

This script shows how Django signals automatically track message edits
and save old content to MessageHistory.

Usage:
    python manage.py shell
    exec(open('Django-Chat/Models/demo.py').read())
"""

from django.contrib.auth.models import User
from django.utils import timezone
from .models import Message, MessageHistory, Notification
from .signals import can_edit_message, edit_message


def demo_message_edit_tracking():
    """Demonstrate the message edit tracking system."""
    
    print("=== Django Signals for Message Edit Tracking Demo ===")
    print()
    
    # Create test users
    print("1. Creating test users...")
    user1, created = User.objects.get_or_create(
        username='alice',
        defaults={'email': 'alice@example.com'}
    )
    if created:
        user1.set_password('password123')
        user1.save()
        print(f"   Created user: {user1.username}")
    else:
        print(f"   User already exists: {user1.username}")
    
    user2, created = User.objects.get_or_create(
        username='bob',
        defaults={'email': 'bob@example.com'}
    )
    if created:
        user2.set_password('password123')
        user2.save()
        print(f"   Created user: {user2.username}")
    else:
        print(f"   User already exists: {user2.username}")
    
    print()
    
    # Create initial message
    print("2. Creating initial message...")
    message = Message.objects.create(
        sender=user1,
        receiver=user2,
        content="Hey Bob! How are you doing?"
    )
    print(f"   ✓ Message created: {message}")
    print(f"   ✓ Initial content: '{message.content}'")
    print(f"   ✓ Edited status: {message.edited}")
    print(f"   ✓ Edit count: {message.edit_count}")
    print()
    
    # Clear notifications from initial message creation
    print("3. Clearing initial notifications...")
    initial_notifications = Notification.objects.filter(
        notification_type='new_message'
    ).count()
    print(f"   ✓ Initial notifications created: {initial_notifications}")
    print()
    
    # First edit
    print("4. Performing first edit...")
    print(f"   Original content: '{message.content}'")
    
    message.content = "Hey Bob! How are you doing today?"
    message.save()
    message.refresh_from_db()
    
    print(f"   ✓ New content: '{message.content}'")
    print(f"   ✓ Edited status: {message.edited}")
    print(f"   ✓ Edit count: {message.edit_count}")
    print(f"   ✓ Last edited at: {message.last_edited_at}")
    
    # Check history
    print("\n   Edit History:")
    for i, history in enumerate(message.get_edit_history(), 1):
        print(f"     Edit #{i}: '{history.old_content}' (edited at {history.edited_at})")
    
    print()
    
    # Second edit
    print("5. Performing second edit...")
    print(f"   Current content: '{message.content}'")
    
    message.content = "Hey Bob! How are you doing today? Hope you're having a great day!"
    message.save()
    message.refresh_from_db()
    
    print(f"   ✓ New content: '{message.content}'")
    print(f"   ✓ Edit count: {message.edit_count}")
    
    # Check complete history
    print("\n   Complete Edit History:")
    for i, history in enumerate(message.get_edit_history(), 1):
        print(f"     Edit #{i}: '{history.old_content}' (edited by {history.edited_by.username} at {history.edited_at})")
    
    print()
    
    # Test edit permissions
    print("6. Testing edit permissions...")
    can_edit = can_edit_message(message, user1)
    print(f"   ✓ Can Alice edit her message? {can_edit}")
    
    can_edit = can_edit_message(message, user2)
    print(f"   ✓ Can Bob edit Alice's message? {can_edit}")
    
    print()
    
    # Test utility function
    print("7. Testing edit utility function...")
    success, error = edit_message(
        message, 
        "Hey Bob! How are you doing today? Hope you're having a fantastic day!",
        user1,
        "Adding more enthusiasm"
    )
    
    if success:
        message.refresh_from_db()
        print(f"   ✓ Edit successful: '{message.content}'")
        print(f"   ✓ Edit count: {message.edit_count}")
    else:
        print(f"   ✗ Edit failed: {error}")
    
    print()
    
    # Test failed edit (same content)
    print("8. Testing failed edit (same content)...")
    success, error = edit_message(
        message, 
        message.content,  # Same content
        user1
    )
    
    if success:
        print("   ✓ Edit successful")
    else:
        print(f"   ✗ Edit failed as expected: {error}")
    
    print()
    
    # Test unauthorized edit
    print("9. Testing unauthorized edit...")
    success, error = edit_message(
        message, 
        "Bob trying to edit Alice's message",
        user2  # Bob trying to edit Alice's message
    )
    
    if success:
        print("   ✗ Edit should have failed!")
    else:
        print(f"   ✓ Edit failed as expected: {error}")
    
    print()
    
    # Show final statistics
    print("10. Final statistics:")
    print(f"    Total messages: {Message.objects.count()}")
    print(f"    Total message histories: {MessageHistory.objects.count()}")
    print(f"    Total notifications: {Notification.objects.count()}")
    
    # Show notification breakdown
    new_msg_notifications = Notification.objects.filter(
        notification_type='new_message'
    ).count()
    edit_notifications = Notification.objects.filter(
        notification_type='message_edited'
    ).count()
    
    print(f"    New message notifications: {new_msg_notifications}")
    print(f"    Edit notifications: {edit_notifications}")
    
    print()
    
    # Show all notifications
    print("11. All notifications:")
    for notification in Notification.objects.all().order_by('-created_at'):
        print(f"    - {notification.notification_type}: {notification.notification_text}")
    
    print()
    
    # Show message timeline
    print("12. Message timeline:")
    print(f"    Original message: 'Hey Bob! How are you doing?'")
    for i, history in enumerate(reversed(list(message.get_edit_history())), 1):
        print(f"    Edit #{i}: '{history.old_content}' → (next version)")
    print(f"    Current version: '{message.content}'")
    
    print()
    print("=== Demo Complete ===")
    print("The Django pre_save signal automatically captured old content")
    print("whenever a Message instance was modified, creating a complete edit history!")


def demo_admin_interface_features():
    """Demonstrate features available in the Django admin interface."""
    
    print("\n=== Django Admin Interface Features ===")
    print()
    
    print("1. Message Admin Features:")
    print("   - View message edit status with visual indicators")
    print("   - See edit count for each message")
    print("   - Direct link to view edit history")
    print("   - Inline edit history display")
    print("   - Filter by edited status")
    print()
    
    print("2. MessageHistory Admin Features:")
    print("   - View all edit history records")
    print("   - Link back to original message")
    print("   - Preview of old content")
    print("   - Filter by editor and date")
    print("   - Read-only to preserve audit trail")
    print()
    
    print("3. Enhanced Notifications:")
    print("   - Different notification types (new_message, message_edited)")
    print("   - Filter by notification type")
    print("   - Bulk actions to mark as read")
    print()
    
    print("To explore these features:")
    print("1. Add 'django_chat' to INSTALLED_APPS")
    print("2. Run: python manage.py makemigrations django_chat")
    print("3. Run: python manage.py migrate")
    print("4. Create superuser: python manage.py createsuperuser")
    print("5. Access admin at: http://localhost:8000/admin/")


if __name__ == '__main__':
    # This will run when executed directly
    demo_message_edit_tracking()
    demo_admin_interface_features()

