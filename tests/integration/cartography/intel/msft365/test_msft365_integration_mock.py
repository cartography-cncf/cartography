import unittest
import json
import os
from unittest.mock import patch, MagicMock
from neo4j import GraphDatabase

# Import the functions to test
from cartography.intel.msft365.msft365 import (
    sync_Msft365_users,
    sync_Msft365_user_group_relationships,
    sync_Msft365_device_relationships
)

# Load mock data from fixtures
def load_fixture(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, "fixtures", file_name), 'r') as f:
        return json.load(f)

class TestMsft365Neo4jSync(unittest.TestCase):
    def setUp(self):
        # Mock environment variables
        self.tenant_id = "mock_tenant"
        self.client_id = "mock_client"
        self.client_secret = "mock_secret"
        self.neo4j_uri = "bolt://localhost:7687"
        self.neo4j_user = "neo4j"
        self.neo4j_password = "password"
        
        os.environ.update({
            "Msft365_TENANT_ID": self.tenant_id,
            "Msft365_CLIENT_ID": self.client_id,
            "Msft365_CLIENT_SECRET": self.client_secret
        })

        # Create mock Neo4j session
        self.mock_session = MagicMock()
        self.mock_result = MagicMock()
        self.mock_result.single.return_value = {"count": 0}
        self.mock_session.run.return_value = self.mock_result

    @patch('requests.post')
    @patch('requests.get')
    @patch('neo4j.GraphDatabase.driver')
    def test_user_sync_to_neo4j(self, mock_driver, mock_get, mock_post):
        """End-to-end test of user data sync with mock data"""
        # Configure mocks
        mock_post.return_value = self._mock_auth_response()
        mock_get.return_value = self._mock_api_response(load_fixture("users.json"))
        mock_driver.return_value.session.return_value = self.mock_session

        # Execute sync
        sync_Msft365_users(
            self.mock_session,
            "mock_token",
            "test_update_tag",
            {}
        )

        # Verify database operations
        self._assert_user_operations()

    @patch('requests.post')
    @patch('requests.get')
    @patch('neo4j.GraphDatabase.driver')
    def test_group_membership_sync(self, mock_driver, mock_get, mock_post):
        """Validate group membership relationships with mock data"""
        # Configure mocks
        mock_post.return_value = self._mock_auth_response()
        mock_get.side_effect = [
            self._mock_api_response(load_fixture("groups.json")),
            self._mock_api_response(load_fixture("users.json"))  # Mock members
        ]
        mock_driver.return_value.session.return_value = self.mock_session

        # Execute sync
        sync_Msft365_user_group_relationships(
            self.mock_session,
            "mock_token",
            load_fixture("groups.json"),
            "test_update_tag",
            {}
        )

        # Verify relationships
        self._assert_group_operations()

    @patch('requests.post')
    @patch('requests.get')
    @patch('neo4j.GraphDatabase.driver')
    def test_device_ownership_relationships(self, mock_driver, mock_get, mock_post):
        """Test device ownership with mock data"""
        # Configure mocks
        mock_post.return_value = self._mock_auth_response()
        mock_get.side_effect = [
            self._mock_api_response(load_fixture("devices.json")),
            self._mock_api_response(load_fixture("users.json"))  # Mock owners
        ]
        mock_driver.return_value.session.return_value = self.mock_session

        # Execute sync
        sync_Msft365_device_relationships(
            self.mock_session,
            "mock_token",
            load_fixture("devices.json"),
            load_fixture("users.json"),
            "test_update_tag",
            {}
        )

        # Verify device relationships
        self._assert_device_operations()

    def _mock_auth_response(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access_token": "mock_token"}
        return mock_resp

    def _mock_api_response(self, data):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"value": data}
        return mock_resp

    def _assert_user_operations(self):
        # Verify user nodes created
        user_data = load_fixture("users.json")
        calls = self.mock_session.run.call_args_list
        
        # Check cleanup operation
        self.assertIn("MATCH (u:Msft365User) DETACH DELETE u", str(calls[0]))
        
        # Check node creation
        create_calls = [c for c in calls if "CREATE (u:Msft365User" in str(c)]
        self.assertEqual(len(create_calls), len(user_data))

    def _assert_group_operations(self):
        # Verify group relationships
        group_data = load_fixture("groups.json")
        user_data = load_fixture("users.json")
        calls = self.mock_session.run.call_args_list
        
        # Check group nodes created
        group_calls = [c for c in calls if "MERGE (g:Msft365Group" in str(c)]
        self.assertEqual(len(group_calls), len(group_data))
        
        # Check relationships created
        rel_calls = [c for c in calls if "MERGE (u)-[:MEMBER_OF]->(g)" in str(c)]
        self.assertEqual(len(rel_calls), len(user_data))

    def _assert_device_operations(self):
        # Verify device relationships
        device_data = load_fixture("devices.json")
        user_data = load_fixture("users.json")
        calls = self.mock_session.run.call_args_list
        
        # Check device nodes created
        device_calls = [c for c in calls if "CREATE (d:Msft365Device" in str(c)]
        self.assertEqual(len(device_calls), len(device_data))
        
        # Check ownership relationships
        rel_calls = [c for c in calls if "MERGE (u)-[:OWNED_BY]->(d)" in str(c)]
        self.assertEqual(len(rel_calls), len(user_data))
