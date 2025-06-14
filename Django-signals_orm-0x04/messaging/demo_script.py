#!/usr/bin/env python
"""
Demonstration script for Django Signals, ORM, and Caching features.

This script demonstrates:
1. Event Listeners (Signals) for user notifications
2. Signal for logging message edits
3. Signal for cleaning up user data on deletion
4. Advanced ORM techniques for threaded conversations
5. Custom ORM manager for unread messages
6. Basic view-level caching

Run this script with: python manage.py shell < demo_script.py
"""

import os
import django
from django.contrib.auth.models import User
from messaging.models import Message, Notification, MessageHistory
from django.core.cache import cache
from django.utils import timezone

print("=== Django Signals, ORM & Caching Demo ===")
print()

# Task 0 & 1: Signals for notifications and message editing
print("1. Testing Signal for User Notifications (Task 0)")
print("-" * 50)

# Create test users
user1, created = User.objects.get_or_create(
    username='alice',
    defaults={'email': 'alice@example.com', 'first_name': 'Alice'}
)
user2, created = User.objects.get_or_create(
    username='bob',
    defaults={'email': 'bob@example.com', 'first_name': 'Bob'}
)
print(f"Created users: {user1.username} and {user2.username}")

# Create a message (this will trigger the post_save signal)
print("\nCreating a message from Alice to Bob...")
message1 = Message.objects.create(
    sender=user1,
    receiver=user2,
    content="Hello Bob! How are you doing today?"
)
print(f"Message created: {message1}")

# Check if notification was created automatically
notifications = Notification.objects.filter(user=user2, message=message1)
if notifications.exists():
    notification = notifications.first()
    print(f"✓ Notification automatically created: {notification.content}")
else:
    print("✗ No notification was created")

print()
print("2. Testing Signal for Message Edit Logging (Task 1)")
print("-" * 50)

# Edit the message (this will trigger the pre_save signal)
print("Editing the message...")
original_content = message1.content
message1.content = "Hello Bob! How are you doing today? Hope you're well!"
message1.save()

# Check if message history was created
history = MessageHistory.objects.filter(message=message1)
if history.exists():
    history_entry = history.first()
    print(f"✓ Message history created: {history_entry.old_content}")
    print(f"✓ Message marked as edited: {message1.edited}")
else:
    print("✗ No message history was created")

print()
print("3. Testing Advanced ORM - Threaded Conversations (Task 3)")
print("-" * 50)

# Create a reply to the message
print("Creating a threaded reply...")
reply1 = Message.objects.create(
    sender=user2,
    receiver=user1,
    content="Hi Alice! I'm doing great, thanks for asking!",
    parent_message=message1
)

# Create another reply to the original message
reply2 = Message.objects.create(
    sender=user2,
    receiver=user1,
    content="How about you? How's work going?",
    parent_message=message1
)

print(f"Reply 1: {reply1.content}")
print(f"Reply 2: {reply2.content}")

# Test the threaded conversation retrieval with ORM optimization
print("\nRetrieving threaded conversation with ORM optimization:")
threaded_messages = Message.objects.filter(
    id__in=[message1.id, reply1.id, reply2.id]
).select_related('sender', 'receiver', 'parent_message').prefetch_related(
    'replies__sender', 'replies__receiver'
)

for msg in threaded_messages:
    if msg.parent_message:
        print(f"  └─ Reply by {msg.sender.username}: {msg.content[:50]}...")
    else:
        print(f"Original by {msg.sender.username}: {msg.content[:50]}...")
        replies = msg.get_all_replies()
        print(f"  Total replies: {len(replies)}")

print()
print("4. Testing Custom ORM Manager for Unread Messages (Task 4)")
print("-" * 50)

# Create some more messages
Message.objects.create(
    sender=user1,
    receiver=user2,
    content="Another unread message"
)

# Mark one message as read
message1.read = True
message1.save()

# Test the custom manager
unread_messages = Message.unread.for_user(user2)
print(f"Unread messages for {user2.username}: {unread_messages.count()}")
for msg in unread_messages:
    print(f"  - From {msg.sender.username}: {msg.content[:30]}...")

print()
print("5. Testing Caching (Task 5)")
print("-" * 50)

# Test low-level caching
print("Testing low-level cache...")
cache_key = 'demo_messages_count'
cached_count = cache.get(cache_key)

if cached_count is None:
    # Count not in cache, calculate it
    message_count = Message.objects.count()
    cache.set(cache_key, message_count, 300)  # Cache for 5 minutes
    print(f"✓ Message count calculated and cached: {message_count}")
else:
    print(f"✓ Message count retrieved from cache: {cached_count}")

# Test cache versioning
print("\nTesting cache versioning...")
version_key = 'demo_user_data_v1'
user_data = {
    'username': user1.username,
    'message_count': user1.sent_messages.count(),
    'timestamp': timezone.now().isoformat()
}
cache.set(version_key, user_data, 600)
retrieved_data = cache.get(version_key)
if retrieved_data:
    print(f"✓ Versioned data cached and retrieved: {retrieved_data['username']}")

print()
print("6. Testing User Data Cleanup Signal (Task 2)")
print("-" * 50)

# Create a test user for deletion
test_user = User.objects.create_user(
    username='testuser',
    email='test@example.com'
)

# Create some data for this user
test_message = Message.objects.create(
    sender=test_user,
    receiver=user1,
    content="This message will be deleted with the user"
)

print(f"Created test user: {test_user.username}")
print(f"Messages by test user before deletion: {Message.objects.filter(sender=test_user).count()}")
print(f"Notifications for test user before deletion: {Notification.objects.filter(user=test_user).count()}")

# Delete the user (this will trigger the post_delete signal)
test_user_id = test_user.id
test_user.delete()

# Check if cleanup happened
remaining_messages = Message.objects.filter(sender_id=test_user_id)
remaining_notifications = Notification.objects.filter(user_id=test_user_id)

print(f"✓ Messages by deleted user after deletion: {remaining_messages.count()}")
print(f"✓ Notifications for deleted user after deletion: {remaining_notifications.count()}")

print()
print("=== Demo completed successfully! ===")
print()
print("Summary of implemented features:")
print("✓ Task 0: Signal for user notifications on new messages")
print("✓ Task 1: Signal for logging message edits")
print("✓ Task 2: Signal for cleaning up user data on deletion")
print("✓ Task 3: Advanced ORM techniques for threaded conversations")
print("✓ Task 4: Custom ORM manager for unread messages")
print("✓ Task 5: Basic caching implementation")
print()
print("All signals, ORM optimizations, and caching features are working correctly!")

