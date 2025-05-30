#!/usr/bin/env python3
"""
Unit tests for utils module
"""
import unittest
from unittest.mock import patch, Mock
from parameterized import parameterized
from utils import access_nested_map, get_json, memoize


class TestAccessNestedMap(unittest.TestCase):
    """
    Tests for access_nested_map function
    """
    @parameterized.expand([
        ({"a": 1}, ("a",), 1),
        ({"a": {"b": 2}}, ("a",), {"b": 2}),
        ({"a": {"b": 2}}, ("a", "b"), 2),
    ])
    def test_access_nested_map(self, nested_map, path, expected):
        """Test that access_nested_map returns expected results"""
        self.assertEqual(access_nested_map(nested_map, path), expected)

    @parameterized.expand([
        ({}, ("a",), "a"),
        ({"a": 1}, ("a", "b"), "b"),
    ])
    def test_access_nested_map_exception(self, nested_map, path, expected):
        """Test that access_nested_map raises KeyError with expected message"""
        with self.assertRaises(KeyError) as context:
            access_nested_map(nested_map, path)
        self.assertEqual(str(context.exception), f"'{expected}'")


class TestGetJson(unittest.TestCase):
    """Tests for get_json function"""

    @parameterized.expand([
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False}),
    ])
    @patch('requests.get')
    def test_get_json(self, test_url, test_payload, mock_get):
        """Test that get_json returns expected result"""
        # Configure the mock to return a response with a JSON payload
        mock_response = Mock()
        mock_response.json.return_value = test_payload
        mock_get.return_value = mock_response

        # Call the function under test
        result = get_json(test_url)

        # Assert that requests.get was called exactly once with the expected URL
        mock_get.assert_called_once_with(test_url)

        # Assert that the output of get_json is equal to test_payload
        self.assertEqual(result, test_payload)


class TestMemoize(unittest.TestCase):
    """Tests for memoize decorator"""

    def test_memoize(self):
        """Test that when calling a_property twice, the correct result is returned
        but a_method is only called once"""
        class TestClass:
            """Test class for memoization"""
            def a_method(self):
                """Method that returns 42"""
                return 42

            @memoize
            def a_property(self):
                """Property that returns the result of a_method"""
                return self.a_method()

        # Create an instance of TestClass
        test_obj = TestClass()

        # Mock a_method
        with patch.object(TestClass, 'a_method', return_value=42) as mock_method:
            # Call a_property twice
            first_call = test_obj.a_property
            second_call = test_obj.a_property

            # Check that both calls return the expected result
            self.assertEqual(first_call, 42)
            self.assertEqual(second_call, 42)

            # Check that a_method was only called once
            mock_method.assert_called_once()


if __name__ == "__main__":
    unittest.main()

