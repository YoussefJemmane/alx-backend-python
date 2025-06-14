from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Message, MessageHistory, Notification
from .signals import can_edit_message, edit_message


class MessageEditTrackingTest(TestCase):
    """Test cases for message edit tracking functionality."""
    
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
    
    def test_message_creation_without_edit(self):
        """Test that a new message is created without edit fields set."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original message content"
        )
        
        self.assertFalse(message.edited)
        self.assertIsNone(message.last_edited_at)
        self.assertEqual(message.edit_count, 0)
        self.assertFalse(message.has_edit_history())
    
    def test_message_edit_creates_history(self):
        """Test that editing a message creates a history record."""
        # Create original message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original message content"
        )
        
        original_content = message.content
        
        # Edit the message
        message.content = "Edited message content"
        message.save()
        
        # Refresh from database
        message.refresh_from_db()
        
        # Check that edit fields are updated
        self.assertTrue(message.edited)
        self.assertIsNotNone(message.last_edited_at)
        self.assertEqual(message.edit_count, 1)
        self.assertTrue(message.has_edit_history())
        
        # Check that history record was created
        history_records = message.get_edit_history()
        self.assertEqual(history_records.count(), 1)
        
        history = history_records.first()
        self.assertEqual(history.old_content, original_content)
        self.assertEqual(history.edited_by, self.sender)
        self.assertEqual(history.message, message)
    
    def test_multiple_edits_create_multiple_history_records(self):
        """Test that multiple edits create multiple history records."""
        # Create original message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        # First edit
        message.content = "First edit"
        message.save()
        
        # Second edit
        message.content = "Second edit"
        message.save()
        
        # Refresh from database
        message.refresh_from_db()
        
        # Check edit count
        self.assertEqual(message.edit_count, 2)
        
        # Check history records
        history_records = message.get_edit_history()
        self.assertEqual(history_records.count(), 2)
        
        # Check that history is in correct order (most recent first)
        history_list = list(history_records)
        self.assertEqual(history_list[0].old_content, "First edit")
        self.assertEqual(history_list[1].old_content, "Original content")
    
    def test_no_history_created_for_same_content(self):
        """Test that no history is created when content doesn't change."""
        # Create original message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        # "Edit" with same content
        message.content = "Original content"
        message.save()
        
        # Refresh from database
        message.refresh_from_db()
        
        # Check that no edit was recorded
        self.assertFalse(message.edited)
        self.assertEqual(message.edit_count, 0)
        self.assertFalse(message.has_edit_history())
    
    def test_edit_notification_created(self):
        """Test that editing a message creates a notification for the receiver."""
        # Create original message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        # Clear notifications created for new message
        Notification.objects.all().delete()
        
        # Edit the message
        message.content = "Edited content"
        message.save()
        
        # Check that edit notification was created
        edit_notifications = Notification.objects.filter(
            notification_type='message_edited'
        )
        self.assertEqual(edit_notifications.count(), 1)
        
        notification = edit_notifications.first()
        self.assertEqual(notification.user, self.receiver)
        self.assertEqual(notification.message, message)
        self.assertIn('edited a message', notification.notification_text)


class MessageEditPermissionsTest(TestCase):
    """Test cases for message edit permissions and validation."""
    
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
        self.other_user = User.objects.create_user(
            username='other_user',
            email='other@example.com',
            password='testpass123'
        )
    
    def test_can_edit_own_message(self):
        """Test that a user can edit their own message."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Test message"
        )
        
        self.assertTrue(can_edit_message(message, self.sender))
    
    def test_cannot_edit_others_message(self):
        """Test that a user cannot edit someone else's message."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Test message"
        )
        
        self.assertFalse(can_edit_message(message, self.other_user))
        self.assertFalse(can_edit_message(message, self.receiver))
    
    def test_cannot_edit_old_message(self):
        """Test that old messages cannot be edited (time restriction)."""
        # Create message with old timestamp
        old_time = timezone.now() - timedelta(hours=25)  # 25 hours ago
        
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Old message"
        )
        
        # Manually set old timestamp
        Message.objects.filter(pk=message.pk).update(timestamp=old_time)
        message.refresh_from_db()
        
        self.assertFalse(can_edit_message(message, self.sender))
    
    def test_cannot_edit_message_with_max_edits(self):
        """Test that messages with maximum edits cannot be edited further."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Test message"
        )
        
        # Set edit count to maximum
        message.edit_count = 5
        message.save()
        
        self.assertFalse(can_edit_message(message, self.sender))
    
    def test_edit_message_utility_function(self):
        """Test the edit_message utility function."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        # Test successful edit
        success, error = edit_message(
            message, "New content", self.sender, "Fixed typo"
        )
        
        self.assertTrue(success)
        self.assertIsNone(error)
        
        message.refresh_from_db()
        self.assertEqual(message.content, "New content")
        self.assertTrue(message.edited)
    
    def test_edit_message_validation(self):
        """Test edit message validation."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        # Test empty content
        success, error = edit_message(message, "", self.sender)
        self.assertFalse(success)
        self.assertIn("empty", error.lower())
        
        # Test same content
        success, error = edit_message(message, "Original content", self.sender)
        self.assertFalse(success)
        self.assertIn("no changes", error.lower())
        
        # Test unauthorized user
        success, error = edit_message(message, "New content", self.other_user)
        self.assertFalse(success)
        self.assertIn("permission", error.lower())


class MessageHistoryModelTest(TestCase):
    """Test cases for the MessageHistory model."""
    
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
        
        self.message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Test message"
        )
    
    def test_message_history_creation(self):
        """Test that MessageHistory can be created successfully."""
        history = MessageHistory.objects.create(
            message=self.message,
            old_content="Old content",
            edited_by=self.sender,
            edit_reason="Fixing typo"
        )
        
        self.assertEqual(history.message, self.message)
        self.assertEqual(history.old_content, "Old content")
        self.assertEqual(history.edited_by, self.sender)
        self.assertEqual(history.edit_reason, "Fixing typo")
        self.assertIsNotNone(history.edited_at)
    
    def test_message_history_str_representation(self):
        """Test the string representation of MessageHistory."""
        history = MessageHistory.objects.create(
            message=self.message,
            old_content="Old content",
            edited_by=self.sender
        )
        
        expected_str = f"Edit of message {self.message.id} by {self.sender.username} at {history.edited_at}"
        self.assertEqual(str(history), expected_str)
    
    def test_message_history_ordering(self):
        """Test that message history is ordered by edited_at (newest first)."""
        history1 = MessageHistory.objects.create(
            message=self.message,
            old_content="First edit",
            edited_by=self.sender
        )
        
        history2 = MessageHistory.objects.create(
            message=self.message,
            old_content="Second edit",
            edited_by=self.sender
        )
        
        histories = MessageHistory.objects.all()
        self.assertEqual(histories[0], history2)  # Newest first
        self.assertEqual(histories[1], history1)


class NotificationEnhancementsTest(TestCase):
    """Test cases for enhanced notification functionality."""
    
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
    
    def test_notification_types(self):
        """Test different notification types."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Test message"
        )
        
        # Check new message notification
        new_msg_notification = Notification.objects.filter(
            notification_type='new_message'
        ).first()
        
        self.assertIsNotNone(new_msg_notification)
        self.assertEqual(new_msg_notification.notification_type, 'new_message')
        
        # Clear notifications and edit message
        Notification.objects.all().delete()
        
        message.content = "Edited content"
        message.save()
        
        # Check edit notification
        edit_notification = Notification.objects.filter(
            notification_type='message_edited'
        ).first()
        
        self.assertIsNotNone(edit_notification)
        self.assertEqual(edit_notification.notification_type, 'message_edited')


class IntegrationTest(TestCase):
    """Integration tests for the complete message edit tracking system."""
    
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
    
    def test_complete_message_lifecycle(self):
        """Test a complete message lifecycle with edits and notifications."""
        # Create initial message
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Hello, how are you?"
        )
        
        # Verify initial state
        self.assertFalse(message.edited)
        self.assertEqual(message.edit_count, 0)
        
        # Verify new message notification
        initial_notifications = Notification.objects.filter(
            notification_type='new_message'
        ).count()
        self.assertEqual(initial_notifications, 1)
        
        # Edit the message
        message.content = "Hello, how are you doing today?"
        message.save()
        
        message.refresh_from_db()
        
        # Verify edit tracking
        self.assertTrue(message.edited)
        self.assertEqual(message.edit_count, 1)
        self.assertTrue(message.has_edit_history())
        
        # Verify edit history
        history = message.get_edit_history().first()
        self.assertEqual(history.old_content, "Hello, how are you?")
        
        # Verify edit notification
        edit_notifications = Notification.objects.filter(
            notification_type='message_edited'
        ).count()
        self.assertEqual(edit_notifications, 1)
        
        # Edit again
        message.content = "Hello, how are you doing today? Hope you're well!"
        message.save()
        
        message.refresh_from_db()
        
        # Verify multiple edits
        self.assertEqual(message.edit_count, 2)
        self.assertEqual(message.get_edit_history().count(), 2)
        
        # Verify final state
        total_messages = Message.objects.count()
        total_histories = MessageHistory.objects.count()
        total_notifications = Notification.objects.count()
        
        self.assertEqual(total_messages, 1)
        self.assertEqual(total_histories, 2)
        self.assertEqual(total_notifications, 3)  # 1 new + 2 edits

