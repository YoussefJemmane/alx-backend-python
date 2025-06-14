from django.urls import path
from . import views

app_name = 'chats'

urlpatterns = [
    path('', views.conversation_list, name='conversation_list'),
    path('conversation/<int:user_id>/', views.conversation_detail, name='conversation_detail'),
    path('unread/', views.unread_messages, name='unread_messages'),
    path('message/<int:message_id>/history/', views.message_history, name='message_history'),
    path('notifications/', views.notifications, name='notifications'),
    path('send/', views.send_message, name='send_message'),
    path('delete-account/', views.delete_user_account, name='delete_account'),
    path('cache-test/', views.cache_test_view, name='cache_test'),
]

