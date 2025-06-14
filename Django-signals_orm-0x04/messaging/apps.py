from django.apps import AppConfig


class MessagingConfig(AppConfig):
    """Configuration for the messaging app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messaging'
    
    def ready(self):
        """Import signal handlers when the app is ready."""
        import messaging.signals

