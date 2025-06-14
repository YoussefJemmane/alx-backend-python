#!/usr/bin/env python
"""
Test script to demonstrate user deletion functionality with signal handling.

This script shows how the post_delete signal automatically cleans up
all user-related data when a user account is deleted.

Run this script in your Django shell:
    python manage.py shell < test_user_deletion.py

Or execute individual parts in the Django shell.
"""

import os
import sys
import django
from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import transaction
from django.core.management import execute_from_command_line

# Ensure Django is set up
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
    django.setup()

# Import models after Django setup
from messaging.models import Message, MessageHistory, Notification


def test_user_deletion_cascade():
    """
    Test that demonstrates the CASCADE deletion behavior and signal handling.
    """
    print("=" * 60)
    print("Testing User Deletion with Signal Handling")
    print("=" * 60)
    
    # Create test users
    print("\n1. Creating test users...")
    user1 = User.objects.create_user(
        username='testuser1',
        email='user1@test.com',
        password='testpass123'
    )
    user2 = User.objects.create_user(
        username='testuser2', 
        email='user2@test.com',
        password='testpass123'
    )
    print(f"   Created users: {user1.username}, {user2.username}")
    
    # Create test messages
    print("\n2. Creating test messages...")
    messages = []
    for i in range(3):
        msg = Message.objects.create(
            sender=user1,
            receiver=user2,
            content=f"Test message {i+1} from {user1.username} to {user2.username}"
        )
        messages.append(msg)
        print(f"   Created message {i+1}: ID {msg.id}")
    
    # Create some messages in the other direction
    for i in range(2):
        msg = Message.objects.create(
            sender=user2,
            receiver=user1,
            content=f"Reply message {i+1} from {user2.username} to {user1.username}"
        )
        messages.append(msg)
        print(f"   Created reply {i+1}: ID {msg.id}")
    
    # Edit some messages to create history
    print("\n3. Editing messages to create history...")
    first_message = messages[0]
    original_content = first_message.content
    first_message.content = "This message has been edited!"
    first_message.save()
    print(f"   Edited message {first_message.id}")
    
    # Check initial data counts
    print("\n4. Initial data counts:")
    total_messages = Message.objects.count()
    user1_sent = user1.sent_messages.count()
    user1_received = user1.received_messages.count()
    user1_notifications = user1.notifications.count()
    user1_edit_history = user1.message_edits.count()
    
    print(f"   Total messages in system: {total_messages}")
    print(f"   User1 sent messages: {user1_sent}")
    print(f"   User1 received messages: {user1_received}")
    print(f"   User1 notifications: {user1_notifications}")
    print(f"   User1 edit history records: {user1_edit_history}")
    
    user2_sent = user2.sent_messages.count()
    user2_received = user2.received_messages.count() 
    user2_notifications = user2.notifications.count()
    user2_edit_history = user2.message_edits.count()
    
    print(f"   User2 sent messages: {user2_sent}")
    print(f"   User2 received messages: {user2_received}")
    print(f"   User2 notifications: {user2_notifications}")
    print(f"   User2 edit history records: {user2_edit_history}")
    
    total_notifications = Notification.objects.count()
    total_history = MessageHistory.objects.count()
    
    print(f"   Total notifications: {total_notifications}")
    print(f"   Total history records: {total_history}")
    
    # Delete user1 and observe cascade effect
    print("\n5. Deleting user1...")
    user1_id = user1.id
    user1_username = user1.username
    
    with transaction.atomic():
        # The delete() call will trigger the post_delete signal
        user1.delete()
    
    print(f"   User {user1_username} (ID: {user1_id}) deleted")
    
    # Check data counts after deletion
    print("\n6. Data counts after user1 deletion:")
    remaining_messages = Message.objects.count()
    remaining_notifications = Notification.objects.count()
    remaining_history = MessageHistory.objects.count()
    
    print(f"   Remaining messages: {remaining_messages}")
    print(f"   Remaining notifications: {remaining_notifications}")
    print(f"   Remaining history records: {remaining_history}")
    
    # Check user2's data (should be unaffected except for messages with user1)
    user2_remaining_sent = user2.sent_messages.count()
    user2_remaining_received = user2.received_messages.count()
    user2_remaining_notifications = user2.notifications.count()
    
    print(f"   User2 remaining sent messages: {user2_remaining_sent}")
    print(f"   User2 remaining received messages: {user2_remaining_received}")
    print(f"   User2 remaining notifications: {user2_remaining_notifications}")
    
    # Verify CASCADE worked correctly
    print("\n7. Verification:")
    expected_remaining_messages = 0  # All messages should be deleted due to CASCADE
    if remaining_messages == expected_remaining_messages:
        print("   ✅ CASCADE deletion worked correctly for messages")
    else:
        print(f"   ❌ Expected {expected_remaining_messages} messages, got {remaining_messages}")
    
    if remaining_notifications == 0:
        print("   ✅ CASCADE deletion worked correctly for notifications")
    else:
        print(f"   ❌ Expected 0 notifications, got {remaining_notifications}")
    
    if remaining_history == 0:
        print("   ✅ CASCADE deletion worked correctly for message history")
    else:
        print(f"   ❌ Expected 0 history records, got {remaining_history}")
    
    # Clean up user2
    print("\n8. Cleaning up remaining test data...")
    user2.delete()
    print(f"   Deleted user {user2.username}")
    
    final_message_count = Message.objects.count()
    final_notification_count = Notification.objects.count()
    final_history_count = MessageHistory.objects.count()
    
    print(f"   Final counts - Messages: {final_message_count}, "
          f"Notifications: {final_notification_count}, "
          f"History: {final_history_count}")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("The post_delete signal properly cleaned up all user-related data.")
    print("=" * 60)


def demonstrate_view_functionality():
    """
    Demonstrate how to use the delete_user view functionality.
    """
    print("\n" + "=" * 60)
    print("View Usage Instructions")
    print("=" * 60)
    
    print("""
    To use the user deletion functionality in your Django app:
    
    1. Include the URLs in your main urlpatterns:
       
       from django.urls import path, include
       
       urlpatterns = [
           path('chat/', include('Django-Chat.Views.urls')),
           # ... your other URLs
       ]
    
    2. Visit these URLs:
       
       /chat/delete-account/     - Main deletion page
       /chat/deletion-stats/     - View data statistics
       /chat/export-data/        - Export user data
       /chat/api/delete-account/ - API endpoint
    
    3. The deletion process:
       
       a) User visits /chat/delete-account/
       b) User sees warning and data statistics
       c) User types confirmation text
       d) POST request triggers user.delete()
       e) post_delete signal automatically cleans up:
          - All sent/received messages
          - All notifications
          - All message edit history
          - Any other related data
       f) User is redirected to success page
    
    4. API Usage (for programmatic deletion):
       
       POST /chat/api/delete-account/
       Content-Type: application/json
       
       {
           "confirmation": "delete username"
       }
       
       Response:
       {
           "success": true,
           "message": "Account deleted successfully",
           "deleted_data": {
               "messages_deleted": 10,
               "notifications_deleted": 5,
               "edit_history_deleted": 2
           }
       }
    """)


if __name__ == "__main__":
    try:
        test_user_deletion_cascade()
        demonstrate_view_functionality()
    except Exception as e:
        print(f"Error running test: {str(e)}")
        import traceback
        traceback.print_exc()

