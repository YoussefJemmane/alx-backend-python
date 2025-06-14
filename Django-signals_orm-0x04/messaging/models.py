from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Message(models.Model):
    """Enhanced Message model with edit tracking."""
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
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    # New fields for edit tracking
    edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    edited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='edited_messages'
    )
    last_edited_at = models.DateTimeField(null=True, blank=True)
    edit_count = models.IntegerField(default=0)
    
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    read = models.BooleanField(default=False)
    
    objects = models.Manager()
    unread = UnreadMessagesManager()
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        edited_str = " (edited)" if self.edited else ""
        return f"Message from {self.sender.username} to {self.receiver.username} at {self.timestamp}{edited_str}"
    
    def get_edit_history(self):
        """Get the edit history for this message."""
        return self.history.all().order_by('-edited_at')
    
    def has_edit_history(self):
        """Check if this message has edit history."""
        return self.history.exists()


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
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.notification_text}"

