import unittest
import requests
import os
from neo4j import GraphDatabase
from .test_msft365_basic import TestMsft365BasicFunctionality

class TestMsft365Neo4jSync(TestMsft365BasicFunctionality):
    def setUp(self):
        super().setUp()
        if not hasattr(self, 'access_token'):
            self.test_can_authenticate_with_graph_api()
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def test_user_sync_to_neo4j(self):
        """End-to-end test of user data sync"""
        self.test_can_authenticate_with_graph_api()
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Handle pagination
        users = []
        url = "https://graph.microsoft.com/v1.0/users"
        while url:
            response = requests.get(url, headers=headers).json()
            users.extend(response.get("value", []))
            url = response.get("@odata.nextLink")
        
        # Write to Neo4j
        with GraphDatabase.driver(self.neo4j_uri) as driver:
            with driver.session() as session:
                if not os.environ.get('PERSIST_TEST_DATA'):
                    session.run("MATCH (u:Msft365User) DETACH DELETE u")
                
                for user in users:
                    session.run(
                        "CREATE (u:Msft365User {id: $id, name: $name, email: $email})",
                        id=user['id'],
                        name=user.get('displayName'),
                        email=user.get('userPrincipalName')
                    )
                
                # Validate sync
                result = session.run("MATCH (u:Msft365User) RETURN count(u) AS count")
                actual_count = result.single()['count']
            if os.environ.get('PERSIST_TEST_DATA'):
                self.assertGreaterEqual(actual_count, len(users))
            else:
                self.assertEqual(actual_count, len(users))


    def test_group_membership_sync(self):
        """Validate group membership relationships in Neo4j"""
        groups = self.test_can_fetch_groups()
        group_id = groups[0]['id']
        members = self.test_can_fetch_group_members()

        with GraphDatabase.driver(self.neo4j_uri) as driver:
            with driver.session() as session:
                # Conditional cleanup
                if not os.environ.get('PERSIST_TEST_DATA'):
                    session.run("MATCH (g:Msft365Group) DETACH DELETE g")
                    session.run("MATCH ()-[r:MEMBER_OF]->() DELETE r")

                # Create/Merge groups
                for group in groups:
                    session.run(
                        """MERGE (g:Msft365Group {id: $id})
                        ON CREATE SET g.name = $name
                        ON MATCH SET g.name = $name""",
                        id=group['id'],
                        name=group.get('displayName')
                    )

                # Create relationships using MERGE
                for member in members:
                    session.run(
                        """MATCH (u:Msft365User {id: $user_id})
                        MATCH (g:Msft365Group {id: $group_id})
                        MERGE (u)-[:MEMBER_OF]->(g)""",
                        user_id=member['id'],
                        group_id=group_id
                    )

                # Adjusted verification
                result = session.run(
                    "MATCH (u:Msft365User)-[:MEMBER_OF]->(g:Msft365Group) " 
                    "RETURN count(*) AS count"
                )
                count = result.single()['count']
                
                if os.environ.get('PERSIST_TEST_DATA'):
                    self.assertGreaterEqual(count, 2)  # Allow existing relationships
                else:
                    self.assertEqual(count, 2)


    #  """Validate device ownership relationships in Neo4j"""
    def test_device_ownership_relationships(self):
       
        # Get test data
        devices = self.test_can_fetch_devices()
        if not devices:
            self.skipTest("No devices available for testing")
            
        device_id = devices[0]['id']
        headers = {"Authorization": f"Bearer {self.access_token}"}
        owners = requests.get(
            f"https://graph.microsoft.com/v1.0/devices/{device_id}/registeredOwners",
            headers=headers
        ).json().get('value', [])

        with GraphDatabase.driver(self.neo4j_uri,
                                auth=(self.neo4j_user, self.neo4j_password)) as driver:
            with driver.session() as session:
                # Clear existing relationships
                session.run("MATCH ()-[r:OWNED_BY]->() DELETE r")
                
                # Create relationships
                for owner in owners:
                    session.run(
                        """MATCH (u:Msft365User {id: $user_id}), (d:Msft365Device {id: $device_id})
                        MERGE (u)-[:OWNED_BY]->(d)""",
                        user_id=owner['id'],
                        device_id=device_id
                    )

                # Verify relationships
                result = session.run(
                    "MATCH (u:Msft365User)-[:OWNED_BY]->(d:Msft365Device) RETURN count(*) AS count"
                )
                self.assertGreater(result.single()['count'], 0)

            

        
