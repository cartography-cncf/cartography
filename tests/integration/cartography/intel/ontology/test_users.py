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
    """Test sync behavior with empty source of truth list"""
    # Arrange
    _ensure_local_neo4j_has_test_duo_users(neo4j_session)
    _ensure_local_neo4j_has_test_tailscale_users(neo4j_session)

    # Act
    cartography.intel.ontology.users.sync(
        neo4j_session, [], TEST_UPDATE_TAG, {"UPDATE_TAG": TEST_UPDATE_TAG}
    )

    user_count = neo4j_session.run("MATCH (u:User) RETURN count(u) as count").single()[
        "count"
    ]
    assert user_count == 4


@patch.object(
    cartography.intel.ontology.users,
    "get_source_nodes_from_graph",
    return_value=EXISTING_DUO_USERS,
)
def test_load_ontology_users_integration(mock_get_source_nodes, neo4j_session):
    """Test end-to-end loading of ontology users"""

    # Arrange
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
