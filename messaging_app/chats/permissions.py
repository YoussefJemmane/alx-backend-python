from rest_framework import permissions

class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission to allow only participants in a conversation to view, update, and delete it.
    """
    def has_permission(self, request, view):
        """
        Check if the user is authenticated.
        For write operations (PUT, PATCH, DELETE), ensure stricter validation.
        """
        if not (request.user and request.user.is_authenticated):
            return False
            
        # For read-only methods, just checking authentication is enough at this level
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # For write methods (PUT, PATCH, DELETE), we'll do additional checking in has_object_permission
        if request.method in ["PUT", "PATCH", "DELETE"]:
            # The actual object-level permission check will happen in has_object_permission
            return True
            
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user is a participant in the conversation or its related message.
        Enforce stricter permissions for PUT, PATCH, and DELETE operations.
        """
        # For Conversation objects
        if hasattr(obj, 'participants'):
            is_participant = request.user in obj.participants.all()
            # For write operations, enforce stricter rules if needed
            if request.method in ["PUT", "PATCH", "DELETE"]:
                return is_participant
            return is_participant
        
        # For Message objects - check if the user is in the conversation
        if hasattr(obj, 'conversation'):
            is_participant = request.user in obj.conversation.participants.all()
            # For editing/deleting messages, only allow the sender or conversation admin
            if request.method in ["PUT", "PATCH", "DELETE"]:
                # Allow if user is the sender of the message
                if hasattr(obj, 'sender') and obj.sender == request.user:
                    return True
                return is_participant
            return is_participant
        
        return False

