from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save, post_delete
from .models import Message, Notification, MessageHistory
from .signals import create_notification_on_message, log_message_edit, cleanup_user_data


class MessageModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com')
        
    def test_message_creation(self):
        """Test basic message creation."""
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Hello, this is a test message!"
        )
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.receiver, self.user2)
        self.assertEqual(message.content, "Hello, this is a test message!")
        self.assertFalse(message.read)
        self.assertFalse(message.edited)
        
    def test_message_str_representation(self):
        """Test string representation of message."""
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Hello, this is a test message!"
        )
        expected_str = f"Message from {self.user1.username} to {self.user2.username}: Hello, this is a test message!..."
        self.assertEqual(str(message), expected_str)
        
    def test_unread_messages_manager(self):
        """Test custom manager for unread messages."""
        # Create some messages
        msg1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Unread message 1"
        )
        msg2 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Unread message 2"
        )
        msg3 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Read message",
            read=True
        )
        
        # Test unread messages manager
        unread_messages = Message.unread.for_user(self.user2)
        self.assertEqual(unread_messages.count(), 2)
        self.assertIn(msg1, unread_messages)
        self.assertIn(msg2, unread_messages)
        self.assertNotIn(msg3, unread_messages)
        
    def test_threaded_messages(self):
        """Test threaded conversation functionality."""
        # Create parent message
        parent_msg = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Parent message"
        )
        
        # Create reply
        reply_msg = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Reply to parent",
            parent_message=parent_msg
        )
        
        # Test relationships
        self.assertEqual(reply_msg.parent_message, parent_msg)
        self.assertIn(reply_msg, parent_msg.replies.all())
        
        # Test get_all_replies method
        all_replies = parent_msg.get_all_replies()
        self.assertEqual(len(all_replies), 1)
        self.assertEqual(all_replies[0], reply_msg)


class SignalTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com')
        
    def test_notification_created_on_message_save(self):
        """Test that notification is created when a message is saved."""
        # Create message
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Test message for notification"
        )
        
        # Check that notification was created
        notifications = Notification.objects.filter(user=self.user2, message=message)
        self.assertEqual(notifications.count(), 1)
        
        notification = notifications.first()
        self.assertEqual(notification.user, self.user2)
        self.assertEqual(notification.message, message)
        self.assertIn(self.user1.username, notification.content)
        self.assertFalse(notification.read)
        
    def test_message_history_created_on_edit(self):
        """Test that message history is created when a message is edited."""
        # Create message
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Original content"
        )
        
        # Edit the message
        message.content = "Edited content"
        message.save()
        
        # Check that history was created
        history = MessageHistory.objects.filter(message=message)
        self.assertEqual(history.count(), 1)
        
        history_entry = history.first()
        self.assertEqual(history_entry.old_content, "Original content")
        self.assertTrue(message.edited)
        
    def test_user_data_cleanup_on_delete(self):
        """Test that user data is cleaned up when user is deleted."""
        # Create some data
        message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Message from user1"
        )
        message2 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Message from user2"
        )
        
        # Check notifications exist
        self.assertEqual(Notification.objects.filter(user=self.user2).count(), 1)
        self.assertEqual(Notification.objects.filter(user=self.user1).count(), 1)
        
        # Delete user1
        user1_id = self.user1.id
        self.user1.delete()
        
        # Check that messages sent by user1 are deleted
        self.assertFalse(Message.objects.filter(sender_id=user1_id).exists())
        
        # Check that messages received by user1 are deleted
        self.assertFalse(Message.objects.filter(receiver_id=user1_id).exists())
        
        # Check that notifications for user1 are deleted
        self.assertFalse(Notification.objects.filter(user_id=user1_id).exists())
        
    def test_signal_disconnection_during_test(self):
        """Test that signals can be disconnected during tests."""
        # Disconnect the signal
        post_save.disconnect(create_notification_on_message, sender=Message)
        
        try:
            # Create message
            message = Message.objects.create(
                sender=self.user1,
                receiver=self.user2,
                content="Test message without notification"
            )
            
            # Check that no notification was created
            notifications = Notification.objects.filter(user=self.user2, message=message)
            self.assertEqual(notifications.count(), 0)
            
        finally:
            # Reconnect the signal
            post_save.connect(create_notification_on_message, sender=Message)


class NotificationModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com')
        self.message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Test message"
        )
        
    def test_notification_creation(self):
        """Test basic notification creation."""
        notification = Notification.objects.create(
            user=self.user2,
            message=self.message,
            content="Test notification"
        )
        self.assertEqual(notification.user, self.user2)
        self.assertEqual(notification.message, self.message)
        self.assertEqual(notification.content, "Test notification")
        self.assertFalse(notification.read)
        
    def test_notification_str_representation(self):
        """Test string representation of notification."""
        notification = Notification.objects.create(
            user=self.user2,
            message=self.message,
            content="Test notification content"
        )
        expected_str = f"Notification for {self.user2.username}: Test notification content..."
        self.assertEqual(str(notification), expected_str)


class MessageHistoryModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com')
        self.message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Test message"
        )
        
    def test_message_history_creation(self):
        """Test basic message history creation."""
        history = MessageHistory.objects.create(
            message=self.message,
            old_content="Old content"
        )
        self.assertEqual(history.message, self.message)
        self.assertEqual(history.old_content, "Old content")
        
    def test_message_history_str_representation(self):
        """Test string representation of message history."""
        history = MessageHistory.objects.create(
            message=self.message,
            old_content="Old content for history"
        )
        expected_str = f"History for message {self.message.id}: Old content for history..."
        self.assertEqual(str(history), expected_str)
