from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.contrib.auth.models import User
from messaging.models import Message, Notification
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from django.utils import timezone


@cache_page(60)  # Cache for 60 seconds
@login_required
def conversation_list(request):
    """Display a cached list of messages in conversations."""
    # Get all messages for the current user with optimized queries
    messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('sender', 'receiver', 'parent_message').prefetch_related(
        Prefetch('replies', queryset=Message.objects.select_related('sender', 'receiver'))
    ).order_by('-timestamp')
    
    # Paginate the results
    paginator = Paginator(messages, 20)  # Show 20 messages per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'messages': page_obj,
        'user': request.user,
    }
    
    return render(request, 'chats/conversation_list.html', context)


@login_required
def conversation_detail(request, user_id):
    """Display conversation between current user and specified user."""
    other_user = get_object_or_404(User, id=user_id)
    
    # Get messages between the two users with threading support
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).select_related('sender', 'receiver', 'parent_message').prefetch_related(
        'replies__sender', 'replies__receiver'
    ).order_by('timestamp')
    
    # Mark messages as read
    unread_messages = messages.filter(receiver=request.user, read=False)
    unread_messages.update(read=True)
    
    context = {
        'messages': messages,
        'other_user': other_user,
        'current_user': request.user,
    }
    
    return render(request, 'chats/conversation_detail.html', context)


@login_required
def unread_messages(request):
    """Display unread messages using custom manager."""
    # Use the custom manager to get unread messages
    unread_msgs = Message.unread.for_user(request.user)
    
    context = {
        'unread_messages': unread_msgs,
    }
    
    return render(request, 'chats/unread_messages.html', context)


@login_required
def message_history(request, message_id):
    """Display edit history for a message."""
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user has permission to view this message
    if message.sender != request.user and message.receiver != request.user:
        return HttpResponse("Unauthorized", status=403)
    
    # Get message history
    history = message.history.all().order_by('-edited_at')
    
    context = {
        'message': message,
        'history': history,
    }
    
    return render(request, 'chats/message_history.html', context)


@login_required
def notifications(request):
    """Display notifications for the current user."""
    user_notifications = Notification.objects.filter(
        user=request.user
    ).select_related('message__sender').order_by('-timestamp')
    
    # Paginate notifications
    paginator = Paginator(user_notifications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
    }
    
    return render(request, 'chats/notifications.html', context)


@login_required
def send_message(request):
    """Send a message to another user."""
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_id')
        content = request.POST.get('content')
        parent_message_id = request.POST.get('parent_message_id')
        
        if not receiver_id or not content:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        try:
            receiver = User.objects.get(id=receiver_id)
            
            # Create the message
            message_data = {
                'sender': request.user,
                'receiver': receiver,
                'content': content.strip(),
            }
            
            # Add parent message if this is a reply
            if parent_message_id:
                try:
                    parent_message = Message.objects.get(id=parent_message_id)
                    message_data['parent_message'] = parent_message
                except Message.DoesNotExist:
                    pass
            
            message = Message.objects.create(**message_data)
            
            # Invalidate cache for conversation list
            cache.delete('views.decorators.cache.cache_page')
            
            return JsonResponse({
                'success': True,
                'message_id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
            })
            
        except User.DoesNotExist:
            return JsonResponse({'error': 'Receiver not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def delete_user_account(request):
    """Delete user account and all related data."""
    if request.method == 'POST':
        # Confirmation check
        confirm = request.POST.get('confirm')
        if confirm == 'DELETE':
            user = request.user
            # The post_delete signal will handle cleanup
            user.delete()
            return JsonResponse({'success': True, 'message': 'Account deleted successfully'})
        else:
            return JsonResponse({'error': 'Confirmation required'}, status=400)
    
    return render(request, 'chats/delete_account.html')


def cache_test_view(request):
    """Test view to demonstrate caching functionality."""
    # Try to get data from cache
    cached_data = cache.get('test_data')
    
    if cached_data is None:
        # Data not in cache, generate it
        cached_data = {
            'timestamp': timezone.now().isoformat(),
            'message': 'This data was generated and cached',
            'cache_hit': False
        }
        # Store in cache for 5 minutes
        cache.set('test_data', cached_data, 300)
    else:
        cached_data['cache_hit'] = True
    
    return JsonResponse(cached_data)
