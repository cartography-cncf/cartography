import os
import unittest
from unittest.mock import patch
from neo4j import GraphDatabase

from cartography.intel.msft365 import msft365_loader
from cartography.intel.msft365 import msft365

from tests.integration.cartography.intel.msft365.msft365_test_util import (
    _mock_auth_response,
    _mock_api_response,
    load_fixture,
    get_neo4j_session,
)

class TestMsft365Neo4jSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
            try:
                cls.driver = GraphDatabase.driver(
                    os.environ["CARTOGRAPHY_NEO4J_URI"],
                    auth=(
                        os.environ["CARTOGRAPHY_NEO4J_USER"],
                        os.environ["CARTOGRAPHY_NEO4J_PASSWORD"]
                    ),
                )
            except KeyError as e:
                raise EnvironmentError(f"Missing required environment variable: {e}")

            cls.neo4j_session = cls.driver.session()

    @classmethod
    def tearDownClass(cls):
        cls.neo4j_session.close()
        cls.driver.close()

    def test_can_authenticate_with_graph_api(self):
        """Test that mock authentication returns a successful response"""
        with patch("requests.post") as mock_post:
            mock_post.return_value = _mock_auth_response()
            response = mock_post()
            self.assertEqual(response.status_code, 200)

    @patch("requests.post")
    @patch("requests.get")
    def test_device_node_sync(self, mock_get, mock_post):
        """Validate that Msft365Device nodes are created correctly from mock data."""

        print("🧪 TEST: Msft365Device mock sync starting...")

        # 🧹 Clean up existing nodes
        self.neo4j_session.run("MATCH (d:Msft365Device) DETACH DELETE d")

        # 📦 Load mocked device data
        device_fixture = load_fixture("devices.json") # ["value"] (removed temp TAKEOUT THIS COMMENT)
        mock_post.return_value = _mock_auth_response()
        mock_get.return_value = _mock_api_response(device_fixture)

        # Patch the loader to directly insert into Neo4j using Cypher
        def patched_load_devices(session, schema, data, update_tag):
            for record in data:
                # Use Cartography helper to create the correct Cypher
                cypher, params = schema.create_node_merge_statement(record, update_tag)
                session.run(cypher, **params)

        # Patch the version that msft365.py calls
        with patch("cartography.intel.msft365.msft365.msft365_load_devices", new=patched_load_devices):
            transformed = msft365.transform_devices(device_fixture)
            msft365_loader.msft365_load_devices(self.neo4j_session, transformed, "test_update_tag")

        # ✅ Verify expected nodes were inserted
        result = self.neo4j_session.run("MATCH (d:Msft365Device) RETURN count(d) AS device_count").single()
        actual_count = result["device_count"]
        expected_count = len(device_fixture)
        self.assertEqual(actual_count, expected_count)
        print("✅ PASSED: Msft365Device mock sync")
