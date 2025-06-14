from django.apps import AppConfig


class DjangoChatConfig(AppConfig):
    """Configuration for the Django Chat app with message edit tracking."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_chat'
    verbose_name = 'Django Chat with Edit History'
    
    def ready(self):
        """Import signal handlers when the app is ready."""
        try:
            import django_chat.signals
            print("Django Chat signals loaded successfully")
        except ImportError as e:
            print(f"Error loading Django Chat signals: {e}")

