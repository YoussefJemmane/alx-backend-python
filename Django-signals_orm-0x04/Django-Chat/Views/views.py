from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.exceptions import PermissionDenied
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST"])
def delete_user(request):
    """
    View to handle user account deletion.
    
    GET: Display confirmation page
    POST: Process the deletion request
    
    This view allows users to delete their own accounts. The deletion process
    will trigger a post_delete signal that cleans up all related data.
    """
    if request.method == 'GET':
        # Display confirmation page
        context = {
            'user': request.user,
            'message_count': request.user.sent_messages.count() + request.user.received_messages.count(),
            'notification_count': request.user.notifications.count(),
            'edit_history_count': request.user.message_edits.count(),
        }
        return render(request, 'chat/delete_user_confirm.html', context)
    
    elif request.method == 'POST':
        try:
            # Get the confirmation from the form
            confirmation = request.POST.get('confirmation', '').strip().lower()
            expected_confirmation = f"delete {request.user.username}".lower()
            
            if confirmation != expected_confirmation:
                messages.error(
                    request, 
                    f'Please type "delete {request.user.username}" to confirm account deletion.'
                )
                return redirect('chat:delete_user')
            
            # Store user info for success message
            username = request.user.username
            user_id = request.user.id
            
            logger.info(f"User {username} (ID: {user_id}) initiated account deletion")
            
            # Use transaction to ensure data consistency during deletion
            with transaction.atomic():
                # Get the user instance
                user_to_delete = request.user
                
                # Log out the user before deletion
                logout(request)
                
                # Delete the user account
                # This will trigger the post_delete signal which will clean up related data
                user_to_delete.delete()
                
                logger.info(f"User {username} (ID: {user_id}) account successfully deleted")
            
            # Success message and redirect
            messages.success(
                request, 
                f'Account "{username}" has been successfully deleted. All associated data has been removed.'
            )
            return redirect('chat:account_deleted')
            
        except Exception as e:
            logger.error(f"Error during user deletion for {request.user.username}: {str(e)}")
            messages.error(
                request, 
                'An error occurred while deleting your account. Please try again or contact support.'
            )
            return redirect('chat:delete_user')


@require_http_methods(["GET"])
def account_deleted(request):
    """
    Success page displayed after account deletion.
    """
    return render(request, 'chat/account_deleted.html')


@login_required
@require_http_methods(["POST"])
def delete_user_api(request):
    """
    API endpoint for user account deletion (JSON response).
    
    This provides a programmatic way to delete user accounts,
    useful for mobile apps or AJAX requests.
    """
    try:
        data = json.loads(request.body)
        confirmation = data.get('confirmation', '').strip().lower()
        expected_confirmation = f"delete {request.user.username}".lower()
        
        if confirmation != expected_confirmation:
            return JsonResponse({
                'success': False,
                'error': f'Please provide "delete {request.user.username}" as confirmation.',
                'required_confirmation': f'delete {request.user.username}'
            }, status=400)
        
        # Store user info for response
        username = request.user.username
        user_id = request.user.id
        
        # Get statistics before deletion
        stats = {
            'messages_deleted': request.user.sent_messages.count() + request.user.received_messages.count(),
            'notifications_deleted': request.user.notifications.count(),
            'edit_history_deleted': request.user.message_edits.count(),
        }
        
        logger.info(f"API: User {username} (ID: {user_id}) initiated account deletion")
        
        # Use transaction for data consistency
        with transaction.atomic():
            user_to_delete = request.user
            
            # Delete the user account (triggers post_delete signal)
            user_to_delete.delete()
            
            logger.info(f"API: User {username} (ID: {user_id}) account successfully deleted")
        
        return JsonResponse({
            'success': True,
            'message': f'Account "{username}" has been successfully deleted.',
            'deleted_data': stats
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data provided.'
        }, status=400)
    except Exception as e:
        logger.error(f"API: Error during user deletion for {request.user.username}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while deleting your account. Please try again.'
        }, status=500)


@login_required
def user_deletion_stats(request):
    """
    View to show statistics about data that will be deleted if user deletes their account.
    """
    user = request.user
    
    # Calculate statistics
    sent_messages = user.sent_messages.count()
    received_messages = user.received_messages.count()
    total_messages = sent_messages + received_messages
    
    notifications = user.notifications.count()
    edit_history = user.message_edits.count()
    
    # Messages where user is mentioned in edit history
    edited_messages = user.edited_messages.count()
    
    context = {
        'user': user,
        'stats': {
            'sent_messages': sent_messages,
            'received_messages': received_messages,
            'total_messages': total_messages,
            'notifications': notifications,
            'edit_history': edit_history,
            'edited_messages': edited_messages,
        }
    }
    
    return render(request, 'chat/user_deletion_stats.html', context)


@login_required
def export_user_data(request):
    """
    View to export user data before deletion (optional functionality).
    
    This allows users to download their data before deleting their account,
    which is useful for GDPR compliance.
    """
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    user = request.user
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{user.username}_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write user information
    writer.writerow(['User Data Export'])
    writer.writerow(['Generated:', datetime.now().isoformat()])
    writer.writerow([])
    
    writer.writerow(['User Information'])
    writer.writerow(['Username', 'Email', 'First Name', 'Last Name', 'Date Joined', 'Last Login'])
    writer.writerow([
        user.username,
        user.email,
        user.first_name,
        user.last_name,
        user.date_joined.isoformat() if user.date_joined else '',
        user.last_login.isoformat() if user.last_login else ''
    ])
    writer.writerow([])
    
    # Write sent messages
    writer.writerow(['Sent Messages'])
    writer.writerow(['To', 'Content', 'Timestamp', 'Is Read', 'Edited', 'Edit Count'])
    for message in user.sent_messages.all():
        writer.writerow([
            message.receiver.username,
            message.content,
            message.timestamp.isoformat(),
            message.is_read,
            message.edited,
            message.edit_count
        ])
    writer.writerow([])
    
    # Write received messages
    writer.writerow(['Received Messages'])
    writer.writerow(['From', 'Content', 'Timestamp', 'Is Read', 'Edited', 'Edit Count'])
    for message in user.received_messages.all():
        writer.writerow([
            message.sender.username,
            message.content,
            message.timestamp.isoformat(),
            message.is_read,
            message.edited,
            message.edit_count
        ])
    writer.writerow([])
    
    # Write notifications
    writer.writerow(['Notifications'])
    writer.writerow(['Text', 'Is Read', 'Created At', 'Related Message ID'])
    for notification in user.notifications.all():
        writer.writerow([
            notification.notification_text,
            notification.is_read,
            notification.created_at.isoformat(),
            notification.message.id if notification.message else ''
        ])
    
    return response

