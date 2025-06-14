from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Message, MessageHistory, Notification


@receiver(pre_save, sender=Message)
def log_message_edit(sender, instance, **kwargs):
    """
    Signal handler that logs the old content of a message before it's updated.
    
    This signal is triggered before a Message instance is saved to the database.
    If the message already exists and the content has changed, it creates a
    MessageHistory record to preserve the old content.
    
    Args:
        sender: The model class (Message)
        instance: The actual instance of the Message being saved
        **kwargs: Additional keyword arguments
    """
    if instance.pk:  # Only process if this is an update (not a new message)
        try:
            # Get the original message from the database
            original_message = Message.objects.get(pk=instance.pk)
            
            # Check if the content has actually changed
            if original_message.content != instance.content:
                # Create a history record with the old content
                MessageHistory.objects.create(
                    message=instance,
                    old_content=original_message.content,
                    edited_by=instance.sender,  # Assuming sender is editing their own message
                    edited_at=timezone.now()
                )
                
                # Update the message's edit tracking fields
                instance.edited = True
                instance.last_edited_at = timezone.now()
                instance.edit_count = original_message.edit_count + 1
                
                print(f"Message edit logged: Message {instance.pk} edited by {instance.sender.username}")
                
        except Message.DoesNotExist:
            # This shouldn't happen, but handle gracefully
            print(f"Warning: Could not find original message with pk {instance.pk}")


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Signal handler that creates notifications for new messages and message edits.
    
    Args:
        sender: The model class (Message)
        instance: The actual instance of the Message that was saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        # Create notification for new message
        notification_text = f"You have a new message from {instance.sender.username}"
        
        Notification.objects.create(
            user=instance.receiver,
            message=instance,
            notification_text=notification_text,
            notification_type='new_message'
        )
        
        print(f"New message notification created for {instance.receiver.username}")
        
    elif instance.edited:
        # Create notification for message edit (only notify receiver if different from sender)
        if instance.receiver != instance.sender:
            notification_text = f"{instance.sender.username} edited a message they sent to you"
            
            Notification.objects.create(
                user=instance.receiver,
                message=instance,
                notification_text=notification_text,
                notification_type='message_edited'
            )
            
            print(f"Message edit notification created for {instance.receiver.username}")


@receiver(post_save, sender=MessageHistory)
def log_message_history_creation(sender, instance, created, **kwargs):
    """
    Signal handler that logs when a message history record is created.
    
    This is useful for debugging and auditing purposes.
    
    Args:
        sender: The model class (MessageHistory)
        instance: The actual instance of the MessageHistory that was saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        print(f"Message history record created: Message {instance.message.pk} - Edit #{instance.message.edit_count}")
        print(f"Old content preview: {instance.old_content[:50]}...")


# Additional utility functions for message editing
def can_edit_message(message, user):
    """
    Utility function to check if a user can edit a message.
    
    Args:
        message: The Message instance
        user: The User instance
        
    Returns:
        bool: True if the user can edit the message, False otherwise
    """
    # Only the sender can edit their own messages
    if message.sender != user:
        return False
    
    # Optional: Add time-based restrictions
    # For example, only allow editing within 24 hours
    from datetime import timedelta
    time_limit = timezone.now() - timedelta(hours=24)
    if message.timestamp < time_limit:
        return False
    
    # Optional: Limit number of edits
    if message.edit_count >= 5:  # Maximum 5 edits per message
        return False
    
    return True


def edit_message(message, new_content, user, edit_reason=None):
    """
    Utility function to safely edit a message with proper validation.
    
    Args:
        message: The Message instance to edit
        new_content: The new content for the message
        user: The User performing the edit
        edit_reason: Optional reason for the edit
        
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    # Check if user can edit this message
    if not can_edit_message(message, user):
        return False, "You don't have permission to edit this message"
    
    # Validate new content
    if not new_content or not new_content.strip():
        return False, "Message content cannot be empty"
    
    if new_content == message.content:
        return False, "No changes detected in message content"
    
    # Store the edit reason in a temporary attribute
    # This will be picked up by the pre_save signal
    if edit_reason:
        message._edit_reason = edit_reason
    
    # Update the message content
    message.content = new_content
    message.save()
    
    return True, None

