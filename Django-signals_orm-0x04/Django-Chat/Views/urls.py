from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # User deletion views
    path('delete-account/', views.delete_user, name='delete_user'),
    path('account-deleted/', views.account_deleted, name='account_deleted'),
    
    # API endpoints
    path('api/delete-account/', views.delete_user_api, name='delete_user_api'),
    
    # Data and statistics views
    path('deletion-stats/', views.user_deletion_stats, name='user_deletion_stats'),
    path('export-data/', views.export_user_data, name='export_user_data'),
]

