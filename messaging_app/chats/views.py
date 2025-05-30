from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Conversation, Message
from .serializers import UserSerializer, ConversationSerializer, MessageSerializer

# Create your views here.
class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing conversations
    """
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']
    
    def get_queryset(self):
        """
        This view should return a list of all conversations
        for the currently authenticated user.
        """
        user = self.request.user
        return Conversation.objects.filter(participants=user)
    
    def perform_create(self, serializer):
        """
        Create a new conversation and automatically add the current user
        as a participant
        """
        conversation = serializer.save()
        conversation.participants.add(self.request.user)
        
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """
        Add a participant to the conversation
        """
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'User ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user = User.objects.get(pk=user_id)
            conversation.participants.add(user)
            return Response({'status': 'participant added'})
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """
        Send a message to this conversation
        """
        conversation = self.get_object()
        content = request.data.get('content')
        
        if not content:
            return Response(
                {'error': 'Message content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        message = Message.objects.create(
            sender=request.user,
            conversation=conversation,
            content=content
        )
        
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing messages
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        This view should return a list of all messages
        for the conversation specified in the URL.
        """
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            return Message.objects.filter(conversation_id=conversation_id)
        return Message.objects.none()
    
    def perform_create(self, serializer):
        """
        Create a new message with the sender set to the current user
        """
        serializer.save(sender=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """
        Return all unread messages for the current user
        """
        user = request.user
        conversations = user.conversations.all()
        unread_messages = Message.objects.filter(
            conversation__in=conversations, 
            is_read=False
        ).exclude(sender=user)
        
        serializer = self.get_serializer(unread_messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark a message as read
        """
        message = self.get_object()
        message.is_read = True
        message.save()
        return Response({'status': 'message marked as read'})
