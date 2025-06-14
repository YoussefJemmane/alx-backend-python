from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Message, MessageHistory, Notification


class MessageHistoryInline(admin.TabularInline):
    """Inline admin for MessageHistory to show edit history within Message admin."""
    model = MessageHistory
    extra = 0
    readonly_fields = ['old_content', 'edited_at', 'edited_by', 'edit_reason']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False  # Don't allow manual addition of history records


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Enhanced admin configuration for Message model with edit history."""
    list_display = [
        'sender', 'receiver', 'content_preview', 'timestamp', 
        'is_read', 'edited_status', 'edit_count', 'view_history'
    ]
    list_filter = ['timestamp', 'is_read', 'edited', 'sender', 'receiver']
    search_fields = ['sender__username', 'receiver__username', 'content']
    readonly_fields = ['timestamp', 'edited', 'last_edited_at', 'edit_count']
    ordering = ['-timestamp']
    inlines = [MessageHistoryInline]
    
    fieldsets = (
        ('Message Information', {
            'fields': ('sender', 'receiver', 'content', 'is_read')
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'last_edited_at'),
            'classes': ('collapse',)
        }),
        ('Edit Tracking', {
            'fields': ('edited', 'edit_count'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Show a preview of the message content."""
        content = obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        return content
    content_preview.short_description = 'Content Preview'
    
    def edited_status(self, obj):
        """Show the edit status with visual indicators."""
        if obj.edited:
            return format_html(
                '<span style="color: orange;">✓ Edited</span>'
            )
        else:
            return format_html(
                '<span style="color: green;">Original</span>'
            )
    edited_status.short_description = 'Status'
    
    def view_history(self, obj):
        """Link to view the edit history of the message."""
        if obj.has_edit_history():
            url = reverse('admin:messaging_messagehistory_changelist')
            return format_html(
                '<a href="{}?message__id__exact={}" target="_blank">View History ({})</a>',
                url, obj.id, obj.edit_count
            )
        else:
            return "No edits"
    view_history.short_description = 'Edit History'


@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for MessageHistory model."""
    list_display = [
        'id', 'message_link', 'old_content_preview', 
        'edited_by', 'edited_at', 'edit_reason'
    ]
    list_filter = ['edited_at', 'edited_by', 'message__sender']
    search_fields = [
        'message__content', 'old_content', 'edited_by__username', 
        'message__sender__username', 'edit_reason'
    ]
    readonly_fields = ['message', 'old_content', 'edited_at', 'edited_by']
    ordering = ['-edited_at']
    
    def has_add_permission(self, request):
        return False  # Don't allow manual addition of history records
    
    def has_delete_permission(self, request, obj=None):
        return False  # Don't allow deletion of history records
    
    def message_link(self, obj):
        """Link to the related message."""
        url = reverse('admin:messaging_message_change', args=[obj.message.id])
        return format_html(
            '<a href="{}" target="_blank">Message #{}</a>',
            url, obj.message.id
        )
    message_link.short_description = 'Message'
    
    def old_content_preview(self, obj):
        """Show a preview of the old content."""
        content = obj.old_content[:100] + '...' if len(obj.old_content) > 100 else obj.old_content
        return format_html(
            '<div style="max-width: 300px; word-wrap: break-word;">{}</div>',
            content
        )
    old_content_preview.short_description = 'Old Content'


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

