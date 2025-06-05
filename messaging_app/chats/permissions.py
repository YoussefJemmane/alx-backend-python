from rest_framework import permissions

class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission to allow only participants in a conversation to view, update, and delete it.
    """
    def has_permission(self, request, view):
        """
        Check if the user is authenticated.
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user is a participant in the conversation or its related message.
        """
        # For Conversation objects
        if hasattr(obj, 'participants'):
            return request.user in obj.participants.all()
        
        # For Message objects - check if the user is in the conversation
        if hasattr(obj, 'conversation'):
            return request.user in obj.conversation.participants.all()
        
        return False

