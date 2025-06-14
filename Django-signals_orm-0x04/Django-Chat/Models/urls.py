from django.urls import path
from . import views

app_name = 'models'

urlpatterns = [
    # Threaded conversations
    path('', views.threaded_conversations_list, name='threaded_conversations_list'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('start/', views.start_new_conversation, name='start_new_conversation'),
    
    # Reply functionality
    path('reply/<int:parent_message_id>/', views.create_reply, name='create_reply'),
    
    # Unread messages functionality (Custom ORM Manager demonstration)
    path('inbox/', views.unread_messages_inbox, name='unread_messages_inbox'),
    path('inbox/threads/', views.unread_messages_by_thread, name='unread_messages_by_thread'),
    path('inbox/recent/', views.recent_unread_messages, name='recent_unread_messages'),
    
    # Message read status API endpoints
    path('api/mark-read/', views.mark_messages_as_read, name='mark_messages_as_read'),
    path('api/mark-sender-read/', views.mark_all_from_sender_as_read, name='mark_all_from_sender_as_read'),
    
    # Analytics and statistics
    path('analytics/', views.conversation_analytics, name='conversation_analytics'),
    
    # API endpoints
    path('api/thread/<int:conversation_id>/', views.api_thread_tree, name='api_thread_tree'),
    
    # Search functionality
    path('search/', views.search_conversations, name='search_conversations'),
    
    # Demo and testing
    path('demo/recursive-queries/', views.demo_recursive_queries, name='demo_recursive_queries'),
]

