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
    
    # Analytics and statistics
    path('analytics/', views.conversation_analytics, name='conversation_analytics'),
    
    # API endpoints
    path('api/thread/<int:conversation_id>/', views.api_thread_tree, name='api_thread_tree'),
    
    # Search functionality
    path('search/', views.search_conversations, name='search_conversations'),
    
    # Demo and testing
    path('demo/recursive-queries/', views.demo_recursive_queries, name='demo_recursive_queries'),
]

