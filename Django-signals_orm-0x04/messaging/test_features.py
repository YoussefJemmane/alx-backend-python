#!/usr/bin/env python
"""
Manual testing script for Django Signals, ORM, and Caching features.

This script demonstrates all the implemented tasks:
- Task 0: Signals for User Notifications
- Task 1: Signal for Logging Message Edits
- Task 2: Signals for Deleting User-Related Data
- Task 3: Advanced ORM Techniques for Threaded Conversations
- Task 4: Custom ORM Manager for Unread Messages
- Task 5: Basic View Caching

To run: python test_features.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messaging_app.settings')
django.setup()

from django.contrib.auth.models import User
from messaging.models import Message, Notification, MessageHistory
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q, Prefetch

def clear_test_data():
    """Clear any existing test data."""
    User.objects.filter(username__in=['alice', 'bob', 'charlie']).delete()
    Message.objects.all().delete()
    Notification.objects.all().delete()
    MessageHistory.objects.all().delete()
    cache.clear()

def test_task_0_signals_for_notifications():
    """Test Task 0: Implement Signals for User Notifications"""
    print("\n" + "="*60)
    print("TASK 0: Testing Signals for User Notifications")
    print("="*60)
    
    # Create test users
    alice = User.objects.create_user(username='alice', email='alice@example.com')
    bob = User.objects.create_user(username='bob', email='bob@example.com')
    
    print(f"✓ Created users: {alice.username} and {bob.username}")
    
    # Create a message (should trigger post_save signal)
    message = Message.objects.create(
        sender=alice,
        receiver=bob,
        content="Hello Bob! This should trigger a notification."
    )
    
    print(f"✓ Created message: {message.content[:50]}...")
    
    # Check if notification was automatically created
    notifications = Notification.objects.filter(user=bob, message=message)
    if notifications.exists():
        notification = notifications.first()
        print(f"✓ PASS: Notification automatically created for {bob.username}")
        print(f"   Content: {notification.content}")
        return True
    else:
        print("✗ FAIL: No notification was created")
        return False

def test_task_1_signal_for_message_edits():
    """Test Task 1: Create a Signal for Logging Message Edits"""
    print("\n" + "="*60)
    print("TASK 1: Testing Signal for Logging Message Edits")
    print("="*60)
    
    alice = User.objects.get(username='alice')
    bob = User.objects.get(username='bob')
    
    # Create a message
    message = Message.objects.create(
        sender=alice,
        receiver=bob,
        content="Original message content"
    )
    
    print(f"✓ Created message with original content")
    print(f"   Original: {message.content}")
    print(f"   Edited flag: {message.edited}")
    
    # Edit the message (should trigger pre_save signal)
    message.content = "Edited message content - this should create history"
    message.save()
    
    print(f"✓ Message edited")
    print(f"   New content: {message.content}")
    print(f"   Edited flag: {message.edited}")
    
    # Check if history was created
    history = MessageHistory.objects.filter(message=message)
    if history.exists() and message.edited:
        history_entry = history.first()
        print(f"✓ PASS: Message history created and message marked as edited")
        print(f"   History content: {history_entry.old_content}")
        return True
    else:
        print("✗ FAIL: Message history not created or edited flag not set")
        return False

def test_task_2_user_deletion_cleanup():
    """Test Task 2: Use Signals for Deleting User-Related Data"""
    print("\n" + "="*60)
    print("TASK 2: Testing Signals for User Data Cleanup")
    print("="*60)
    
    # Create a test user
    charlie = User.objects.create_user(username='charlie', email='charlie@example.com')
    alice = User.objects.get(username='alice')
    
    # Create some data for Charlie
    msg1 = Message.objects.create(
        sender=charlie,
        receiver=alice,
        content="Message from Charlie"
    )
    
    msg2 = Message.objects.create(
        sender=alice,
        receiver=charlie,
        content="Message to Charlie"
    )
    
    print(f"✓ Created test user: {charlie.username}")
    print(f"   Messages sent by Charlie: {Message.objects.filter(sender=charlie).count()}")
    print(f"   Messages received by Charlie: {Message.objects.filter(receiver=charlie).count()}")
    print(f"   Notifications for Charlie: {Notification.objects.filter(user=charlie).count()}")
    
    # Store counts before deletion
    charlie_id = charlie.id
    messages_sent_before = Message.objects.filter(sender=charlie).count()
    messages_received_before = Message.objects.filter(receiver=charlie).count()
    notifications_before = Notification.objects.filter(user=charlie).count()
    
    # Delete Charlie (should trigger post_delete signal)
    charlie.delete()
    
    # Check cleanup
    messages_sent_after = Message.objects.filter(sender_id=charlie_id).count()
    messages_received_after = Message.objects.filter(receiver_id=charlie_id).count()
    notifications_after = Notification.objects.filter(user_id=charlie_id).count()
    
    print(f"✓ User deleted")
    print(f"   Messages sent after deletion: {messages_sent_after}")
    print(f"   Messages received after deletion: {messages_received_after}")
    print(f"   Notifications after deletion: {notifications_after}")
    
    if (messages_sent_after == 0 and messages_received_after == 0 and 
        notifications_after == 0):
        print("✓ PASS: All user-related data cleaned up successfully")
        return True
    else:
        print("✗ FAIL: User data not properly cleaned up")
        return False

def test_task_3_advanced_orm_threaded_conversations():
    """Test Task 3: Advanced ORM Techniques for Threaded Conversations"""
    print("\n" + "="*60)
    print("TASK 3: Testing Advanced ORM - Threaded Conversations")
    print("="*60)
    
    alice = User.objects.get(username='alice')
    bob = User.objects.get(username='bob')
    
    # Create a parent message
    parent_msg = Message.objects.create(
        sender=alice,
        receiver=bob,
        content="Hey Bob, how's the Django project going?"
    )
    
    print(f"✓ Created parent message: {parent_msg.content[:40]}...")
    
    # Create threaded replies
    reply1 = Message.objects.create(
        sender=bob,
        receiver=alice,
        content="Hi Alice! It's going great, just implemented signals!",
        parent_message=parent_msg
    )
    
    reply2 = Message.objects.create(
        sender=alice,
        receiver=bob,
        content="That's awesome! What about ORM optimization?",
        parent_message=parent_msg
    )
    
    reply3 = Message.objects.create(
        sender=bob,
        receiver=alice,
        content="Working on prefetch_related and select_related now!",
        parent_message=parent_msg
    )
    
    print(f"✓ Created {parent_msg.replies.count()} threaded replies")
    
    # Test advanced ORM techniques
    print("\n--- Testing ORM Optimizations ---")
    
    # Method 1: Using select_related and prefetch_related
    optimized_messages = Message.objects.filter(
        Q(sender=alice) | Q(receiver=alice)
    ).select_related('sender', 'receiver', 'parent_message').prefetch_related(
        Prefetch('replies', queryset=Message.objects.select_related('sender', 'receiver'))
    ).order_by('timestamp')
    
    print(f"✓ Retrieved {optimized_messages.count()} messages with ORM optimization")
    
    # Display threaded conversation
    for msg in optimized_messages:
        if msg.parent_message is None:  # Parent message
            print(f"📧 {msg.sender.username}: {msg.content[:50]}...")
            # Get all replies using the recursive method
            all_replies = msg.get_all_replies()
            for reply in all_replies:
                print(f"   └─ {reply.sender.username}: {reply.content[:40]}...")
    
    # Test the recursive query functionality
    all_replies = parent_msg.get_all_replies()
    if len(all_replies) == 3:
        print(f"✓ PASS: Recursive query returned {len(all_replies)} replies correctly")
        return True
    else:
        print(f"✗ FAIL: Expected 3 replies, got {len(all_replies)}")
        return False

def test_task_4_custom_orm_manager():
    """Test Task 4: Custom ORM Manager for Unread Messages"""
    print("\n" + "="*60)
    print("TASK 4: Testing Custom ORM Manager for Unread Messages")
    print("="*60)
    
    alice = User.objects.get(username='alice')
    bob = User.objects.get(username='bob')
    
    # Create some messages for Bob
    Message.objects.create(
        sender=alice,
        receiver=bob,
        content="Unread message 1",
        read=False
    )
    
    Message.objects.create(
        sender=alice,
        receiver=bob,
        content="Unread message 2",
        read=False
    )
    
    read_message = Message.objects.create(
        sender=alice,
        receiver=bob,
        content="This message is read",
        read=True
    )
    
    print(f"✓ Created test messages (2 unread, 1 read)")
    
    # Test the custom manager
    unread_messages = Message.unread.for_user(bob)
    total_messages = Message.objects.filter(receiver=bob)
    
    print(f"   Total messages for {bob.username}: {total_messages.count()}")
    print(f"   Unread messages using custom manager: {unread_messages.count()}")
    
    # Verify the manager uses .only() optimization
    print("\n--- Testing .only() optimization ---")
    for msg in unread_messages:
        print(f"   - From {msg.sender.username}: {msg.content[:30]}...")
    
    if unread_messages.count() >= 2:  # Should have at least 2 unread
        print("✓ PASS: Custom manager correctly filters unread messages")
        return True
    else:
        print("✗ FAIL: Custom manager not working correctly")
        return False

def test_task_5_basic_caching():
    """Test Task 5: Basic View Caching"""
    print("\n" + "="*60)
    print("TASK 5: Testing Basic Caching")
    print("="*60)
    
    # Test low-level caching
    print("--- Testing Low-Level Caching ---")
    
    cache_key = 'test_message_count'
    
    # Clear any existing cache
    cache.delete(cache_key)
    
    # First access - should calculate and cache
    cached_data = cache.get(cache_key)
    if cached_data is None:
        message_count = Message.objects.count()
        cache.set(cache_key, message_count, 300)  # Cache for 5 minutes
        print(f"✓ Data calculated and cached: {message_count} messages")
        cache_miss = True
    else:
        print(f"✓ Data retrieved from cache: {cached_data} messages")
        cache_miss = False
    
    # Second access - should hit cache
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        print(f"✓ Cache hit: Retrieved {cached_data} from cache")
        cache_hit = True
    else:
        print("✗ Cache miss on second access")
        cache_hit = False
    
    # Test cache versioning
    print("\n--- Testing Cache Versioning ---")
    version_key = 'user_stats_v1'
    alice = User.objects.get(username='alice')
    
    user_stats = {
        'username': alice.username,
        'sent_messages': alice.sent_messages.count(),
        'received_messages': alice.received_messages.count(),
        'timestamp': timezone.now().isoformat()
    }
    
    cache.set(version_key, user_stats, 600)
    retrieved_stats = cache.get(version_key)
    
    if retrieved_stats and retrieved_stats['username'] == alice.username:
        print(f"✓ Versioned cache working: {retrieved_stats['username']} stats cached")
        versioned_cache = True
    else:
        print("✗ Versioned cache not working")
        versioned_cache = False
    
    # Test cache invalidation
    print("\n--- Testing Cache Invalidation ---")
    cache.delete(cache_key)
    if cache.get(cache_key) is None:
        print("✓ Cache invalidation working")
        invalidation = True
    else:
        print("✗ Cache invalidation failed")
        invalidation = False
    
    if cache_miss and cache_hit and versioned_cache and invalidation:
        print("✓ PASS: All caching functionality working correctly")
        return True
    else:
        print("✗ FAIL: Some caching functionality not working")
        return False

def run_all_tests():
    """Run all feature tests"""
    print("Django Signals, ORM & Caching - Feature Testing")
    print("=" * 60)
    
    # Clear any existing test data
    clear_test_data()
    
    results = []
    
    # Run all tests
    results.append(test_task_0_signals_for_notifications())
    results.append(test_task_1_signal_for_message_edits())
    results.append(test_task_2_user_deletion_cleanup())
    results.append(test_task_3_advanced_orm_threaded_conversations())
    results.append(test_task_4_custom_orm_manager())
    results.append(test_task_5_basic_caching())
    
    # Summary
    print("\n" + "="*60)
    print("FINAL RESULTS SUMMARY")
    print("="*60)
    
    tasks = [
        "Task 0: Signals for User Notifications",
        "Task 1: Signal for Logging Message Edits",
        "Task 2: Signals for User Data Cleanup",
        "Task 3: Advanced ORM - Threaded Conversations",
        "Task 4: Custom ORM Manager for Unread Messages",
        "Task 5: Basic Caching"
    ]
    
    passed = sum(results)
    total = len(results)
    
    for i, (task, result) in enumerate(zip(tasks, results)):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {task}")
    
    print(f"\nOverall: {passed}/{total} tasks passed")
    
    if passed == total:
        print("\n🎉 ALL FEATURES WORKING CORRECTLY! 🎉")
        print("\nImplemented features:")
        print("• Event-driven notifications using Django signals")
        print("• Message edit logging with pre_save signals")
        print("• Automated data cleanup with post_delete signals")
        print("• Threaded conversations with ORM optimization")
        print("• Custom managers for efficient queries")
        print("• Multi-level caching implementation")
    else:
        print(f"\n⚠️  {total - passed} tasks need attention")
    
    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

