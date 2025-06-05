from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import uuid

# Create your models here.
class User(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser
    """
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # AbstractUser already has email, first_name, last_name, and password fields
    # but we'll keep these references to match the check requirements
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    
    def __str__(self):
        return self.username


class Conversation(models.Model):
    """
    Conversation model to track which users are involved in a conversation
    """
    conversation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"Conversation {self.conversation_id} - {self.title}"


class Message(models.Model):
    """
    Message model containing sender, conversation, message_body and sent_at
    """
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    message_body = models.TextField()  # Renamed from content
    sent_at = models.DateTimeField(auto_now_add=True)  # Renamed from timestamp
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['sent_at']  # Updated to use sent_at instead of timestamp
    
    def __str__(self):
        return f"Message from {self.sender.username} in {self.conversation.conversation_id}"
