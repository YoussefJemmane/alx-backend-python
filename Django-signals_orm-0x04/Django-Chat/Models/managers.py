from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q, Count, Prefetch, F, Max, Min
from django.utils import timezone
from datetime import timedelta


class ThreadedMessageQuerySet(models.QuerySet):
    """Custom QuerySet for optimized threaded message operations."""
    
    def with_threading_data(self):
        """Annotate queryset with threading-related data."""
        return self.select_related(
            'sender', 'receiver', 'parent_message', 'root_message'
        ).prefetch_related(
            'replies__sender',
            'replies__receiver',
            'history'
        )
    
    def root_messages_only(self):
        """Filter to only root messages (no parent)."""
        return self.filter(parent_message__isnull=True)
    
    def replies_only(self):
        """Filter to only reply messages (have parent)."""
        return self.filter(parent_message__isnull=False)
    
    def by_thread_depth(self, max_depth=None):
        """Filter by thread depth."""
        qs = self.order_by('thread_depth', 'timestamp')
        if max_depth is not None:
            qs = qs.filter(thread_depth__lte=max_depth)
        return qs
    
    def for_user(self, user):
        """Get messages involving a specific user."""
        return self.filter(Q(sender=user) | Q(receiver=user))
    
    def with_reply_counts(self):
        """Annotate with reply counts."""
        return self.annotate(
            direct_reply_count=Count('replies'),
            total_thread_count=Count('thread_messages')
        )
    
    def optimized_thread_tree(self, root_message):
        """Get optimized thread tree for a root message."""
        return self.filter(
            Q(id=root_message.id) | Q(root_message=root_message)
        ).select_related(
            'sender', 'receiver', 'parent_message'
        ).prefetch_related(
            Prefetch(
                'replies',
                queryset=self.model.objects.select_related('sender', 'receiver')
            ),
            'history__edited_by'
        ).order_by('thread_depth', 'timestamp')
    
    def recent_conversations(self, user, days=30, limit=50):
        """Get recent conversations for a user."""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        return self.root_messages_only().for_user(user).filter(
            timestamp__gte=cutoff_date
        ).with_threading_data().with_reply_counts().order_by(
            '-timestamp'
        )[:limit]
    
    def search_in_threads(self, query, user=None):
        """Search for messages within threads."""
        qs = self.filter(content__icontains=query)
        if user:
            qs = qs.for_user(user)
        return qs.with_threading_data().order_by('-timestamp')


class ThreadedMessageManager(models.Manager):
    """Custom manager for threaded message operations."""
    
    def get_queryset(self):
        return ThreadedMessageQuerySet(self.model, using=self._db)
    
    def with_threading_data(self):
        return self.get_queryset().with_threading_data()
    
    def root_messages_only(self):
        return self.get_queryset().root_messages_only()
    
    def replies_only(self):
        return self.get_queryset().replies_only()
    
    def for_user(self, user):
        return self.get_queryset().for_user(user)
    
    def recent_conversations(self, user, days=30, limit=50):
        return self.get_queryset().recent_conversations(user, days, limit)
    
    def get_thread_tree_optimized(self, root_message_id):
        """Get an optimized thread tree for a root message."""
        try:
            root_message = self.get(id=root_message_id, parent_message__isnull=True)
            return self.get_queryset().optimized_thread_tree(root_message)
        except self.model.DoesNotExist:
            return self.none()
    
    def create_reply(self, parent_message, sender, receiver, content):
        """Create a reply to an existing message."""
        return self.create(
            parent_message=parent_message,
            sender=sender,
            receiver=receiver,
            content=content
        )
    
    def get_conversation_stats(self, user, days=30):
        """Get conversation statistics for a user."""
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count, Q
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        stats = self.for_user(user).filter(timestamp__gte=cutoff_date).aggregate(
            total_messages=Count('id'),
            root_messages=Count('id', filter=Q(parent_message__isnull=True)),
            replies=Count('id', filter=Q(parent_message__isnull=False)),
            total_threads=Count('root_message', distinct=True)
        )
        
        return stats
    
    def bulk_create_threaded_messages(self, messages_data):
        """Bulk create messages with proper threading setup."""
        messages = []
        for data in messages_data:
            message = self.model(**data)
            # Set threading fields before bulk create
            if message.parent_message:
                message.thread_depth = message.parent_message.thread_depth + 1
                message.root_message = (
                    message.parent_message.root_message or message.parent_message
                )
            else:
                message.thread_depth = 0
                message.root_message = None
            messages.append(message)
        
        created_messages = self.bulk_create(messages)
        
        # Update root_message for root messages
        root_message_updates = []
        for message in created_messages:
            if not message.parent_message and not message.root_message:
                message.root_message = message
                root_message_updates.append(message)
        
        if root_message_updates:
            self.bulk_update(root_message_updates, ['root_message'])
        
        return created_messages


class ConversationTreeBuilder:
    """Helper class for building conversation trees efficiently."""
    
    def __init__(self, messages_queryset):
        self.messages = list(messages_queryset)
        self.message_dict = {msg.id: msg for msg in self.messages}
        self.children_dict = {}
        self._build_children_dict()
    
    def _build_children_dict(self):
        """Build a dictionary mapping parent IDs to their children."""
        for message in self.messages:
            parent_id = message.parent_message_id
            if parent_id not in self.children_dict:
                self.children_dict[parent_id] = []
            if parent_id:  # Skip root messages (parent_id is None)
                self.children_dict[parent_id].append(message)
    
    def get_tree_structure(self, root_message_id=None):
        """Get the tree structure starting from a root message."""
        if root_message_id:
            root_message = self.message_dict.get(root_message_id)
            if not root_message:
                return []
            return self._build_tree_recursive(root_message)
        else:
            # Return all root messages with their trees
            root_messages = [msg for msg in self.messages if not msg.parent_message_id]
            return [self._build_tree_recursive(msg) for msg in root_messages]
    
    def _build_tree_recursive(self, message):
        """Recursively build tree structure for a message."""
        children = self.children_dict.get(message.id, [])
        return {
            'message': message,
            'children': [self._build_tree_recursive(child) for child in children]
        }
    
    def get_flattened_thread(self, root_message_id):
        """Get a flattened list of messages in thread order."""
        tree = self.get_tree_structure(root_message_id)
        if not tree:
            return []
        
        def flatten_recursive(node, depth=0):
            result = [(node['message'], depth)]
            for child in node['children']:
                result.extend(flatten_recursive(child, depth + 1))
            return result
        
        return flatten_recursive(tree[0]) if tree else []


class UnreadMessagesQuerySet(models.QuerySet):
    """Custom QuerySet for unread message operations with field optimization."""
    
    def unread_for_user(self, user):
        """Filter messages that are unread for a specific user."""
        return self.filter(
            receiver=user,
            is_read=False
        )
    
    def optimized_unread(self, user):
        """Get unread messages with optimized field selection."""
        return self.unread_for_user(user).only(
            'id', 'sender', 'content', 'timestamp', 
            'is_read', 'thread_depth', 'parent_message'
        ).select_related(
            'sender'  # Only sender info needed for inbox display
        ).order_by('-timestamp')
    
    def inbox_optimized(self, user):
        """Optimized query for inbox display with minimal fields."""
        return self.unread_for_user(user).only(
            'id', 'sender__username', 'content', 'timestamp',
            'thread_depth', 'parent_message__id'
        ).select_related(
            'sender', 'parent_message'
        ).order_by('-timestamp')
    
    def unread_by_sender(self, user, sender):
        """Get unread messages from a specific sender."""
        return self.filter(
            receiver=user,
            sender=sender,
            is_read=False
        ).only(
            'id', 'content', 'timestamp', 'thread_depth'
        ).order_by('-timestamp')
    
    def unread_count_by_sender(self, user):
        """Get count of unread messages grouped by sender."""
        return self.unread_for_user(user).values(
            'sender__id', 'sender__username'
        ).annotate(
            unread_count=Count('id'),
            latest_message=Max('timestamp')
        ).order_by('-latest_message')
    
    def unread_threads(self, user):
        """Get unread messages organized by thread."""
        return self.unread_for_user(user).select_related(
            'sender', 'root_message'
        ).only(
            'id', 'sender__username', 'content', 'timestamp',
            'thread_depth', 'root_message__id', 'parent_message__id'
        ).order_by('root_message__id', 'thread_depth', 'timestamp')
    
    def recent_unread(self, user, hours=24):
        """Get unread messages from the last N hours."""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        return self.unread_for_user(user).filter(
            timestamp__gte=cutoff_time
        ).only(
            'id', 'sender__username', 'content', 'timestamp'
        ).select_related('sender').order_by('-timestamp')
    
    def priority_unread(self, user, priority_senders=None):
        """Get unread messages with priority senders first."""
        qs = self.unread_for_user(user)
        
        if priority_senders:
            # Annotate with priority flag
            from django.db.models import Case, When, BooleanField
            qs = qs.annotate(
                is_priority=Case(
                    When(sender__in=priority_senders, then=True),
                    default=False,
                    output_field=BooleanField()
                )
            ).order_by('-is_priority', '-timestamp')
        
        return qs.only(
            'id', 'sender__username', 'content', 'timestamp', 'thread_depth'
        ).select_related('sender')
    
    def mark_as_read_bulk(self, user, message_ids=None):
        """Bulk mark messages as read for a user."""
        qs = self.unread_for_user(user)
        if message_ids:
            qs = qs.filter(id__in=message_ids)
        return qs.update(is_read=True)
    
    def unread_summary(self, user):
        """Get summary statistics for unread messages."""
        unread_qs = self.unread_for_user(user)
        
        summary = unread_qs.aggregate(
            total_unread=Count('id'),
            oldest_unread=Min('timestamp'),
            newest_unread=Max('timestamp'),
            unique_senders=Count('sender', distinct=True)
        )
        
        # Add thread information
        summary['unread_threads'] = unread_qs.values(
            'root_message'
        ).distinct().count()
        
        return summary


class UnreadMessagesManager(models.Manager):
    """Custom manager for filtering and optimizing unread message queries."""
    
    def get_queryset(self):
        return UnreadMessagesQuerySet(self.model, using=self._db)
    
    def for_user(self, user):
        """Get all unread messages for a specific user."""
        return self.get_queryset().unread_for_user(user)
    
    def optimized_inbox(self, user, limit=50):
        """Get optimized unread messages for inbox display."""
        return self.get_queryset().inbox_optimized(user)[:limit]
    
    def recent_unread(self, user, hours=24):
        """Get recent unread messages."""
        return self.get_queryset().recent_unread(user, hours)
    
    def unread_by_sender(self, user, sender):
        """Get unread messages from a specific sender."""
        return self.get_queryset().unread_by_sender(user, sender)
    
    def unread_count_by_sender(self, user):
        """Get unread message counts grouped by sender."""
        return self.get_queryset().unread_count_by_sender(user)
    
    def unread_threads(self, user):
        """Get unread messages organized by thread."""
        return self.get_queryset().unread_threads(user)
    
    def priority_unread(self, user, priority_senders=None):
        """Get unread messages with priority sorting."""
        return self.get_queryset().priority_unread(user, priority_senders)
    
    def mark_as_read(self, user, message_ids=None):
        """Mark messages as read for a user."""
        return self.get_queryset().mark_as_read_bulk(user, message_ids)
    
    def get_unread_summary(self, user):
        """Get comprehensive unread message summary."""
        return self.get_queryset().unread_summary(user)
    
    def has_unread(self, user):
        """Check if user has any unread messages (optimized)."""
        return self.get_queryset().unread_for_user(user).exists()
    
    def unread_count(self, user):
        """Get total count of unread messages for user."""
        return self.get_queryset().unread_for_user(user).count()
    
    def latest_unread(self, user, count=5):
        """Get the latest N unread messages with minimal fields."""
        return self.get_queryset().unread_for_user(user).only(
            'id', 'sender__username', 'content', 'timestamp'
        ).select_related('sender').order_by('-timestamp')[:count]
    
    def unread_from_conversation(self, user, root_message_id):
        """Get unread messages from a specific conversation thread."""
        return self.get_queryset().filter(
            Q(id=root_message_id) | Q(root_message_id=root_message_id),
            receiver=user,
            is_read=False
        ).only(
            'id', 'sender__username', 'content', 'timestamp', 'thread_depth'
        ).select_related('sender').order_by('thread_depth', 'timestamp')
    
    def batch_mark_read_by_sender(self, user, sender):
        """Mark all unread messages from a specific sender as read."""
        return self.get_queryset().filter(
            receiver=user,
            sender=sender,
            is_read=False
        ).update(is_read=True)
    
    def auto_mark_old_as_read(self, user, days=30):
        """Auto-mark old unread messages as read (cleanup function)."""
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.get_queryset().filter(
            receiver=user,
            is_read=False,
            timestamp__lt=cutoff_date
        ).update(is_read=True)


class ReadMessagesManager(models.Manager):
    """Companion manager for read messages (for completeness)."""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_read=True)
    
    def for_user(self, user):
        """Get all read messages for a user."""
        return self.get_queryset().filter(
            Q(sender=user) | Q(receiver=user)
        )
    
    def recently_read(self, user, hours=24):
        """Get recently read messages."""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        return self.for_user(user).filter(
            # For received messages, we want recently read ones
            # For sent messages, we want recently sent ones
            Q(receiver=user) | Q(sender=user, timestamp__gte=cutoff_time)
        ).only(
            'id', 'sender__username', 'receiver__username', 
            'content', 'timestamp'
        ).select_related('sender', 'receiver').order_by('-timestamp')


class MessageReadStatusManager:
    """Utility class for managing message read status operations."""
    
    @staticmethod
    def mark_conversation_as_read(user, root_message_id):
        """Mark all messages in a conversation thread as read for a user."""
        from .models import Message
        
        return Message.objects.filter(
            Q(id=root_message_id) | Q(root_message_id=root_message_id),
            receiver=user,
            is_read=False
        ).update(is_read=True)
    
    @staticmethod
    def get_read_statistics(user):
        """Get comprehensive read/unread statistics for a user."""
        from .models import Message
        
        received_stats = Message.objects.filter(receiver=user).aggregate(
            total_received=Count('id'),
            read_count=Count('id', filter=Q(is_read=True)),
            unread_count=Count('id', filter=Q(is_read=False)),
            latest_received=Max('timestamp')
        )
        
        sent_stats = Message.objects.filter(sender=user).aggregate(
            total_sent=Count('id'),
            latest_sent=Max('timestamp')
        )
        
        return {
            'received': received_stats,
            'sent': sent_stats,
            'read_percentage': (
                received_stats['read_count'] / received_stats['total_received'] * 100
                if received_stats['total_received'] > 0 else 0
            )
        }
    
    @staticmethod
    def bulk_mark_as_read(user, message_ids):
        """Bulk mark specific messages as read."""
        from .models import Message
        
        return Message.objects.filter(
            id__in=message_ids,
            receiver=user,
            is_read=False
        ).update(is_read=True)
    
    @staticmethod
    def auto_read_policy(user, auto_read_after_hours=72):
        """Implement auto-read policy for old messages."""
        from .models import Message
        
        cutoff_time = timezone.now() - timedelta(hours=auto_read_after_hours)
        return Message.objects.filter(
            receiver=user,
            is_read=False,
            timestamp__lt=cutoff_time
        ).update(is_read=True)


class ThreadAnalytics:
    """Analytics helper for threaded conversations."""
    
    @staticmethod
    def get_most_active_threads(user, limit=10, days=30):
        """Get most active threads for a user."""
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Import here to avoid circular imports
        from .models import Message
        
        return Message.objects.root_messages_only().for_user(user).filter(
            timestamp__gte=cutoff_date
        ).annotate(
            reply_count=Count('thread_messages')
        ).order_by('-reply_count')[:limit]
    
    @staticmethod
    def get_thread_engagement_stats(thread_root_id):
        """Get engagement statistics for a specific thread."""
        from django.db.models import Count, Q
        from .models import Message
        
        try:
            root_message = Message.objects.get(id=thread_root_id, parent_message__isnull=True)
            thread_messages = root_message.get_thread_tree()
            
            stats = {
                'total_messages': thread_messages.count(),
                'unique_participants': len(set(
                    list(thread_messages.values_list('sender_id', flat=True)) +
                    list(thread_messages.values_list('receiver_id', flat=True))
                )),
                'max_depth': thread_messages.aggregate(
                    max_depth=models.Max('thread_depth')
                )['max_depth'] or 0,
                'last_activity': thread_messages.aggregate(
                    last_activity=models.Max('timestamp')
                )['last_activity'],
                'edited_messages': thread_messages.filter(edited=True).count()
            }
            
            return stats
        except Message.DoesNotExist:
            return None

