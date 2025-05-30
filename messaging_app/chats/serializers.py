from rest_framework import serializers
from .models import User, Conversation, Message


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'bio', 'profile_picture']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        """Create and return a new user"""
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data.get('password', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            bio=validated_data.get('bio', ''),
        )
        return user


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for the Message model"""
    sender_username = serializers.ReadOnlyField(source='sender.username')
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_username', 'conversation', 'content', 'timestamp', 'is_read']
        read_only_fields = ['timestamp']


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
    
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'participants', 'messages', 'created_at', 'updated_at', 'participant_ids']
        read_only_fields = ['created_at', 'updated_at']
    
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

