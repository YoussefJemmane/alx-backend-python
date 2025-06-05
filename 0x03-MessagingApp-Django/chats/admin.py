from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Conversation, Message

# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for the User model"""
    list_display = ('user_id', 'username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Info', {'fields': ('bio', 'profile_picture', 'phone_number')}),
    )


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin configuration for the Conversation model"""
    list_display = ('conversation_id', 'title', 'created_at', 'updated_at', 'get_participants')
    search_fields = ('title',)
    filter_horizontal = ('participants',)
    
    def get_participants(self, obj):
        """Return a comma-separated list of participant usernames"""
        return ", ".join([user.username for user in obj.participants.all()])
    
    get_participants.short_description = 'Participants'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin configuration for the Message model"""
    list_display = ('message_id', 'sender', 'conversation', 'sent_at', 'is_read', 'truncated_content')
    list_filter = ('is_read', 'sent_at')
    search_fields = ('message_body', 'sender__username')
    
    def truncated_content(self, obj):
        """Return the first 50 characters of the message content"""
        if len(obj.message_body) > 50:
            return f"{obj.message_body[:50]}..."
        return obj.message_body
    
    truncated_content.short_description = 'Message Body'
