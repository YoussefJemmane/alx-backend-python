from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Message, MessageHistory, Notification
import json
from django.views.decorators.cache import cache_page


@cache_page(60)
@login_required
def message_list(request):
    """
    Display all unread messages with edit history indicators.
    """
    unread_messages = Message.unread.unread_for_user(request.user).select_related('sender', 'receiver').only('id', 'content', 'timestamp', 'sender__username', 'receiver__username')
    
    context = {
        'messages': unread_messages,
        'user': request.user
    }
    return render(request, 'messaging/message_list.html', context)


@login_required
def message_detail(request, message_id):
    """
    Display detailed view of a message including its edit history.
    """
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user has permission to view this message
    if request.user != message.sender and request.user != message.receiver:
        messages.error(request, "You don't have permission to view this message.")
        return redirect('message_list')
    
    edit_history = message.get_edit_history()
    
    context = {
        'message': message,
        'edit_history': edit_history,
        'user': request.user
    }
    return render(request, 'messaging/message_detail.html', context)


@login_required
@require_http_methods(["POST"])
def edit_message(request, message_id):
    """
    Edit a message and track the edit history.
    """
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user has permission to edit this message
    if request.user != message.sender:
        return JsonResponse({
            'success': False, 
            'error': "You can only edit your own messages."
        }, status=403)
    
    try:
        data = json.loads(request.body)
        new_content = data.get('content', '').strip()
        edit_reason = data.get('edit_reason', '').strip()
        
        if not new_content:
            return JsonResponse({
                'success': False, 
                'error': "Message content cannot be empty."
            }, status=400)
        
        # The pre_save signal will handle creating the history record
        message.content = new_content
        message.save()
        
        # If an edit reason was provided, update the most recent history record
        if edit_reason and message.history.exists():
            latest_history = message.history.first()
            latest_history.edit_reason = edit_reason
            latest_history.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'edited': message.edited,
                'edited_at': message.edited_at.isoformat() if message.edited_at else None,
                'edit_count': message.edit_count
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': "Invalid JSON data."
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f"An error occurred: {str(e)}"
        }, status=500)


@login_required
def message_history(request, message_id):
    """
    API endpoint to get the edit history of a message.
    """
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user has permission to view this message
    if request.user != message.sender and request.user != message.receiver:
        return JsonResponse({
            'success': False, 
            'error': "You don't have permission to view this message history."
        }, status=403)
    
    history = []
    for edit in message.get_edit_history():
        history.append({
            'id': edit.id,
            'old_content': edit.old_content,
            'edited_at': edit.edited_at.isoformat(),
            'edited_by': edit.edited_by.username,
            'edit_reason': edit.edit_reason or "No reason provided"
        })
    
    return JsonResponse({
        'success': True,
        'message_id': message.id,
        'current_content': message.content,
        'edited': message.edited,
        'edit_count': message.edit_count,
        'history': history
    })


@login_required
def send_message(request):
    """
    Send a new message.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            receiver_id = data.get('receiver_id')
            content = data.get('content', '').strip()
            
            if not receiver_id or not content:
                return JsonResponse({
                    'success': False, 
                    'error': "Receiver and content are required."
                }, status=400)
            
            receiver = get_object_or_404(User, id=receiver_id)
            
            message = Message.objects.create(
                sender=request.user,
                receiver=receiver,
                content=content
            )
            
            return JsonResponse({
                'success': True,
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender': message.sender.username,
                    'receiver': message.receiver.username,
                    'timestamp': message.timestamp.isoformat()
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False, 
                'error': "Invalid JSON data."
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f"An error occurred: {str(e)}"
            }, status=500)
    
    return render(request, 'messaging/send_message.html')


@login_required
def notifications(request):
    """
    Display user notifications.
    """
    user_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'notifications': user_notifications,
        'user': request.user
    }
    return render(request, 'messaging/notifications.html', context)


@login_required
@require_http_methods(["POST"])
def delete_user(request):
    """
    Allow a user to delete their own account. This will trigger the post_delete signal for cleanup.
    """
    user = request.user
    user.delete()  # This triggers the post_delete signal
    return JsonResponse({
        'success': True,
        'message': 'Your account has been deleted.'
    })


@login_required
def message_thread(request, message_id):
    """
    Fetch all replies to a message and display them in a threaded format.
    """
    message = get_object_or_404(Message, id=message_id)
    
    # Fetch all replies recursively
    def get_replies(message):
        replies = Message.objects.filter(parent_message=message)
        return [{'message': reply, 'replies': get_replies(reply)} for reply in replies]
    
    thread = {
        'message': message,
        'replies': get_replies(message)
    }
    
    context = {
        'thread': thread,
        'user': request.user
    }
    return render(request, 'messaging/message_thread.html', context)

