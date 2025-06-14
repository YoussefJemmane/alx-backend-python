"""
Django-Chat Models Package

This package implements advanced ORM techniques for threaded conversations
including:

- Self-referential foreign keys for parent_message relationships
- Custom managers and querysets for optimized querying
- select_related and prefetch_related for N+1 query prevention
- Recursive queries for thread traversal
- Bulk operations for performance
- Thread analytics and statistics
- Tree structure building and visualization

Key Components:
- models.py: Enhanced Message model with threading support
- managers.py: Custom managers and querysets for optimization
- views.py: Views demonstrating threaded conversation functionality
- urls.py: URL patterns for the views
- templates/: HTML templates for threaded conversation display
- test_threaded_conversations.py: Comprehensive test and demo script

The implementation showcases advanced Django ORM techniques for efficiently
handling hierarchical data structures and complex relationships.
"""

__version__ = '1.0.0'
__author__ = 'Django Chat Team'

# Import key classes for easy access
from .models import Message, MessageHistory, Notification
from .managers import (
    ThreadedMessageManager,
    ThreadedMessageQuerySet,
    ConversationTreeBuilder,
    ThreadAnalytics
)

__all__ = [
    'Message',
    'MessageHistory', 
    'Notification',
    'ThreadedMessageManager',
    'ThreadedMessageQuerySet',
    'ConversationTreeBuilder',
    'ThreadAnalytics',
]

# Django Chat Models package
default_app_config = 'Django-Chat.Models.apps.DjangoChatConfig'

