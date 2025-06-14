#!/usr/bin/env python
"""
Demo script showcasing the Custom ORM Manager for Unread Messages.

This script demonstrates:
1. The read boolean field in the Message model
2. The UnreadMessagesManager custom manager
3. Query optimization with .only() for retrieving necessary fields
4. Usage in views to display unread messages in user's inbox

Run this script in Django shell:
python manage.py shell < demo_unread_manager.py
"""

import os
import sys
import django
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import connection

# Setup Django if not already done
if not hasattr(django, 'setup_called'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
    django.setup()
    django.setup_called = True

from Models.models import Message, Notification

def demo_unread_messages_manager():
    """
    Comprehensive demonstration of the UnreadMessagesManager.
    """
    print("=" * 80)
    print("CUSTOM ORM MANAGER FOR UNREAD MESSAGES - DEMONSTRATION")
    print("=" * 80)
    
    # Get or create test users
    user1, created = User.objects.get_or_create(
        username='demo_user_1',
        defaults={'email': 'user1@example.com'}
    )
    user2, created = User.objects.get_or_create(
        username='demo_user_2', 
        defaults={'email': 'user2@example.com'}
    )
    user3, created = User.objects.get_or_create(
        username='demo_user_3',
        defaults={'email': 'user3@example.com'}
    )
    
    print(f"\n1. SETUP: Using test users:")
    print(f"   - {user1.username} (ID: {user1.id})")
    print(f"   - {user2.username} (ID: {user2.id})")
    print(f"   - {user3.username} (ID: {user3.id})")
    
    # Create sample messages (some read, some unread)
    print(f"\n2. CREATING SAMPLE MESSAGES:")
    
    # Messages from user2 to user1 (some unread)
    msg1 = Message.objects.create(
        sender=user2,
        receiver=user1,
        content="Hello! This is an unread message.",
        is_read=False  # Unread
    )
    
    msg2 = Message.objects.create(
        sender=user2,
        receiver=user1,
        content="This is another unread message from user2.",
        is_read=False  # Unread
    )
    
    msg3 = Message.objects.create(
        sender=user2,
        receiver=user1,
        content="This message has been read.",
        is_read=True  # Read
    )
    
    # Messages from user3 to user1 (mix of read/unread)
    msg4 = Message.objects.create(
        sender=user3,
        receiver=user1,
        content="Urgent message from user3!",
        is_read=False  # Unread
    )
    
    msg5 = Message.objects.create(
        sender=user3,
        receiver=user1,
        content="Follow-up message from user3.",
        is_read=True  # Read
    )
    
    # Old unread message (for recent filter demo)
    old_msg = Message.objects.create(
        sender=user2,
        receiver=user1,
        content="This is an old unread message.",
        is_read=False,
        timestamp=timezone.now() - timedelta(days=2)
    )
    
    print(f"   ✓ Created {Message.objects.count()} total messages")
    print(f"   ✓ {Message.objects.filter(is_read=False).count()} unread messages")
    print(f"   ✓ {Message.objects.filter(is_read=True).count()} read messages")
    
    print(f"\n3. DEMONSTRATING UnreadMessagesManager:")
    
    # Basic unread messages for user
    print(f"\n   3.1 Basic unread messages for {user1.username}:")
    unread_basic = Message.unread.for_user(user1)
    print(f"       Count: {unread_basic.count()}")
    for msg in unread_basic:
        print(f"       - From {msg.sender.username}: \"{msg.content[:30]}...\"")
    
    # Optimized inbox query with .only()
    print(f"\n   3.2 Optimized inbox query (using .only() for performance):")
    print(f"       SQL Query optimization with .only() - fetching minimal fields:")
    
    # Show the SQL query being generated
    with connection.cursor() as cursor:
        initial_queries = len(connection.queries)
        
        optimized_inbox = Message.unread.optimized_inbox(user1, limit=10)
        list(optimized_inbox)  # Execute the query
        
        final_queries = len(connection.queries)
        if final_queries > initial_queries:
            last_query = connection.queries[-1]['sql']
            print(f"       SQL: {last_query[:100]}...")
    
    print(f"       Retrieved {optimized_inbox.count()} messages with optimized field selection")
    
    # Unread messages by sender
    print(f"\n   3.3 Unread messages grouped by sender:")
    unread_by_sender = Message.unread.unread_count_by_sender(user1)
    for sender_info in unread_by_sender:
        print(f"       - {sender_info['sender__username']}: {sender_info['unread_count']} unread")
    
    # Recent unread messages (last 24 hours)
    print(f"\n   3.4 Recent unread messages (last 24 hours):")
    recent_unread = Message.unread.recent_unread(user1, hours=24)
    print(f"       Count: {recent_unread.count()}")
    for msg in recent_unread:
        print(f"       - From {msg.sender.username}: \"{msg.content[:30]}...\"")
    
    # Unread summary statistics
    print(f"\n   3.5 Comprehensive unread summary:")
    summary = Message.unread.get_unread_summary(user1)
    print(f"       Total unread: {summary['total_unread']}")
    print(f"       Unique senders: {summary['unique_senders']}")
    print(f"       Unread threads: {summary['unread_threads']}")
    if summary['oldest_unread']:
        print(f"       Oldest unread: {summary['oldest_unread'].strftime('%Y-%m-%d %H:%M')}")
    if summary['newest_unread']:
        print(f"       Newest unread: {summary['newest_unread'].strftime('%Y-%m-%d %H:%M')}")
    
    # Unread messages from specific sender
    print(f"\n   3.6 Unread messages from specific sender ({user2.username}):")
    from_user2 = Message.unread.unread_by_sender(user1, user2)
    print(f"       Count: {from_user2.count()}")
    for msg in from_user2:
        print(f"       - \"{msg.content[:40]}...\"")
    
    # Threaded unread messages
    print(f"\n   3.7 Unread messages organized by threads:")
    unread_threads = Message.unread.unread_threads(user1)
    print(f"       Total unread messages in threads: {unread_threads.count()}")
    
    # Check if user has any unread messages (optimized)
    print(f"\n   3.8 Quick unread check (optimized .exists() query):")
    has_unread = Message.unread.has_unread(user1)
    print(f"       {user1.username} has unread messages: {has_unread}")
    
    # Get latest unread messages
    print(f"\n   3.9 Latest 3 unread messages (minimal fields):")
    latest_unread = Message.unread.latest_unread(user1, count=3)
    for msg in latest_unread:
        print(f"       - From {msg.sender.username}: \"{msg.content[:30]}...\"")
    
    print(f"\n4. DEMONSTRATING BULK OPERATIONS:")
    
    # Mark specific messages as read
    print(f"\n   4.1 Marking specific messages as read:")
    unread_ids = list(Message.unread.for_user(user1).values_list('id', flat=True)[:2])
    print(f"       Marking messages {unread_ids} as read...")
    
    marked_count = Message.unread.mark_as_read(user1, unread_ids)
    print(f"       ✓ Marked {marked_count} messages as read")
    print(f"       Remaining unread: {Message.unread.unread_count(user1)}")
    
    # Mark all messages from a sender as read
    print(f"\n   4.2 Marking all messages from {user3.username} as read:")
    sender_marked = Message.unread.batch_mark_read_by_sender(user1, user3)
    print(f"       ✓ Marked {sender_marked} messages from {user3.username} as read")
    print(f"       Remaining unread: {Message.unread.unread_count(user1)}")
    
    print(f"\n5. FIELD OPTIMIZATION DEMONSTRATION:")
    
    # Show the difference between regular query and optimized query
    print(f"\n   5.1 Comparing regular vs optimized queries:")
    
    # Regular query (fetches all fields)
    print(f"       Regular query (all fields):")
    regular_query = Message.objects.filter(receiver=user1, is_read=False)
    print(f"       - Fetches all model fields: {[f.name for f in Message._meta.fields]}")
    
    # Optimized query (only specific fields)
    print(f"\n       Optimized query (only necessary fields):")
    optimized_query = Message.unread.optimized_inbox(user1)
    print(f"       - Only fetches: id, sender, content, timestamp, is_read, thread_depth, parent_message")
    print(f"       - Plus related sender information for display")
    
    print(f"\n6. INTEGRATION WITH VIEWS:")
    print(f"\n   The custom manager is now integrated into views:")
    print(f"   - /inbox/ - Main unread messages inbox")
    print(f"   - /inbox/threads/ - Unread messages by thread")
    print(f"   - /inbox/recent/ - Recent unread messages")
    print(f"   - API endpoints for marking messages as read")
    
    print(f"\n" + "=" * 80)
    print(f"DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print(f"")
    print(f"Key Features Demonstrated:")
    print(f"✓ Read boolean field in Message model")
    print(f"✓ UnreadMessagesManager custom manager")
    print(f"✓ Query optimization with .only() method")
    print(f"✓ Multiple filtering and aggregation methods")
    print(f"✓ Bulk operations for marking as read")
    print(f"✓ Integration with Django views")
    print(f"✓ Performance optimizations for large datasets")
    print(f"=" * 80)

def demo_manager_methods():
    """
    Demonstrate all available methods in UnreadMessagesManager.
    """
    print(f"\n" + "=" * 60)
    print(f"AVAILABLE UNREADMESSAGESMANAGER METHODS:")
    print(f"=" * 60)
    
    manager_methods = [
        ('for_user(user)', 'Get all unread messages for a specific user'),
        ('optimized_inbox(user, limit=50)', 'Optimized unread messages for inbox display'),
        ('recent_unread(user, hours=24)', 'Recent unread messages'),
        ('unread_by_sender(user, sender)', 'Unread messages from specific sender'),
        ('unread_count_by_sender(user)', 'Count unread messages grouped by sender'),
        ('unread_threads(user)', 'Unread messages organized by thread'),
        ('priority_unread(user, priority_senders)', 'Unread with priority sorting'),
        ('mark_as_read(user, message_ids)', 'Mark specific messages as read'),
        ('get_unread_summary(user)', 'Comprehensive unread statistics'),
        ('has_unread(user)', 'Quick check if user has unread messages'),
        ('unread_count(user)', 'Total count of unread messages'),
        ('latest_unread(user, count=5)', 'Latest N unread messages'),
        ('unread_from_conversation(user, root_id)', 'Unread from specific thread'),
        ('batch_mark_read_by_sender(user, sender)', 'Mark all from sender as read'),
        ('auto_mark_old_as_read(user, days=30)', 'Auto-mark old messages as read')
    ]
    
    for method, description in manager_methods:
        print(f"  {method:<45} - {description}")
    
    print(f"\nQuerySet Methods (via get_queryset()):")
    queryset_methods = [
        ('unread_for_user(user)', 'Filter unread for user'),
        ('optimized_unread(user)', 'Optimized field selection'),
        ('inbox_optimized(user)', 'Inbox display optimization'),
        ('unread_summary(user)', 'Statistical summary'),
        ('mark_as_read_bulk(user, ids)', 'Bulk mark as read')
    ]
    
    for method, description in queryset_methods:
        print(f"  {method:<45} - {description}")
    
    print(f"=" * 60)

if __name__ == "__main__":
    try:
        demo_unread_messages_manager()
        demo_manager_methods()
    except Exception as e:
        print(f"Error running demo: {e}")
        import traceback
        traceback.print_exc()

