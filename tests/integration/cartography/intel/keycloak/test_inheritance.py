import cartography.intel.keycloak.inheritance
from tests.integration.util import check_rels

TEST_REALM = "inheritance-test"
TEST_UPDATE_TAG = 123456789


def test_group_role_inheritance_uses_scoped_matchlinks(neo4j_session):
    neo4j_session.run(
        """
        MERGE (realm:KeycloakRealm {name: $realm})
        MERGE (user:KeycloakUser {id: "inheritance-user"})
        MERGE (group:KeycloakGroup {id: "inheritance-group"})
        MERGE (role:KeycloakRole {id: "inheritance-role"})
        MERGE (realm)-[:RESOURCE]->(user)
        MERGE (realm)-[:RESOURCE]->(group)
        MERGE (realm)-[:RESOURCE]->(role)
        MERGE (user)-[:MEMBER_OF]->(group)
        MERGE (group)-[:GRANTS]->(role)
        """,
        realm=TEST_REALM,
    )

    cartography.intel.keycloak.inheritance._sync_realm_inheritance(
        neo4j_session,
        TEST_REALM,
        TEST_UPDATE_TAG,
    )

    expected_relationships = {("inheritance-user", "inheritance-role")}
    assert (
        check_rels(
            neo4j_session,
            "KeycloakUser",
            "id",
            "KeycloakRole",
            "id",
            "ASSUME_ROLE",
            rel_direction_right=True,
        )
        == expected_relationships
    )
    assert (
        check_rels(
            neo4j_session,
            "KeycloakUser",
            "id",
            "KeycloakRole",
            "id",
            "HAS_ROLE",
            rel_direction_right=True,
        )
        == expected_relationships
    )

    neo4j_session.run(
        """
        MATCH (:KeycloakGroup {id: "inheritance-group"})-[r:GRANTS]->
              (:KeycloakRole {id: "inheritance-role"})
        DELETE r
        """,
    )
    cartography.intel.keycloak.inheritance._sync_realm_inheritance(
        neo4j_session,
        TEST_REALM,
        TEST_UPDATE_TAG + 1,
    )
    cartography.intel.keycloak.inheritance._cleanup_realm(
        neo4j_session,
        TEST_REALM,
        TEST_UPDATE_TAG + 1,
    )

    assert (
        check_rels(
            neo4j_session,
            "KeycloakUser",
            "id",
            "KeycloakRole",
            "id",
            "ASSUME_ROLE",
            rel_direction_right=True,
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "KeycloakUser",
            "id",
            "KeycloakRole",
            "id",
            "HAS_ROLE",
            rel_direction_right=True,
        )
        == set()
    )
