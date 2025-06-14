from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .managers import ThreadedMessageManager, UnreadMessagesManager, ReadMessagesManager


class Message(models.Model):
    """Enhanced Message model with edit tracking and threaded conversations."""
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    
    # Threading support - self-referential foreign key
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text="The message this is replying to (for threaded conversations)"
    )
    
    # Thread depth for efficient querying and display
    thread_depth = models.PositiveIntegerField(
        default=0,
        help_text="Depth in the conversation thread (0 for root messages)"
    )
    
    # Root message for quick thread identification
    root_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='thread_messages',
        help_text="The root message of this thread"
    )
    
    # New fields for edit tracking
    edited = models.BooleanField(default=False)
    last_edited_at = models.DateTimeField(null=True, blank=True)
    edit_count = models.IntegerField(default=0)
    
    # Custom managers for different types of operations
    objects = ThreadedMessageManager()  # Default manager with threading
    unread = UnreadMessagesManager()    # Manager for unread messages
    read = ReadMessagesManager()        # Manager for read messages
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['parent_message', 'timestamp']),
            models.Index(fields=['root_message', 'thread_depth', 'timestamp']),
            models.Index(fields=['sender', 'receiver', 'timestamp']),
            models.Index(fields=['thread_depth', 'timestamp']),
        ]
    
    def __str__(self):
        edited_str = " (edited)" if self.edited else ""
        return f"Message from {self.sender.username} to {self.receiver.username} at {self.timestamp}{edited_str}"
    
    def get_edit_history(self):
        """Get the edit history for this message."""
        return self.history.all().order_by('-edited_at')
    
    def has_edit_history(self):
        """Check if this message has edit history."""
        return self.history.exists()
    
    def save(self, *args, **kwargs):
        """Override save to automatically set thread_depth and root_message."""
        if self.parent_message:
            # Set thread depth one level deeper than parent
            self.thread_depth = self.parent_message.thread_depth + 1
            # Set root message to parent's root (or parent if it's a root message)
            self.root_message = self.parent_message.root_message or self.parent_message
        else:
            # This is a root message
            self.thread_depth = 0
            self.root_message = None
        
        super().save(*args, **kwargs)
        
        # If this is a root message, set root_message to self
        if not self.parent_message and not self.root_message:
            self.root_message = self
            super().save(update_fields=['root_message'])
    
    def get_all_replies(self):
        """Get all direct replies to this message."""
        return self.replies.select_related('sender', 'receiver', 'parent_message').order_by('timestamp')
    
    def get_thread_tree(self):
        """Get the entire thread tree starting from this message using optimized queries."""
        # Get the root message if this isn't one
        root = self.root_message or self
        
        # Fetch all messages in the thread with optimized queries
        thread_messages = Message.objects.filter(
            models.Q(id=root.id) | models.Q(root_message=root)
        ).select_related(
            'sender', 'receiver', 'parent_message'
        ).prefetch_related(
            'replies', 'history'
        ).order_by('thread_depth', 'timestamp')
        
        return thread_messages
    
    def get_recursive_replies(self, max_depth=None):
        """Get all replies recursively using Django ORM."""
        if max_depth is not None and self.thread_depth >= max_depth:
            return Message.objects.none()
        
        # Use recursive CTE (Common Table Expression) for PostgreSQL
        # For other databases, we'll use a Python-based recursive approach
        from django.db import connection
        
        if 'postgresql' in connection.vendor:
            return self._get_recursive_replies_postgres()
        else:
            return self._get_recursive_replies_python()
    
    def _get_recursive_replies_postgres(self):
        """Use PostgreSQL CTE for recursive queries."""
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                WITH RECURSIVE reply_tree AS (
                    -- Base case: direct replies to this message
                    SELECT id, sender_id, receiver_id, content, timestamp, 
                           parent_message_id, thread_depth, root_message_id
                    FROM django_chat_models_message 
                    WHERE parent_message_id = %s
                    
                    UNION ALL
                    
                    -- Recursive case: replies to replies
                    SELECT m.id, m.sender_id, m.receiver_id, m.content, m.timestamp,
                           m.parent_message_id, m.thread_depth, m.root_message_id
                    FROM django_chat_models_message m
                    INNER JOIN reply_tree rt ON m.parent_message_id = rt.id
                )
                SELECT * FROM reply_tree ORDER BY thread_depth, timestamp;
            """, [self.id])
            
            reply_ids = [row[0] for row in cursor.fetchall()]
        
        return Message.objects.filter(id__in=reply_ids).select_related(
            'sender', 'receiver', 'parent_message'
        ).order_by('thread_depth', 'timestamp')
    
    def _get_recursive_replies_python(self):
        """Python-based recursive reply fetching for non-PostgreSQL databases."""
        all_replies = []
        current_level = [self]
        
        while current_level:
            # Get all direct replies to messages in current level
            next_level = []
            for message in current_level:
                direct_replies = list(message.get_all_replies())
                all_replies.extend(direct_replies)
                next_level.extend(direct_replies)
            
            current_level = next_level
        
        # Return as QuerySet
        reply_ids = [reply.id for reply in all_replies]
        return Message.objects.filter(id__in=reply_ids).select_related(
            'sender', 'receiver', 'parent_message'
        ).order_by('thread_depth', 'timestamp')
    
    def get_reply_count(self):
        """Get total number of replies in this thread (recursive)."""
        return self.get_recursive_replies().count()
    
    def get_thread_participants(self):
        """Get all users who have participated in this thread."""
        thread_messages = self.get_thread_tree()
        participant_ids = set()
        
        for message in thread_messages:
            participant_ids.add(message.sender.id)
            participant_ids.add(message.receiver.id)
        
        return User.objects.filter(id__in=participant_ids)
    
    def is_root_message(self):
        """Check if this is a root message (no parent)."""
        return self.parent_message is None
    
    def get_thread_root(self):
        """Get the root message of this thread."""
        return self.root_message or self
    
    @classmethod
    def get_threaded_conversations(cls, user, limit=50):
        """Get threaded conversations for a user with optimized queries."""
        # Get root messages where user is sender or receiver
        root_messages = cls.objects.filter(
            models.Q(sender=user) | models.Q(receiver=user),
            parent_message__isnull=True  # Only root messages
        ).select_related(
            'sender', 'receiver'
        ).prefetch_related(
            'replies__sender',
            'replies__receiver',
            'thread_messages__sender',
            'thread_messages__receiver'
        ).order_by('-timestamp')[:limit]
        
        return root_messages
    
    @classmethod
    def get_conversation_with_replies(cls, conversation_id):
        """Get a specific conversation with all its replies optimized."""
        try:
            root_message = cls.objects.get(id=conversation_id, parent_message__isnull=True)
            return root_message.get_thread_tree()
        except cls.DoesNotExist:
            return cls.objects.none()


class MessageHistory(models.Model):
    """Model to store the history of message edits."""
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='history'
    )
    old_content = models.TextField(
        help_text="The content of the message before it was edited"
    )
    edited_at = models.DateTimeField(default=timezone.now)
    edited_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='message_edits'
    )
    edit_reason = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Optional reason for the edit"
    )
    
    class Meta:
        ordering = ['-edited_at']
        verbose_name = "Message History"
        verbose_name_plural = "Message Histories"
    
    def __str__(self):
        return f"Edit of message {self.message.id} by {self.edited_by.username} at {self.edited_at}"


class Notification(models.Model):
    """Model to represent notifications for users."""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    notification_text = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    # New field for notification types
    NOTIFICATION_TYPES = [
        ('new_message', 'New Message'),
        ('message_edited', 'Message Edited'),
        ('message_deleted', 'Message Deleted'),
    ]
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES, 
        default='new_message'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.notification_text}"

