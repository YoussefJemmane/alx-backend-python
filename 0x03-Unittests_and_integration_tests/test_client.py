#!/usr/bin/env python3
"""
Unit tests for client module
"""
import unittest
from unittest.mock import patch, PropertyMock
import requests
from parameterized import parameterized, parameterized_class
from client import GithubOrgClient
from fixtures import TEST_PAYLOAD


class TestGithubOrgClient(unittest.TestCase):
    """
    Tests for GithubOrgClient class
    """

    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    @patch('client.get_json')
    def test_org(self, org_name, mock_get_json):
        """Test that GithubOrgClient.org returns the correct value"""
        # Create a test instance with the given org name
        client = GithubOrgClient(org_name)
        # Configure the mock to return a test payload
        test_payload = {"name": org_name}
        mock_get_json.return_value = test_payload
        # Call the method under test
        result = client.org
        # Assert that get_json was called once with the expected URL
        expected_url = GithubOrgClient.ORG_URL.format(org=org_name)
        mock_get_json.assert_called_once_with(expected_url)
        # Assert that the result equals the test payload
        self.assertEqual(result, test_payload)

    def test_public_repos_url(self):
        """Test that the result of _public_repos_url is the expected one
        based on the mocked payload"""
        # Expected repos_url value
        repos_url = "https://api.github.com/orgs/test-org/repos"
        # Create a test instance
        client = GithubOrgClient("test-org")
        # Mock the org property to return a known payload with repos_url
        with patch.object(GithubOrgClient, 'org',
                          new_callable=PropertyMock,
                          return_value={"repos_url": repos_url}) as mock_org:
            # Call the property under test
            result = client._public_repos_url
            # Assert that the result is the expected URL
            self.assertEqual(result, repos_url)
            # Verify that org property was called
            mock_org.assert_called_once()

    @patch('client.get_json')
    def test_public_repos(self, mock_get_json):
        """Test that public_repos returns the expected list of repos"""
        # Define test repo names and their JSON representations
        test_repos = [
            {"name": "repo1"},
            {"name": "repo2"},
            {"name": "repo3"}
        ]
        expected_repos = ["repo1", "repo2", "repo3"]
        # Configure mock_get_json to return the test repos
        mock_get_json.return_value = test_repos
        # Create test instance
        client = GithubOrgClient("test-org")
        # Mock _public_repos_url to return a test URL
        test_url = "https://api.github.com/orgs/test-org/repos"
        with patch.object(GithubOrgClient, '_public_repos_url',
                          new_callable=PropertyMock,
                          return_value=test_url) as mock_public_repos_url:
            # Call the method under test
            result = client.public_repos()
            # Assert the result is as expected
            self.assertEqual(result, expected_repos)
            # Assert both mocks were called once
            mock_public_repos_url.assert_called_once()
            mock_get_json.assert_called_once_with(test_url)

    @parameterized.expand([
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False),
    ])
    def test_has_license(self, repo, license_key, expected):
        """Test that has_license returns the correct value"""
        # Call the method under test
        result = GithubOrgClient.has_license(repo, license_key)
        # Assert the result is as expected
        self.assertEqual(result, expected)


@parameterized_class(
    ('org_payload', 'repos_payload', 'expected_repos', 'apache2_repos'),
    TEST_PAYLOAD
)
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """Integration tests for GithubOrgClient"""

    @classmethod
    def setUpClass(cls):
        """Set up for the integration tests
        Mock requests.get to return appropriate test payloads based on URL
        """
        # Store original requests.get
        cls.get_patcher = patch('requests.get')
        cls.mock_get = cls.get_patcher.start()

        # Define side effect function to return different responses based on
        # URL
        def side_effect(url):
            """Return mock response based on URL"""
            mock_response = unittest.mock.Mock()
            # URL for organization info
            if url.endswith('/google'):  # org URL
                mock_response.json.return_value = cls.org_payload
            # URL for repos
            elif url.endswith('/repos'):  # repos URL
                mock_response.json.return_value = cls.repos_payload
            return mock_response
        # Configure mock to use side_effect
        cls.mock_get.side_effect = side_effect

    @classmethod
    def tearDownClass(cls):
        """Tear down the integration tests
        Stop the requests.get patcher
        """
        cls.get_patcher.stop()

    def test_public_repos(self):
        """Test that public_repos returns the expected list of repos"""
        # Create client instance with 'google' as the org name
        client = GithubOrgClient('google')
        # Call the method under test
        result = client.public_repos()
        # Assert the result matches the expected list of repos from fixtures
        self.assertEqual(result, self.expected_repos)

    def test_public_repos_with_license(self):
        """Test that public_repos with license filter returns the correct
        repos"""
        # Create client instance with 'google' as the org name
        client = GithubOrgClient('google')
        # Call the method under test with apache-2.0 license filter
        result = client.public_repos(license="apache-2.0")
        # Assert the result matches the expected list of apache2 repos from
        # fixtures
        self.assertEqual(result, self.apache2_repos)


if __name__ == "__main__":
    unittest.main()
