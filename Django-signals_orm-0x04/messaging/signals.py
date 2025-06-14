from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
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


@receiver(post_delete, sender=User)
def cleanup_user_related_data(sender, instance, **kwargs):
    """
    Signal handler that cleans up all user-related data when a user is deleted.
    
    This signal is triggered after a User instance is deleted from the database.
    It handles the cleanup of all related data including messages, notifications,
    and message history records that may not be automatically deleted due to
    foreign key constraints.
    
    Note: Most of the cleanup happens automatically due to CASCADE relationships
    in the models, but this signal provides additional logging and can handle
    any custom cleanup logic that might be needed.
    
    Args:
        sender: The model class (User)
        instance: The actual instance of the User that was deleted
        **kwargs: Additional keyword arguments
    """
    import logging
    logger = logging.getLogger(__name__)
    
    username = instance.username
    user_id = instance.id
    
    try:
        # Log the deletion event
        logger.info(f"Post-delete signal triggered for user: {username} (ID: {user_id})")
        
        # Explicitly delete related data
        Message.objects.filter(sender=instance).delete()
        Message.objects.filter(receiver=instance).delete()
        Notification.objects.filter(user=instance).delete()
        MessageHistory.objects.filter(edited_by=instance).delete()
        
        # Note: Due to the CASCADE relationships defined in the models,
        # the following data should already be automatically deleted:
        # - All sent messages (Message.sender -> CASCADE)
        # - All received messages (Message.receiver -> CASCADE) 
        # - All notifications (Notification.user -> CASCADE)
        # - All message edit history (MessageHistory.edited_by -> CASCADE)
        # - All messages edited by the user (Message.edited_by -> SET_NULL)
        
        # However, we can still perform some additional cleanup or logging:
        
        # Count how much data was cleaned up (this will be 0 due to CASCADE, but good for logging)
        try:
            # These queries will return empty results since CASCADE has already deleted the data,
            # but we keep them for logging purposes and potential future use
            remaining_sent_messages = Message.objects.filter(sender=instance).count()
            remaining_received_messages = Message.objects.filter(receiver=instance).count()
            remaining_notifications = Notification.objects.filter(user=instance).count()
            remaining_edit_history = MessageHistory.objects.filter(edited_by=instance).count()
            
            if remaining_sent_messages > 0 or remaining_received_messages > 0 or remaining_notifications > 0 or remaining_edit_history > 0:
                logger.warning(
                    f"Unexpected remaining data for deleted user {username}: "
                    f"Messages: {remaining_sent_messages + remaining_received_messages}, "
                    f"Notifications: {remaining_notifications}, "
                    f"Edit History: {remaining_edit_history}"
                )
            else:
                logger.info(f"All related data successfully cleaned up for user {username}")
                
        except Exception as count_error:
            logger.error(f"Error counting remaining data for user {username}: {str(count_error)}")
        
        # Additional custom cleanup logic can be added here
        # For example, cleaning up files, external service accounts, etc.
        
        # Log successful completion
        logger.info(f"User deletion cleanup completed successfully for: {username} (ID: {user_id})")
        print(f"User deletion cleanup completed for: {username}")
        
    except Exception as e:
        logger.error(f"Error in user deletion cleanup for {username}: {str(e)}")
        print(f"Error in user deletion cleanup for {username}: {str(e)}")
        # Don't re-raise the exception as it would interfere with the deletion process


@receiver(post_delete, sender=Message)
def cleanup_message_related_data(sender, instance, **kwargs):
    """
    Signal handler that performs additional cleanup when a message is deleted.
    
    This can be useful for cleaning up any additional resources or logging
    message deletions for audit purposes.
    
    Args:
        sender: The model class (Message)
        instance: The actual instance of the Message that was deleted
        **kwargs: Additional keyword arguments
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        message_id = instance.id
        sender_username = instance.sender.username if instance.sender else 'Unknown'
        receiver_username = instance.receiver.username if instance.receiver else 'Unknown'
        
        # Log the message deletion
        logger.info(
            f"Message deleted: ID {message_id} from {sender_username} to {receiver_username}"
        )
        
        # Note: MessageHistory and Notification records related to this message
        # are automatically deleted due to CASCADE relationships
        
        print(f"Message cleanup completed for message ID: {message_id}")
        
    except Exception as e:
        logger.error(f"Error in message deletion cleanup: {str(e)}")
        print(f"Error in message deletion cleanup: {str(e)}")        


@receiver(post_delete, sender=MessageHistory)
def log_message_history_deletion(sender, instance, **kwargs):
    """
    Signal handler that logs when a message history record is deleted.
    
    This is useful for audit trails and debugging.
    
    Args:
        sender: The model class (MessageHistory)
        instance: The actual instance of the MessageHistory that was deleted
        **kwargs: Additional keyword arguments
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        history_id = instance.id
        message_id = instance.message.id if instance.message else 'Unknown'
        editor_username = instance.edited_by.username if instance.edited_by else 'Unknown'
        
        logger.info(
            f"Message history deleted: ID {history_id} for message {message_id} edited by {editor_username}"
        )
        
    except Exception as e:
        logger.error(f"Error logging message history deletion: {str(e)}")        


@receiver(post_delete, sender=Notification)
def log_notification_deletion(sender, instance, **kwargs):
    """
    Signal handler that logs when a notification is deleted.
    
    This is useful for audit trails and debugging.
    
    Args:
        sender: The model class (Notification)
        instance: The actual instance of the Notification that was deleted
        **kwargs: Additional keyword arguments
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        notification_id = instance.id
        user_username = instance.user.username if instance.user else 'Unknown'
        notification_text = instance.notification_text
        
        logger.info(
            f"Notification deleted: ID {notification_id} for user {user_username}: '{notification_text}'"
        )
        
    except Exception as e:
        logger.error(f"Error logging notification deletion: {str(e)}")

