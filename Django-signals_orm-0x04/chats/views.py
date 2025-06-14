from django.views.decorators.cache import cache_page

@cache_page(60)
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