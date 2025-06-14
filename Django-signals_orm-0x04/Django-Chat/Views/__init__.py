"""
Django-Chat Views Package

This package contains views for user account deletion with automatic cleanup
of related data using Django signals.

Key components:
- views.py: View functions for user deletion
- urls.py: URL patterns for the views
- templates/: HTML templates for the user interface
- test_user_deletion.py: Test script demonstrating functionality

The main feature is the post_delete signal that automatically cleans up
all user-related data when a user account is deleted, including:
- Messages (sent and received)
- Notifications
- Message edit history
- Any other related records

This ensures data consistency and prevents orphaned records in the database.
"""

__version__ = '1.0.0'
__author__ = 'Django Chat Team'

