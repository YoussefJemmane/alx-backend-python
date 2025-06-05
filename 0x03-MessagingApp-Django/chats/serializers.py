from rest_framework import serializers
from .models import User, Conversation, Message


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model"""
    # Add CharField for full name display
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    # Add SerializerMethodField for user status or other computed properties
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'bio', 'profile_picture', 'full_name', 'status']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def get_status(self, obj):
        """Return the user's status"""
        # This is just an example of using SerializerMethodField
        return "online" if hasattr(obj, 'is_online') and obj.is_online else "offline"
    
    def create(self, validated_data):
        """Create and return a new user"""
        # Validate that email is unique
        email = validated_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
            
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data.get('password', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            bio=validated_data.get('bio', ''),
        )
        return user
        
    def validate_username(self, value):
        """Validate username to ensure it's valid"""
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        return value


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for the Message model"""
    sender_username = serializers.ReadOnlyField(source='sender.username')
    # Add a CharField for message preview
    message_preview = serializers.CharField(source='message_body', read_only=True)
    # Add a SerializerMethodField for time since sent
    time_since_sent = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_username', 'conversation', 'message_body', 'sent_at', 'is_read', 'message_preview', 'time_since_sent']
        read_only_fields = ['sent_at']
    
    def get_time_since_sent(self, obj):
        """Get the time elapsed since the message was sent"""
        from django.utils import timezone
        from datetime import datetime
        
        if not obj.sent_at:
            return "Unknown"
            
        now = timezone.now()
        time_diff = now - obj.sent_at
        
        if time_diff.days > 0:
            return f"{time_diff.days} days ago"
        elif time_diff.seconds >= 3600:
            return f"{time_diff.seconds // 3600} hours ago"
        elif time_diff.seconds >= 60:
            return f"{time_diff.seconds // 60} minutes ago"
        else:
            return "Just now"
            
    def validate_message_body(self, value):
        """Validate that message content is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty.")
        return value


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for the Conversation model"""
    participants = UserSerializer(many=True, read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    participant_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        many=True,
        required=False
    )
    # Add a SerializerMethodField for conversation summary
    conversation_summary = serializers.SerializerMethodField()
    # Add a CharField for conversation title
    display_title = serializers.CharField(source='title', read_only=True)
    # Add a SerializerMethodField for unread message count
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'display_title', 'participants', 'messages', 'created_at', 'updated_at', 'participant_ids', 'conversation_summary', 'unread_count']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_conversation_summary(self, obj):
        """Return a summary of the conversation"""
        latest_message = obj.messages.order_by('-sent_at').first()
        if not latest_message:
            return "No messages yet"
        return f"Latest: {latest_message.message_body[:30]}..." if len(latest_message.message_body) > 30 else latest_message.message_body
    
    def get_unread_count(self, obj):
        """Return count of unread messages for the current user"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
    
    def validate(self, data):
        """Validate the conversation data"""
        # Ensure there are at least 2 participants
        participant_ids = data.get('participant_ids', [])
        if len(participant_ids) < 1:  # At least 1 other participant (current user is added automatically)
            raise serializers.ValidationError({"participant_ids": "A conversation must have at least one participant."})
        return data
    
    def create(self, validated_data):
        """Create a new conversation with participants"""
        participant_ids = validated_data.pop('participant_ids', [])
        conversation = Conversation.objects.create(**validated_data)
        
        # Add participants to the conversation
        for user in participant_ids:
            conversation.participants.add(user)
        
        return conversation
    
    def update(self, instance, validated_data):
        """Update a conversation, handling participant changes"""
        participant_ids = validated_data.pop('participant_ids', None)
        
        # Update the conversation fields
        instance = super().update(instance, validated_data)
        
        # Update participants if provided
        if participant_ids is not None:
            instance.participants.clear()
            for user in participant_ids:
                instance.participants.add(user)
        
        return instance

