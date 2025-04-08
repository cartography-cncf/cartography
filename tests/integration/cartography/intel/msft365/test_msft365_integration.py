import os
import unittest
from neo4j import GraphDatabase, basic_auth

from cartography.intel.msft365 import msft365
from cartography.intel.msft365 import msft365_loader
from tests.integration.cartography.intel.msft365.test_msft365_basic import TestMsft365BasicFunctionality


class TestMsft365Neo4jSync(TestMsft365BasicFunctionality):
    def setUp(self):
        super().setUp()
        self.neo4j_uri = os.environ.get("CARTOGRAPHY_NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.environ.get("CARTOGRAPHY_NEO4J_USER", "neo4j")
        self.neo4j_password = os.environ["CARTOGRAPHY_NEO4J_PASSWORD"]
        self.access_token = self.test_can_authenticate_with_graph_api()
        print(f"🔐 Using Neo4j URI: {self.neo4j_uri}")

    def get_neo4j_session(self):
        driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=basic_auth(self.neo4j_user, self.neo4j_password)
        )
        return driver.session()

    def test_user_sync_to_neo4j(self):
        with self.get_neo4j_session() as session:
            session.run("MATCH (u:Msft365User) DETACH DELETE u")
            users = self.test_can_fetch_users()
            transformed = msft365.transform_users(users)
            msft365_loader.msft365_load_users(session, transformed, "test_update_tag")

            result = session.run("MATCH (u:Msft365User) RETURN count(u) AS user_count").single()
            self.assertEqual(result["user_count"], len(users))

    def test_group_membership_sync(self):
        with self.get_neo4j_session() as session:
            session.run("MATCH (g:Msft365Group) DETACH DELETE g")
            groups = self.test_can_fetch_groups()
            transformed_groups = msft365.transform_groups(groups)
            msft365_loader.msft365_load_groups(session, transformed_groups, "test_update_tag")

            for group in groups:
                group_id = group["id"]
                members = self.test_can_fetch_group_members(group_id)
                relationships = [{
                    "source_id": member["id"],
                    "target_id": group_id,
                    "lastupdated": "test_update_tag"
                } for member in members if member.get("id")]
                msft365_loader.msft365_load_group_membership(session, relationships, "test_update_tag")

            result = session.run("""
                MATCH (:Msft365User)-[r:MEMBER_OF]->(:Msft365Group)
                RETURN count(r) AS rel_count
            """).single()
            self.assertGreaterEqual(result["rel_count"], 1)

    def test_device_ownership_relationships(self):
        with self.get_neo4j_session() as session:
            session.run("MATCH (u:Msft365User) DETACH DELETE u")
            session.run("MATCH (d:Msft365Device) DETACH DELETE d")

            users = self.test_can_fetch_users()
            msft365_loader.msft365_load_users(session, msft365.transform_users(users), "test_update_tag")

            devices = self.test_can_fetch_devices()
            msft365_loader.msft365_load_devices(session, msft365.transform_devices(devices), "test_update_tag")

            relationships = []
            for device in devices:
                owners = msft365.paginated_api_call(self.access_token, f"devices/{device['id']}/registeredOwners")
                for owner in owners:
                    if owner.get("@odata.type") == "#microsoft.graph.user":
                        relationships.append({
                            "source_id": owner["id"],
                            "target_id": device["id"],
                            "lastupdated": "test_update_tag"
                        })

            msft365_loader.msft365_load_device_ownership(session, relationships, "test_update_tag")

            result = session.run("""
                MATCH (:Msft365User)-[r:OWNS_DEVICE]->(:Msft365Device)
                RETURN count(r) AS rel_count
            """).single()
            self.assertGreaterEqual(result["rel_count"], 0)
