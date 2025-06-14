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
                instance.edited_at = timezone.now()
                instance.edited_by = instance.sender
                instance.last_edited_at = timezone.now()
                instance.edit_count = original_message.edit_count + 1
                
                print(f"Message edit logged: Message {instance.pk} edited by {instance.sender.username}")
                
        except Message.DoesNotExist:
            # This shouldn't happen, but handle gracefully
            print(f"Warning: Could not find original message with pk {instance.pk}")


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Signal handler that creates a notification when a new message is created.
    
    Args:
        sender: The model class (Message)
        instance: The actual instance of the Message that was saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        # Create notification for the receiver
        notification_text = f"You have a new message from {instance.sender.username}"
        
        Notification.objects.create(
            user=instance.receiver,
            message=instance,
            notification_text=notification_text
        )
        
        print(f"Notification created for {instance.receiver.username} about message from {instance.sender.username}")


@receiver(post_save, sender=User)
def user_created_notification(sender, instance, created, **kwargs):
    """
    Optional signal handler for when a new user is created.
    This can be used for welcome notifications or other user-related notifications.
    
    Args:
        sender: The model class (User)
        instance: The actual instance of the User that was saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        print(f"New user created: {instance.username}")
        # You can add additional logic here if needed for user creation notifications

