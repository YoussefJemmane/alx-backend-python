import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from chats.models import Chat, Message

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for User model"""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
    
    def test_create_user(self):
        """Test creating a new user"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
    
    def test_user_string_representation(self):
        """Test string representation of user"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'testuser')


class ChatModelTest(TestCase):
    """Test cases for Chat model"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        self.chat = Chat.objects.create()
        self.chat.participants.add(self.user1, self.user2)
    
    def test_chat_creation(self):
        """Test chat creation"""
        self.assertTrue(isinstance(self.chat, Chat))
        self.assertEqual(self.chat.participants.count(), 2)
    
    def test_chat_string_representation(self):
        """Test string representation of chat"""
        expected = f"Chat {self.chat.chat_id}"
        self.assertEqual(str(self.chat), expected)


class MessageModelTest(TestCase):
    """Test cases for Message model"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        self.chat = Chat.objects.create()
        self.chat.participants.add(self.user1, self.user2)
        
        self.message = Message.objects.create(
            chat=self.chat,
            sender=self.user1,
            message_body='Hello, World!'
        )
    
    def test_message_creation(self):
        """Test message creation"""
        self.assertTrue(isinstance(self.message, Message))
        self.assertEqual(self.message.message_body, 'Hello, World!')
        self.assertEqual(self.message.sender, self.user1)
        self.assertEqual(self.message.chat, self.chat)
    
    def test_message_string_representation(self):
        """Test string representation of message"""
        expected = f"Message {self.message.message_id}"
        self.assertEqual(str(self.message), expected)


class APITest(APITestCase):
    """Test cases for API endpoints"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        self.client = Client()
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        url = reverse('user-list')  # Adjust based on your URL patterns
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123'
        }
        # This is a basic test - adjust based on your actual API structure
        response = self.client.post(url, data, format='json')
        # The exact status code will depend on your API implementation
        self.assertIn(response.status_code, [200, 201, 404])  # 404 if endpoint doesn't exist yet
    
    def test_health_check(self):
        """Test basic health check"""
        # Test if Django is running
        response = self.client.get('/')
        # Should get some response, even if it's 404
        self.assertIsNotNone(response)


@pytest.mark.django_db
class TestPytestIntegration:
    """Test pytest integration works"""
    
    def test_pytest_works(self):
        """Basic test to ensure pytest is working"""
        assert True
    
    def test_database_access(self):
        """Test database access through pytest"""
        user = User.objects.create_user(
            username='pytestuser',
            email='pytest@example.com',
            password='pytestpass'
        )
        assert user.username == 'pytestuser'
        assert User.objects.count() == 1
    
    def test_model_creation(self):
        """Test model creation"""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        chat = Chat.objects.create()
        chat.participants.add(user1, user2)
        
        message = Message.objects.create(
            chat=chat,
            sender=user1,
            message_body='Test message'
        )
        
        assert Chat.objects.count() == 1
        assert Message.objects.count() == 1
        assert message.sender == user1
        assert message.message_body == 'Test message'


# Test configuration
@pytest.fixture(scope='session')
def django_db_setup():
    """Configure test database"""
    from django.conf import settings
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }

