# Unittests and Integration Tests

This project focuses on implementing unit tests and integration tests in Python. The goal is to understand the difference between unit and integration tests, apply parameterized testing, mock objects, fixtures, and learn how to measure code coverage.

## Project Overview

The repository contains utility functions and a GitHub organization client that will be tested using various testing techniques. We'll implement:

- Parameterized unit tests
- Mock HTTP calls
- Memoization testing
- Property mocking
- Integration tests with fixtures

## Testing Approach

### Unit Tests
We use Python's `unittest` framework to write unit tests that verify individual components work as expected in isolation.

### Parameterized Testing
Using the `parameterized` package to run the same test with different inputs and expected outputs.

### Mocking
Using `unittest.mock` to patch external dependencies and simulate responses from external systems.

### Integration Tests
Tests that verify multiple components work together correctly.

## Requirements

- Python 3.7+
- parameterized package
- All files should be executable
- All code should follow PEP8 style guidelines

## Running the Tests

```bash
# Run all tests
python -m unittest discover

# Run specific test file
python -m unittest test_utils.py
```

## File Structure

- `utils.py`: Contains utility functions for accessing nested maps, getting JSON from remote URLs, and memoization
- `client.py`: GitHub organization client implementation
- `test_utils.py`: Unit tests for utility functions
- `test_client.py`: Unit and integration tests for the GitHub client
- `fixtures.py`: Test fixtures for integration tests

