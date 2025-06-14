#!/usr/bin/env python
"""
Demonstration script for the messaging system with automatic notifications.

This script shows how the Django signals automatically create notifications
when new messages are created.

Usage:
    python manage.py shell
    exec(open('messaging/demo.py').read())
"""

from django.contrib.auth.models import User
from messaging.models import Message, Notification


def demo_messaging_system():
    """Demonstrate the messaging system with automatic notifications."""
    
    print("=== Django Signals for User Notifications Demo ===")
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
    
    # Show initial notification count
    print("2. Initial notification counts:")
    print(f"   Alice has {user1.notifications.count()} notifications")
    print(f"   Bob has {user2.notifications.count()} notifications")
    print()
    
    # Create messages and show automatic notification creation
    print("3. Creating messages and observing automatic notifications...")
    
    # Alice sends message to Bob
    print("   Alice sends message to Bob...")
    message1 = Message.objects.create(
        sender=user1,
        receiver=user2,
        content="Hey Bob! How are you doing?"
    )
    print(f"   ✓ Message created: {message1}")
    print(f"   ✓ Bob now has {user2.notifications.count()} notifications")
    
    # Show Bob's notification
    latest_notification = user2.notifications.first()
    if latest_notification:
        print(f"   ✓ Latest notification for Bob: '{latest_notification.notification_text}'")
    
    print()
    
    # Bob replies to Alice
    print("   Bob replies to Alice...")
    message2 = Message.objects.create(
        sender=user2,
        receiver=user1,
        content="Hi Alice! I'm doing great, thanks for asking!"
    )
    print(f"   ✓ Message created: {message2}")
    print(f"   ✓ Alice now has {user1.notifications.count()} notifications")
    
    # Show Alice's notification
    latest_notification = user1.notifications.first()
    if latest_notification:
        print(f"   ✓ Latest notification for Alice: '{latest_notification.notification_text}'")
    
    print()
    
    # Show final counts
    print("4. Final counts:")
    print(f"   Total messages: {Message.objects.count()}")
    print(f"   Total notifications: {Notification.objects.count()}")
    print(f"   Alice's notifications: {user1.notifications.count()}")
    print(f"   Bob's notifications: {user2.notifications.count()}")
    
    print()
    print("5. All notifications:")
    for notification in Notification.objects.all().order_by('-created_at'):
        print(f"   - {notification}")
    
    print()
    print("=== Demo Complete ===")
    print("The Django post_save signal automatically created notifications")
    print("whenever a new Message instance was saved to the database!")


if __name__ == '__main__':
    # This will run when executed directly
    demo_messaging_system()

