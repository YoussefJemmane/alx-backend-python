#!/usr/bin/env python
"""
Comprehensive test script for threaded conversations with advanced ORM techniques.

This script demonstrates:
1. Creating threaded conversations with parent_message relationships
2. Using prefetch_related and select_related for optimization
3. Recursive queries to fetch all replies
4. Thread tree building and visualization
5. Performance comparisons between different query strategies

Usage:
    python manage.py shell < test_threaded_conversations.py

Or in Django shell:
    exec(open('test_threaded_conversations.py').read())
"""

import os
import sys
import django
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction, connection
from django.utils import timezone
from datetime import timedelta
import time
import random

# Ensure Django is set up
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
    django.setup()

# Import models after Django setup
from models import Message, MessageHistory, Notification
from managers import ConversationTreeBuilder, ThreadAnalytics


def print_separator(title):
    """Print a nice separator with title."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def print_query_count():
    """Print the number of database queries executed."""
    print(f"Database queries executed: {len(connection.queries)}")
    connection.queries_log.clear()


def reset_query_count():
    """Reset the query counter."""
    connection.queries_log.clear()


def create_test_users(count=5):
    """Create test users for the demonstration."""
    print(f"Creating {count} test users...")
    users = []
    
    for i in range(count):
        username = f"testuser_{i+1}"
        email = f"user{i+1}@example.com"
        
        # Delete existing user if exists
        User.objects.filter(username=username).delete()
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password="testpass123"
        )
        users.append(user)
        print(f"  Created: {user.username}")
    
    return users


def create_threaded_conversation(users, depth=4, replies_per_level=2):
    """Create a complex threaded conversation for testing."""
    print(f"Creating threaded conversation with depth {depth} and {replies_per_level} replies per level...")
    
    # Create root message
    root_user = users[0]
    receiver_user = users[1]
    
    root_message = Message.objects.create(
        sender=root_user,
        receiver=receiver_user,
        content="This is the root message of our threaded conversation. Let's discuss!"
    )
    
    print(f"  Created root message: ID {root_message.id}")
    
    # Create threaded replies
    messages_created = [root_message]
    current_level = [root_message]
    
    for level in range(depth):
        next_level = []
        
        for parent in current_level:
            for reply_num in range(replies_per_level):
                # Alternate between users for replies
                sender = users[(level + reply_num) % len(users)]
                receiver = parent.sender if sender != parent.sender else parent.receiver
                
                reply = Message.objects.create(
                    parent_message=parent,
                    sender=sender,
                    receiver=receiver,
                    content=f"Reply at depth {level + 1}, reply #{reply_num + 1} to message {parent.id}"
                )
                
                next_level.append(reply)
                messages_created.append(reply)
                
                print(f"    Created reply: ID {reply.id} (depth {reply.thread_depth})")
        
        current_level = next_level
        if not current_level:  # No more messages to reply to
            break
    
    print(f"  Total messages created: {len(messages_created)}")
    return root_message, messages_created


def demonstrate_basic_queries(root_message):
    """Demonstrate basic querying without optimization."""
    print_separator("Basic Queries (Non-Optimized)")
    
    reset_query_count()
    start_time = time.time()
    
    # Get all messages in thread - inefficient way
    print("Getting thread messages the inefficient way...")
    all_messages = []
    
    def get_replies_recursive(message):
        all_messages.append(message)
        for reply in message.replies.all():  # This creates N+1 queries!
            get_replies_recursive(reply)
    
    get_replies_recursive(root_message)
    
    end_time = time.time()
    print(f"Messages found: {len(all_messages)}")
    print(f"Time taken: {end_time - start_time:.4f} seconds")
    print_query_count()


def demonstrate_optimized_queries(root_message):
    """Demonstrate optimized queries using select_related and prefetch_related."""
    print_separator("Optimized Queries with select_related and prefetch_related")
    
    reset_query_count()
    start_time = time.time()
    
    # Method 1: Using the optimized get_thread_tree method
    print("Method 1: Using optimized get_thread_tree()...")
    thread_messages = root_message.get_thread_tree()
    
    print(f"Messages found: {thread_messages.count()}")
    
    # Access related data to test optimization
    for message in thread_messages:
        _ = message.sender.username  # Should not cause additional queries
        _ = message.receiver.username  # Should not cause additional queries
        if message.parent_message:
            _ = message.parent_message.content  # Should not cause additional queries
    
    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.4f} seconds")
    print_query_count()
    
    # Method 2: Using custom manager methods
    reset_query_count()
    start_time = time.time()
    
    print("\nMethod 2: Using optimized manager method...")
    optimized_messages = Message.objects.get_thread_tree_optimized(root_message.id)
    
    print(f"Messages found: {optimized_messages.count()}")
    
    # Access related data
    for message in optimized_messages:
        _ = message.sender.username
        _ = message.receiver.username
        if message.parent_message:
            _ = message.parent_message.content
    
    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.4f} seconds")
    print_query_count()


def demonstrate_recursive_queries(root_message):
    """Demonstrate recursive query techniques."""
    print_separator("Recursive Query Techniques")
    
    # Method 1: Using Django ORM recursive method
    reset_query_count()
    start_time = time.time()
    
    print("Method 1: get_recursive_replies()...")
    recursive_replies = root_message.get_recursive_replies()
    
    print(f"Recursive replies found: {recursive_replies.count()}")
    
    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.4f} seconds")
    print_query_count()
    
    # Method 2: Using ConversationTreeBuilder
    reset_query_count()
    start_time = time.time()
    
    print("\nMethod 2: ConversationTreeBuilder...")
    thread_messages = root_message.get_thread_tree()
    tree_builder = ConversationTreeBuilder(thread_messages)
    
    tree_structure = tree_builder.get_tree_structure(root_message.id)
    flattened_thread = tree_builder.get_flattened_thread(root_message.id)
    
    print(f"Tree structure built with {len(flattened_thread)} messages")
    
    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.4f} seconds")
    print_query_count()
    
    return tree_structure, flattened_thread


def demonstrate_bulk_operations(users):
    """Demonstrate bulk operations for creating threaded messages."""
    print_separator("Bulk Operations for Threaded Messages")
    
    # Prepare bulk data
    messages_data = []
    
    # Create a root message
    root_data = {
        'sender': users[0],
        'receiver': users[1],
        'content': 'Bulk created root message',
        'parent_message': None
    }
    messages_data.append(root_data)
    
    # Create replies (we'll set parent_message after creation)
    for i in range(10):
        reply_data = {
            'sender': users[i % len(users)],
            'receiver': users[(i + 1) % len(users)],
            'content': f'Bulk created reply {i + 1}',
            'parent_message': None  # Will be set after root is created
        }
        messages_data.append(reply_data)
    
    reset_query_count()
    start_time = time.time()
    
    print("Creating messages using bulk operations...")
    
    # First create the root message
    root_message = Message.objects.create(**messages_data[0])
    
    # Update reply data to reference the root message
    for reply_data in messages_data[1:]:
        reply_data['parent_message'] = root_message
    
    # Use the custom bulk create method
    created_messages = Message.objects.bulk_create_threaded_messages(messages_data[1:])
    
    end_time = time.time()
    print(f"Created {len(created_messages) + 1} messages (including root)")
    print(f"Time taken: {end_time - start_time:.4f} seconds")
    print_query_count()
    
    return root_message


def demonstrate_analytics(users):
    """Demonstrate thread analytics functionality."""
    print_separator("Thread Analytics")
    
    # Get most active threads
    print("Most active threads for user:", users[0].username)
    active_threads = ThreadAnalytics.get_most_active_threads(users[0], limit=5)
    
    for i, thread in enumerate(active_threads, 1):
        print(f"  {i}. Thread {thread.id}: {thread.reply_count} replies")
        print(f"     Content: {thread.content[:50]}...")
    
    # Get conversation statistics
    print(f"\nConversation statistics for {users[0].username}:")
    stats = Message.objects.get_conversation_stats(users[0])
    
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Get engagement stats for a specific thread
    if active_threads:
        thread = active_threads[0]
        print(f"\nEngagement stats for thread {thread.id}:")
        engagement_stats = ThreadAnalytics.get_thread_engagement_stats(thread.id)
        
        if engagement_stats:
            for key, value in engagement_stats.items():
                print(f"  {key}: {value}")


def demonstrate_search_functionality(users):
    """Demonstrate search within threaded conversations."""
    print_separator("Search Functionality")
    
    # Search for messages
    search_term = "reply"
    print(f"Searching for messages containing '{search_term}'...")
    
    reset_query_count()
    start_time = time.time()
    
    search_results = Message.objects.search_in_threads(search_term, users[0])
    
    print(f"Found {search_results.count()} messages")
    
    # Group by thread
    threads = {}
    for message in search_results[:10]:  # Limit to first 10 for demo
        root = message.get_thread_root()
        if root.id not in threads:
            threads[root.id] = []
        threads[root.id].append(message)
    
    print(f"Results grouped into {len(threads)} threads:")
    for thread_id, messages in threads.items():
        print(f"  Thread {thread_id}: {len(messages)} matching messages")
    
    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.4f} seconds")
    print_query_count()


def demonstrate_performance_comparison(root_message):
    """Compare performance of different query strategies."""
    print_separator("Performance Comparison")
    
    strategies = [
        ("Basic recursive (N+1 queries)", demonstrate_basic_queries),
        ("Optimized with select_related/prefetch_related", demonstrate_optimized_queries),
        ("Custom recursive queries", demonstrate_recursive_queries)
    ]
    
    results = []
    
    for strategy_name, strategy_func in strategies:
        print(f"\nTesting: {strategy_name}")
        
        reset_query_count()
        start_time = time.time()
        
        try:
            if strategy_name.startswith("Custom"):
                strategy_func(root_message)
            else:
                strategy_func(root_message)
        except Exception as e:
            print(f"Error in {strategy_name}: {e}")
            continue
        
        end_time = time.time()
        query_count = len(connection.queries)
        
        results.append({
            'strategy': strategy_name,
            'time': end_time - start_time,
            'queries': query_count
        })
        
        print(f"  Time: {end_time - start_time:.4f}s, Queries: {query_count}")
    
    # Print summary
    print("\nPerformance Summary:")
    print("-" * 60)
    print(f"{'Strategy':<40} {'Time (s)':<10} {'Queries':<10}")
    print("-" * 60)
    
    for result in results:
        print(f"{result['strategy']:<40} {result['time']:<10.4f} {result['queries']:<10}")


def visualize_thread_structure(tree_structure, max_depth=3):
    """Visualize the thread structure in a tree format."""
    print_separator("Thread Structure Visualization")
    
    def print_tree_node(node, depth=0, prefix=""):
        if depth > max_depth:
            return
        
        message = node['message']
        indent = "  " * depth
        
        # Use different symbols for different depths
        symbols = ["🌳", "🌿", "🍃", "🌱", "🌾"]
        symbol = symbols[min(depth, len(symbols) - 1)]
        
        print(f"{indent}{symbol} [{message.id}] {message.sender.username}: {message.content[:50]}...")
        print(f"{indent}   📅 {message.timestamp.strftime('%Y-%m-%d %H:%M')} | 📊 Depth: {message.thread_depth}")
        
        if message.edited:
            print(f"{indent}   ✏️ Edited {message.edit_count} time(s)")
        
        # Print children
        for i, child in enumerate(node['children']):
            child_prefix = prefix + ("├── " if i < len(node['children']) - 1 else "└── ")
            print_tree_node(child, depth + 1, child_prefix)
    
    if tree_structure:
        print("Thread Tree Structure:")
        print_tree_node(tree_structure)
    else:
        print("No tree structure to display.")


def cleanup_test_data():
    """Clean up test data created during the demonstration."""
    print_separator("Cleanup")
    
    print("Cleaning up test data...")
    
    # Delete test users (this will cascade to delete their messages)
    deleted_users = User.objects.filter(username__startswith='testuser_').delete()
    print(f"Deleted {deleted_users[0]} test users and related data")
    
    print("Cleanup completed.")


def main():
    """Main demonstration function."""
    print_separator("Advanced ORM Techniques for Threaded Conversations")
    print("This demonstration shows optimized querying, recursive relationships,")
    print("and advanced Django ORM techniques for threaded messaging.")
    
    try:
        # Setup test data
        users = create_test_users(5)
        
        # Create a complex threaded conversation
        root_message, all_messages = create_threaded_conversation(users, depth=3, replies_per_level=2)
        
        # Demonstrate different query techniques
        demonstrate_optimized_queries(root_message)
        tree_structure, flattened_thread = demonstrate_recursive_queries(root_message)
        
        # Visualize the thread structure
        visualize_thread_structure(tree_structure)
        
        # Demonstrate bulk operations
        bulk_root = demonstrate_bulk_operations(users)
        
        # Demonstrate analytics
        demonstrate_analytics(users)
        
        # Demonstrate search
        demonstrate_search_functionality(users)
        
        # Performance comparison (commented out to avoid N+1 query issues in demo)
        # print("\nSkipping performance comparison to avoid N+1 query performance issues...")
        # demonstrate_performance_comparison(root_message)
        
        print_separator("Demonstration Completed Successfully")
        print("All advanced ORM techniques have been demonstrated:")
        print("✅ Self-referential foreign keys (parent_message)")
        print("✅ select_related and prefetch_related optimization")
        print("✅ Recursive queries for thread traversal")
        print("✅ Custom managers and querysets")
        print("✅ Bulk operations for performance")
        print("✅ Thread analytics and statistics")
        print("✅ Advanced search functionality")
        print("✅ Tree structure visualization")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Ask user if they want to cleanup
        try:
            response = input("\nDo you want to clean up test data? (y/n): ")
            if response.lower() in ['y', 'yes']:
                cleanup_test_data()
            else:
                print("Test data preserved for further examination.")
        except (EOFError, KeyboardInterrupt):
            print("\nTest data preserved.")


if __name__ == "__main__":
    main()

