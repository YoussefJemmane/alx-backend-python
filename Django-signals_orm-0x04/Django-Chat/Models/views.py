from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Message, MessageHistory, Notification
from .managers import ConversationTreeBuilder, ThreadAnalytics
import json


@login_required
def threaded_conversations_list(request):
    """
    Display a list of threaded conversations for the current user.
    Uses optimized queries with prefetch_related and select_related.
    """
    # Get threaded conversations using optimized manager method
    conversations = Message.objects.recent_conversations(request.user, limit=50)
    
    # Paginate results
    paginator = Paginator(conversations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get conversation statistics
    stats = Message.objects.get_conversation_stats(request.user)
    
    context = {
        'conversations': page_obj,
        'stats': stats,
        'user': request.user
    }
    
    return render(request, 'models/threaded_conversations_list.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """
    Display a specific threaded conversation with all replies.
    Uses recursive queries and optimized prefetching.
    """
    # Get the conversation with optimized threading
    thread_messages = Message.objects.get_thread_tree_optimized(conversation_id)
    
    if not thread_messages.exists():
        messages.error(request, "Conversation not found.")
        return redirect('models:threaded_conversations_list')
    
    # Check if user has permission to view this conversation
    user_can_view = thread_messages.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).exists()
    
    if not user_can_view:
        messages.error(request, "You don't have permission to view this conversation.")
        return redirect('models:threaded_conversations_list')
    
    # Build the conversation tree for efficient display
    tree_builder = ConversationTreeBuilder(thread_messages)
    root_message = thread_messages.filter(parent_message__isnull=True).first()
    
    if root_message:
        conversation_tree = tree_builder.get_tree_structure(root_message.id)
        flattened_thread = tree_builder.get_flattened_thread(root_message.id)
    else:
        conversation_tree = []
        flattened_thread = []
    
    # Get thread analytics
    thread_stats = ThreadAnalytics.get_thread_engagement_stats(conversation_id)
    
    context = {
        'root_message': root_message,
        'thread_messages': thread_messages,
        'conversation_tree': conversation_tree,
        'flattened_thread': flattened_thread,
        'thread_stats': thread_stats,
        'user': request.user
    }
    
    return render(request, 'models/conversation_detail.html', context)


@login_required
@require_http_methods(["POST"])
def create_reply(request, parent_message_id):
    """
    Create a reply to an existing message.
    """
    parent_message = get_object_or_404(Message, id=parent_message_id)
    
    # Check if user can reply to this message
    if request.user != parent_message.sender and request.user != parent_message.receiver:
        return JsonResponse({
            'success': False,
            'error': 'You can only reply to messages you are involved in.'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({
                'success': False,
                'error': 'Reply content cannot be empty.'
            }, status=400)
        
        # Determine receiver (the other person in the conversation)
        receiver = parent_message.sender if request.user == parent_message.receiver else parent_message.receiver
        
        # Create reply using the manager method
        reply = Message.objects.create_reply(
            parent_message=parent_message,
            sender=request.user,
            receiver=receiver,
            content=content
        )
        
        return JsonResponse({
            'success': True,
            'reply': {
                'id': reply.id,
                'content': reply.content,
                'sender': reply.sender.username,
                'receiver': reply.receiver.username,
                'timestamp': reply.timestamp.isoformat(),
                'thread_depth': reply.thread_depth,
                'parent_message_id': reply.parent_message_id
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
def start_new_conversation(request):
    """
    Start a new threaded conversation.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            receiver_id = data.get('receiver_id')
            content = data.get('content', '').strip()
            
            if not receiver_id or not content:
                return JsonResponse({
                    'success': False,
                    'error': 'Receiver and content are required.'
                }, status=400)
            
            receiver = get_object_or_404(User, id=receiver_id)
            
            # Create root message (no parent)
            conversation = Message.objects.create(
                sender=request.user,
                receiver=receiver,
                content=content
                # parent_message=None (default)
            )
            
            return JsonResponse({
                'success': True,
                'conversation': {
                    'id': conversation.id,
                    'content': conversation.content,
                    'sender': conversation.sender.username,
                    'receiver': conversation.receiver.username,
                    'timestamp': conversation.timestamp.isoformat(),
                    'is_root': conversation.is_root_message()
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'An error occurred: {str(e)}'
            }, status=500)
    
    # GET request - show form
    users = User.objects.exclude(id=request.user.id).order_by('username')
    
    context = {
        'users': users,
        'user': request.user
    }
    
    return render(request, 'models/start_conversation.html', context)


@login_required
def conversation_analytics(request):
    """
    Display analytics and statistics for threaded conversations.
    """
    # Get most active threads
    active_threads = ThreadAnalytics.get_most_active_threads(request.user)
    
    # Get user conversation statistics
    user_stats = Message.objects.get_conversation_stats(request.user)
    
    # Get recent activity
    recent_messages = Message.objects.for_user(request.user).with_threading_data()[:20]
    
    context = {
        'active_threads': active_threads,
        'user_stats': user_stats,
        'recent_messages': recent_messages,
        'user': request.user
    }
    
    return render(request, 'models/conversation_analytics.html', context)


@login_required
def api_thread_tree(request, conversation_id):
    """
    API endpoint to get the full thread tree structure as JSON.
    """
    try:
        # Get optimized thread tree
        thread_messages = Message.objects.get_thread_tree_optimized(conversation_id)
        
        if not thread_messages.exists():
            return JsonResponse({
                'success': False,
                'error': 'Conversation not found.'
            }, status=404)
        
        # Check permissions
        user_can_view = thread_messages.filter(
            Q(sender=request.user) | Q(receiver=request.user)
        ).exists()
        
        if not user_can_view:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied.'
            }, status=403)
        
        # Build tree structure
        tree_builder = ConversationTreeBuilder(thread_messages)
        root_message = thread_messages.filter(parent_message__isnull=True).first()
        
        if root_message:
            tree_structure = tree_builder.get_tree_structure(root_message.id)
            
            def serialize_tree_node(node):
                message = node['message']
                return {
                    'id': message.id,
                    'content': message.content,
                    'sender': {
                        'id': message.sender.id,
                        'username': message.sender.username
                    },
                    'receiver': {
                        'id': message.receiver.id,
                        'username': message.receiver.username
                    },
                    'timestamp': message.timestamp.isoformat(),
                    'thread_depth': message.thread_depth,
                    'edited': message.edited,
                    'edit_count': message.edit_count,
                    'children': [serialize_tree_node(child) for child in node['children']]
                }
            
            serialized_tree = serialize_tree_node(tree_structure)
        else:
            serialized_tree = {}
        
        # Get thread statistics
        thread_stats = ThreadAnalytics.get_thread_engagement_stats(conversation_id)
        
        return JsonResponse({
            'success': True,
            'conversation_id': conversation_id,
            'tree': serialized_tree,
            'stats': thread_stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
def search_conversations(request):
    """
    Search within threaded conversations.
    """
    query = request.GET.get('q', '').strip()
    
    if query:
        # Use optimized search method
        search_results = Message.objects.search_in_threads(query, request.user)
        
        # Group results by thread
        threads = {}
        for message in search_results:
            root = message.get_thread_root()
            if root.id not in threads:
                threads[root.id] = {
                    'root': root,
                    'matches': []
                }
            threads[root.id]['matches'].append(message)
    else:
        threads = {}
    
    context = {
        'query': query,
        'threads': threads.values(),
        'user': request.user
    }
    
    return render(request, 'models/search_conversations.html', context)


@login_required
def unread_messages_inbox(request):
    """
    Display the user's inbox with only unread messages.
    Uses the custom UnreadMessagesManager with .only() optimization.
    """
    # Get unread messages using the custom manager with optimized fields
    unread_messages = Message.unread.optimized_inbox(request.user, limit=50)
    
    # Get unread summary statistics
    unread_summary = Message.unread.get_unread_summary(request.user)
    
    # Get unread count by sender for sidebar display
    unread_by_sender = Message.unread.unread_count_by_sender(request.user)
    
    # Paginate results
    paginator = Paginator(unread_messages, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'unread_messages': page_obj,
        'unread_summary': unread_summary,
        'unread_by_sender': unread_by_sender,
        'user': request.user
    }
    
    return render(request, 'models/unread_messages_inbox.html', context)


@login_required
@require_http_methods(["POST"])
def mark_messages_as_read(request):
    """
    Mark specific messages as read via AJAX.
    """
    try:
        data = json.loads(request.body)
        message_ids = data.get('message_ids', [])
        
        if not message_ids:
            return JsonResponse({
                'success': False,
                'error': 'No message IDs provided.'
            }, status=400)
        
        # Use the custom manager to mark messages as read
        updated_count = Message.unread.mark_as_read(request.user, message_ids)
        
        return JsonResponse({
            'success': True,
            'marked_read': updated_count,
            'message': f'{updated_count} messages marked as read.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def mark_all_from_sender_as_read(request):
    """
    Mark all unread messages from a specific sender as read.
    """
    try:
        data = json.loads(request.body)
        sender_id = data.get('sender_id')
        
        if not sender_id:
            return JsonResponse({
                'success': False,
                'error': 'Sender ID is required.'
            }, status=400)
        
        sender = get_object_or_404(User, id=sender_id)
        
        # Use the custom manager to mark all messages from sender as read
        updated_count = Message.unread.batch_mark_read_by_sender(request.user, sender)
        
        return JsonResponse({
            'success': True,
            'marked_read': updated_count,
            'sender': sender.username,
            'message': f'{updated_count} messages from {sender.username} marked as read.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
def unread_messages_by_thread(request):
    """
    Display unread messages organized by conversation threads.
    """
    # Get unread messages organized by thread using custom manager
    unread_threads = Message.unread.unread_threads(request.user)
    
    # Group messages by thread for better display
    threads = {}
    for message in unread_threads:
        root_id = message.root_message.id if message.root_message else message.id
        if root_id not in threads:
            threads[root_id] = {
                'root': message.root_message or message,
                'unread_messages': []
            }
        threads[root_id]['unread_messages'].append(message)
    
    context = {
        'threads': threads.values(),
        'user': request.user
    }
    
    return render(request, 'models/unread_messages_by_thread.html', context)


@login_required
def recent_unread_messages(request):
    """
    Display recent unread messages (last 24 hours).
    """
    hours = int(request.GET.get('hours', 24))
    
    # Get recent unread messages using custom manager
    recent_unread = Message.unread.recent_unread(request.user, hours=hours)
    
    context = {
        'recent_unread': recent_unread,
        'hours': hours,
        'user': request.user
    }
    
    return render(request, 'models/recent_unread_messages.html', context)


@login_required
def demo_recursive_queries(request):
    """
    Demonstration view showing various recursive query techniques.
    """
    # Get a sample conversation for demonstration
    sample_conversation = Message.objects.root_messages_only().for_user(request.user).first()
    
    demo_data = {}
    
    if sample_conversation:
        # Demonstrate different recursive query methods
        demo_data.update({
            'root_message': sample_conversation,
            'direct_replies': sample_conversation.get_all_replies(),
            'recursive_replies': sample_conversation.get_recursive_replies(),
            'full_thread_tree': sample_conversation.get_thread_tree(),
            'thread_participants': sample_conversation.get_thread_participants(),
            'reply_count': sample_conversation.get_reply_count(),
        })
        
        # Build tree structure for visualization
        tree_builder = ConversationTreeBuilder(sample_conversation.get_thread_tree())
        demo_data['tree_structure'] = tree_builder.get_tree_structure(sample_conversation.id)
        demo_data['flattened_thread'] = tree_builder.get_flattened_thread(sample_conversation.id)
    
    context = {
        'demo_data': demo_data,
        'user': request.user
    }
    
    return render(request, 'models/demo_recursive_queries.html', context)

