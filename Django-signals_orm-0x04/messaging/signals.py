from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Message, Notification


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

