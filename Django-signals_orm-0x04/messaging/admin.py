from django.contrib import admin
from .models import Message, Notification


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin configuration for Message model."""
    list_display = ['sender', 'receiver', 'content_preview', 'timestamp', 'is_read']
    list_filter = ['timestamp', 'is_read', 'sender', 'receiver']
    search_fields = ['sender__username', 'receiver__username', 'content']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def content_preview(self, obj):
        """Show a preview of the message content."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin configuration for Notification model."""
    list_display = ['user', 'notification_text', 'message_sender', 'created_at', 'is_read']
    list_filter = ['created_at', 'is_read', 'user']
    search_fields = ['user__username', 'notification_text', 'message__sender__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def message_sender(self, obj):
        """Show the sender of the related message."""
        return obj.message.sender.username
    message_sender.short_description = 'Message Sender'

