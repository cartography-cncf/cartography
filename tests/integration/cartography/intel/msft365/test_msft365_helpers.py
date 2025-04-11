# test_helpers.py
import json
import os
from unittest.mock import MagicMock

def create_mock_response(status_code=200, json_data=None):
    """Create a mock response object that mimics requests.Response"""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    mock_response.text = json.dumps(json_data) if json_data else ""
    return mock_response

def mock_auth_response():
    """Return a standard mock authentication response"""
    return create_mock_response(
        json_data={"access_token": "mock_token", "expires_in": 3600}
    )

def mock_users_response():
    """Return a standard mock users response"""
    return create_mock_response(
        json_data={"value": [
            {
                "id": "user1",
                "displayName": "User One",
                "userPrincipalName": "user1@example.com",
                "mail": "user1@example.com",
                "jobTitle": "Developer",
                "department": "Engineering"
            },
            {
                "id": "user2",
                "displayName": "User Two",
                "userPrincipalName": "user2@example.com",
                "mail": "user2@example.com",
                "jobTitle": "Manager",
                "department": "Engineering"
            }
        ]}
    )

def setup_mock_neo4j_session():
    """Set up a mock Neo4j session"""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single.return_value = {"count": 2}
    mock_session.run.return_value = mock_result
    return mock_session
