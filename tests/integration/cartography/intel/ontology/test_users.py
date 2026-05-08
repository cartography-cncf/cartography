from unittest.mock import patch

import cartography.intel.ontology.users
import tests.data.duo.users
from cartography.intel.duo.users import _transform_users
from tests.integration.cartography.intel.duo.test_users import (
    _ensure_local_neo4j_has_test_users as _ensure_local_neo4j_has_test_duo_users,
)
from tests.integration.cartography.intel.tailscale.test_users import (
    _ensure_local_neo4j_has_test_users as _ensure_local_neo4j_has_test_tailscale_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
EXISTING_DUO_USERS = _transform_users(tests.data.duo.users.GET_USERS_RESPONSE)


def test_sync_with_empty_source_list(neo4j_session):
    """Test sync behavior with empty source of truth list - should default to 'ontology' source"""
    # Arrange - Create UserAccount nodes with the fields expected by the 'ontology' source mapping
    neo4j_session.run(
        """
        UNWIND $users as user
        CREATE (u:UserAccount {
            id: user.id,
            _ont_email: user.email,
            _ont_fullname: user.fullname,
            _ont_firstname: user.firstname,
            _ont_lastname: user.lastname,
            lastupdated: $update_tag
        })
        """,
        users=[
            {
                "id": "user1",
                "email": "homer@simpson.corp",
                "fullname": "Homer Simpson",
                "firstname": "Homer",
                "lastname": "Simpson",
            },
            {
                "id": "user2",
                "email": "marge@simpson.corp",
                "fullname": "Marge Simpson",
                "firstname": "Marge",
                "lastname": "Simpson",
            },
        ],
        update_tag=TEST_UPDATE_TAG,
    )

    # Act - Empty source list should default to 'ontology' source
    cartography.intel.ontology.users.sync(
        neo4j_session, [], TEST_UPDATE_TAG, {"UPDATE_TAG": TEST_UPDATE_TAG}
    )

    # Assert - Check that User nodes were created from UserAccount nodes
    user_count = neo4j_session.run("MATCH (u:User) RETURN count(u) as count").single()[
        "count"
    ]
    assert user_count == 2


def test_sync_accepts_entra_as_alias_for_microsoft_useraccounts(neo4j_session):
    """Legacy 'entra' source names should still resolve to Microsoft user accounts."""
    neo4j_session.run("MATCH (n) DETACH DELETE n;")
    neo4j_session.run(
        """
        CREATE (:UserAccount {
            id: 'msft-user-1',
            _ont_source: 'microsoft',
            _ont_email: 'homer@simpson.corp',
            _ont_fullname: 'Homer Simpson',
            _ont_firstname: 'Homer',
            _ont_lastname: 'Simpson',
            lastupdated: $update_tag
        })
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    cartography.intel.ontology.users.sync(
        neo4j_session, ["entra"], TEST_UPDATE_TAG, {"UPDATE_TAG": TEST_UPDATE_TAG}
    )

    assert check_nodes(
        neo4j_session,
        "User",
        ["email", "firstname", "lastname"],
    ) == {("homer@simpson.corp", "Homer", "Simpson")}


@patch.object(
    cartography.intel.ontology.users,
    "get_source_nodes_from_graph",
    return_value=EXISTING_DUO_USERS,
)
def test_load_ontology_users_integration(mock_get_source_nodes, neo4j_session):
    """Test end-to-end loading of ontology users"""

    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n;")  # Clean the database
    _ensure_local_neo4j_has_test_duo_users(neo4j_session)
    _ensure_local_neo4j_has_test_tailscale_users(neo4j_session)

    # Act
    cartography.intel.ontology.users.sync(
        neo4j_session, ["duo"], TEST_UPDATE_TAG, {"UPDATE_TAG": TEST_UPDATE_TAG}
    )

    # Assert - Check that User nodes were created
    expected_users = {
        ("lmsimpson@simpson.corp", "Lisa", "Simpson"),
        ("bjsimpson@simpson.corp", "Bart", "Simpson"),
        ("hjsimpson@simpson.corp", "Homer", "Simpson"),
        ("mbsimpson@simpson.corp", "Marge", "Simpson"),
    }

    actual_users = check_nodes(
        neo4j_session, "User", ["email", "firstname", "lastname"]
    )
    assert actual_users == expected_users

    # Assert - Check that User nodes have Ontology label
    users_with_ontology_label = neo4j_session.run(
        "MATCH (u:User:Ontology) RETURN count(u) as count"
    ).single()["count"]
    assert users_with_ontology_label == 4

    # Assert - Check that relationships to DuoUser nodes were created
    expected_rels = {
        ("hjsimpson@simpson.corp", "hjsimpson@simpson.corp"),
        ("mbsimpson@simpson.corp", "mbsimpson@simpson.corp"),
        ("lmsimpson@simpson.corp", "lmsimpson@simpson.corp"),
        ("bjsimpson@simpson.corp", "bjsimpson@simpson.corp"),
    }
    actual_rels = check_rels(
        neo4j_session,
        "User",
        "email",
        "DuoUser",
        "email",
        "HAS_ACCOUNT",
        rel_direction_right=True,
    )
    assert actual_rels == expected_rels

    # Assert - Check that relationships to TailscaleUser nodes were created
    expected_rels = {
        ("mbsimpson@simpson.corp", "mbsimpson@simpson.corp"),
        ("hjsimpson@simpson.corp", "hjsimpson@simpson.corp"),
    }
    actual_rels = check_rels(
        neo4j_session,
        "User",
        "email",
        "TailscaleUser",
        "email",
        "HAS_ACCOUNT",
        rel_direction_right=True,
    )
    assert actual_rels == expected_rels


def test_cleanup_removes_stale_custom_user_relationships(neo4j_session):
    """User cleanup should delete stale custom ontology-derived relationships."""
    neo4j_session.run("MATCH (n) DETACH DELETE n;")
    stale_tag = TEST_UPDATE_TAG - 1

    neo4j_session.run(
        """
        MERGE (u:User:Ontology {id: 'hjsimpson@simpson.corp'})
        SET u.email = 'hjsimpson@simpson.corp',
            u.lastupdated = $update_tag

        MERGE (acct:UserAccount {id: 'acct-1'})
        SET acct.email = 'hjsimpson@simpson.corp'
        MERGE (u)-[fresh_has_account:HAS_ACCOUNT]->(acct)
        SET fresh_has_account.lastupdated = $update_tag

        MERGE (sso:AWSSSOUser {id: 'sso-1'})
        MERGE (u)-[stale_sso:HAS_ACCOUNT]->(sso)
        SET stale_sso.lastupdated = $stale_tag

        MERGE (gh:GitHubUser {id: 'github-1'})
        MERGE (u)-[stale_github:HAS_ACCOUNT]->(gh)
        SET stale_github.lastupdated = $stale_tag

        MERGE (key:AccountAccessKey:APIKey {id: 'key-1'})
        MERGE (u)-[stale_key:OWNS]->(key)
        SET stale_key.lastupdated = $stale_tag

        MERGE (app:GoogleWorkspaceOAuthApp:ThirdPartyApp {id: 'app-1'})
        MERGE (u)-[stale_auth:AUTHORIZED]->(app)
        SET stale_auth.lastupdated = $stale_tag
        """,
        update_tag=TEST_UPDATE_TAG,
        stale_tag=stale_tag,
    )

    cartography.intel.ontology.users.cleanup(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    stale_custom_rel_count = neo4j_session.run(
        """
        MATCH (:User {id: 'hjsimpson@simpson.corp'})-[r]->()
        WHERE (type(r) = 'HAS_ACCOUNT' AND endNode(r):AWSSSOUser)
           OR (type(r) = 'HAS_ACCOUNT' AND endNode(r):GitHubUser)
           OR (type(r) = 'OWNS' AND endNode(r):APIKey)
           OR (type(r) = 'AUTHORIZED' AND endNode(r):ThirdPartyApp)
        RETURN count(r) AS count
        """
    ).single()["count"]
    assert stale_custom_rel_count == 0

    fresh_useraccount_rel_count = neo4j_session.run(
        """
        MATCH (:User {id: 'hjsimpson@simpson.corp'})-[r:HAS_ACCOUNT]->(:UserAccount {id: 'acct-1'})
        RETURN count(r) AS count
        """
    ).single()["count"]
    assert fresh_useraccount_rel_count == 1
