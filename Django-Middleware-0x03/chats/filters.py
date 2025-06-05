import django_filters
from .models import Message, Conversation

class MessageFilter(django_filters.FilterSet):
    """
    Filter for Message model
    """
    # Add datetime range filtering
    sent_after = django_filters.DateTimeFilter(field_name='sent_at', lookup_expr='gte')
    sent_before = django_filters.DateTimeFilter(field_name='sent_at', lookup_expr='lte')
    
    # Add sender filtering by username
    sender_username = django_filters.CharFilter(field_name='sender__username', lookup_expr='icontains')
    
    # Filter by read status
    is_read = django_filters.BooleanFilter(field_name='is_read')
    
    # Search in message body
    content = django_filters.CharFilter(field_name='message_body', lookup_expr='icontains')
    
    class Meta:
        model = Message
        fields = ['sender', 'conversation', 'sent_at', 'is_read', 'sender_username', 'content', 'sent_after', 'sent_before']


class ConversationFilter(django_filters.FilterSet):
    """
    Filter for Conversation model
    """
    # Filter by participant
    participant = django_filters.ModelChoiceFilter(field_name='participants', queryset=lambda request: request.user.__class__.objects.all())
    
    # Filter by creation date range
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Filter by title
    title_contains = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    
    class Meta:
        model = Conversation
        fields = ['participants', 'created_at', 'updated_at', 'title']

