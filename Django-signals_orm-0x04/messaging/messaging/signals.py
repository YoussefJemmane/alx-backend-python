from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Message, Notification, MessageHistory


@receiver(post_save, sender=Message)
def create_notification_on_message(sender, instance, created, **kwargs):
    """Create a notification when a new message is created."""
    if created:
        # Create notification for the receiver
        notification_content = f"You have a new message from {instance.sender.username}: {instance.content[:50]}..."
        Notification.objects.create(
            user=instance.receiver,
            message=instance,
            content=notification_content
        )


@receiver(pre_save, sender=Message)
def log_message_edit(sender, instance, **kwargs):
    """Log message content before it's edited."""
    if instance.pk:  # Only for existing instances (updates)
        try:
            # Get the old version of the message
            old_message = Message.objects.get(pk=instance.pk)
            # Check if content has changed
            if old_message.content != instance.content:
                # Save the old content to history
                MessageHistory.objects.create(
                    message=old_message,
                    old_content=old_message.content
                )
                # Mark the message as edited
                instance.edited = True
        except Message.DoesNotExist:
            # Handle case where message doesn't exist (shouldn't happen normally)
            pass


@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """Clean up user-related data when a user is deleted."""
    # Delete all messages sent by the user
    Message.objects.filter(sender=instance).delete()
    
    # Delete all messages received by the user
    Message.objects.filter(receiver=instance).delete()
    
    # Delete all notifications for the user
    Notification.objects.filter(user=instance).delete()
    
    # Note: MessageHistory will be automatically deleted due to CASCADE
    # relationship with Message

