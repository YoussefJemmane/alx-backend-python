from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Message list and detail views
    path('', views.message_list, name='message_list'),
    path('message/<int:message_id>/', views.message_detail, name='message_detail'),
    
    # Message editing and history
    path('message/<int:message_id>/edit/', views.edit_message, name='edit_message'),
    path('message/<int:message_id>/history/', views.message_history, name='message_history'),
    
    # Send new message
    path('send/', views.send_message, name='send_message'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
]

