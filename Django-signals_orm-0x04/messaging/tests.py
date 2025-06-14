from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Message, Notification
from .signals import create_message_notification


class MessageModelTest(TestCase):
    """Test cases for the Message model."""
    
    def setUp(self):
        """Set up test data."""
        self.sender = User.objects.create_user(
            username='sender_user',
            email='sender@example.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver_user',
            email='receiver@example.com',
            password='testpass123'
        )
    
    def test_message_creation(self):
        """Test that a message can be created successfully."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Hello, this is a test message!"
        )
        
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.receiver, self.receiver)
        self.assertEqual(message.content, "Hello, this is a test message!")
        self.assertFalse(message.is_read)
        self.assertIsNotNone(message.timestamp)
    
    def test_message_str_representation(self):
        """Test the string representation of a message."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Test message"
        )
        
        expected_str = f"Message from {self.sender.username} to {self.receiver.username} at {message.timestamp}"
        self.assertEqual(str(message), expected_str)
    
    def test_message_ordering(self):
        """Test that messages are ordered by timestamp (newest first)."""
        message1 = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="First message"
        )
        message2 = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Second message"
        )
        
        messages = Message.objects.all()
        self.assertEqual(messages[0], message2)  # Newest first
        self.assertEqual(messages[1], message1)


class NotificationModelTest(TestCase):
    """Test cases for the Notification model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='test_user',
            email='user@example.com',
            password='testpass123'
        )
        self.sender = User.objects.create_user(
            username='sender_user',
            email='sender@example.com',
            password='testpass123'
        )
        self.message = Message.objects.create(
            sender=self.sender,
            receiver=self.user,
            content="Test message"
        )
    
    def test_notification_creation(self):
        """Test that a notification can be created successfully."""
        notification = Notification.objects.create(
            user=self.user,
            message=self.message,
            notification_text="You have a new message"
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.message, self.message)
        self.assertEqual(notification.notification_text, "You have a new message")
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(notification.created_at)
    
    def test_notification_str_representation(self):
        """Test the string representation of a notification."""
        notification = Notification.objects.create(
            user=self.user,
            message=self.message,
            notification_text="You have a new message"
        )
        
        expected_str = f"Notification for {self.user.username}: You have a new message"
        self.assertEqual(str(notification), expected_str)


class MessageSignalTest(TestCase):
    """Test cases for message-related signals."""
    
    def setUp(self):
        """Set up test data."""
        self.sender = User.objects.create_user(
            username='sender_user',
            email='sender@example.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver_user',
            email='receiver@example.com',
            password='testpass123'
        )
    
    def test_notification_created_on_message_save(self):
        """Test that a notification is automatically created when a new message is saved."""
        # Ensure no notifications exist initially
        self.assertEqual(Notification.objects.count(), 0)
        
        # Create a new message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Hello, this should trigger a notification!"
        )
        
        # Check that a notification was created
        self.assertEqual(Notification.objects.count(), 1)
        
        notification = Notification.objects.first()
        self.assertEqual(notification.user, self.receiver)
        self.assertEqual(notification.message, message)
        self.assertEqual(notification.notification_text, f"You have a new message from {self.sender.username}")
        self.assertFalse(notification.is_read)
    
    def test_no_notification_on_message_update(self):
        """Test that no new notification is created when an existing message is updated."""
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original message"
        )
        
        # Verify one notification was created
        self.assertEqual(Notification.objects.count(), 1)
        
        # Update the message
        message.content = "Updated message content"
        message.save()
        
        # Verify no additional notification was created
        self.assertEqual(Notification.objects.count(), 1)
    
    def test_multiple_messages_create_multiple_notifications(self):
        """Test that multiple messages create multiple notifications."""
        # Create first message
        message1 = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="First message"
        )
        
        # Create second message
        message2 = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Second message"
        )
        
        # Check that two notifications were created
        self.assertEqual(Notification.objects.count(), 2)
        
        notifications = Notification.objects.all().order_by('created_at')
        self.assertEqual(notifications[0].message, message1)
        self.assertEqual(notifications[1].message, message2)


class IntegrationTest(TestCase):
    """Integration tests for the messaging system."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
    
    def test_conversation_flow(self):
        """Test a complete conversation flow with notifications."""
        # User1 sends message to User2
        message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Hello User2!"
        )
        
        # User2 should have a notification
        self.assertEqual(self.user2.notifications.count(), 1)
        notification1 = self.user2.notifications.first()
        self.assertEqual(notification1.message, message1)
        
        # User2 replies to User1
        message2 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Hello User1! How are you?"
        )
        
        # User1 should now have a notification
        self.assertEqual(self.user1.notifications.count(), 1)
        notification2 = self.user1.notifications.first()
        self.assertEqual(notification2.message, message2)
        
        # User3 sends message to User1
        message3 = Message.objects.create(
            sender=self.user3,
            receiver=self.user1,
            content="Hey User1, this is User3!"
        )
        
        # User1 should now have 2 notifications
        self.assertEqual(self.user1.notifications.count(), 2)
        
        # Verify total counts
        self.assertEqual(Message.objects.count(), 3)
        self.assertEqual(Notification.objects.count(), 3)

