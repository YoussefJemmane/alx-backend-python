from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from .views import ConversationViewSet, MessageViewSet

# Create a main router using DefaultRouter
router = DefaultRouter()

# Register the conversation viewset with the main router
router.register(r'conversations', ConversationViewSet)

# Create a nested router for messages inside conversations
conversations_router = NestedDefaultRouter(router, r'conversations', lookup='conversation')
conversations_router.register(r'messages', MessageViewSet, basename='conversation-messages')

# Register the standalone messages viewset
messages_router = DefaultRouter()
messages_router.register(r'messages', MessageViewSet, basename='message')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    path('', include(conversations_router.urls)),
    path('', include(messages_router.urls)),
]

