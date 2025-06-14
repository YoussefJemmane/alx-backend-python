#!/usr/bin/env python
"""
Demonstration script for message edit tracking functionality.

This script shows how the Django pre_save signal automatically logs
old content when messages are edited.

Usage:
    python manage.py shell
    exec(open('messaging/demo_edit.py').read())
"""

from django.contrib.auth.models import User
from .models import Message, MessageHistory, Notification


def demo_message_edit_tracking():
    """Demonstrate the message edit tracking system."""
    
    print("=== Message Edit Tracking Demo ===")
    print()
    
    # Create test users
    print("1. Creating test users...")
    user1, created = User.objects.get_or_create(
        username='alice_edit',
        defaults={'email': 'alice@example.com'}
    )
    if created:
        user1.set_password('password123')
        user1.save()
        print(f"   Created user: {user1.username}")
    else:
        print(f"   User already exists: {user1.username}")
    
    user2, created = User.objects.get_or_create(
        username='bob_edit',
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
        content="Hello Bob! How are you?"
    )
    print(f"   ✓ Message created: {message}")
    print(f"   ✓ Initial content: '{message.content}'")
    print(f"   ✓ Edited: {message.edited}")
    print(f"   ✓ Edit count: {message.edit_count}")
    print(f"   ✓ Has edit history: {message.has_edit_history()}")
    print()
    
    # First edit - this should trigger the pre_save signal
    print("3. Editing the message (first edit)...")
    print(f"   Original content: '{message.content}'")
    
    # This edit will trigger the pre_save signal
    message.content = "Hello Bob! How are you doing today?"
    message.save()
    
    # Refresh from database to see updated fields
    message.refresh_from_db()
    
    print(f"   ✓ New content: '{message.content}'")
    print(f"   ✓ Edited: {message.edited}")
    print(f"   ✓ Edit count: {message.edit_count}")
    print(f"   ✓ Last edited at: {message.last_edited_at}")
    print(f"   ✓ Has edit history: {message.has_edit_history()}")
    
    # Check if history was created
    print("\n   Edit History:")
    history_count = message.get_edit_history().count()
    print(f"   ✓ Number of history records: {history_count}")
    
    for i, history in enumerate(message.get_edit_history(), 1):
        print(f"     Edit #{i}:")
        print(f"       Old content: '{history.old_content}'")
        print(f"       Edited by: {history.edited_by.username}")
        print(f"       Edited at: {history.edited_at}")
    
    print()
    
    # Second edit
    print("4. Making another edit (second edit)...")
    print(f"   Current content: '{message.content}'")
    
    message.content = "Hello Bob! How are you doing today? Hope you're well!"
    message.save()
    message.refresh_from_db()
    
    print(f"   ✓ New content: '{message.content}'")
    print(f"   ✓ Edit count: {message.edit_count}")
    
    # Show complete edit history
    print("\n   Complete Edit History:")
    history_count = message.get_edit_history().count()
    print(f"   ✓ Total history records: {history_count}")
    
    for i, history in enumerate(message.get_edit_history(), 1):
        print(f"     Edit #{i}:")
        print(f"       Old content: '{history.old_content}'")
        print(f"       Edited by: {history.edited_by.username}")
        print(f"       Edited at: {history.edited_at}")
        if history.edit_reason:
            print(f"       Reason: {history.edit_reason}")
    
    print()
    
    # Show final statistics
    print("5. Final statistics:")
    print(f"   Total messages: {Message.objects.count()}")
    print(f"   Total message histories: {MessageHistory.objects.count()}")
    print(f"   Total notifications: {Notification.objects.count()}")
    
    print()
    
    # Test the admin interface features
    print("6. Admin interface features available:")
    print("   - View edit status with visual indicators")
    print("   - See edit count for each message")
    print("   - Direct link to view complete edit history")
    print("   - Inline edit history display within message admin")
    print("   - Filter messages by edit status")
    print("   - Read-only edit history to preserve audit trail")
    
    print()
    print("=== Demo Complete ===")
    print("The Django pre_save signal automatically captured old content")
    print("before each message edit, creating a complete audit trail!")
    print()
    print("To view in Django Admin:")
    print("1. Add 'messaging' to INSTALLED_APPS")
    print("2. Run: python manage.py makemigrations messaging")
    print("3. Run: python manage.py migrate")
    print("4. Access admin to see edit history and tracking")


if __name__ == '__main__':
    demo_message_edit_tracking()

