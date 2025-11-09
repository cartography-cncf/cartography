import logging

import cartography.intel.snipeit
import tests.data.snipeit.tenants
import tests.data.snipeit.users
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

logger = logging.getLogger(__name__)
TEST_UPDATE_TAG = 1234
TEST_SNIPEIT_TENANT_ID = tests.data.snipeit.tenants.TENANTS["simpson_corp"]["id"]


def _ensure_local_neo4j_has_test_snipeit_users(neo4j_session):
    """Helper function to populate Neo4j with test SnipeIt users."""
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_SNIPEIT_TENANT_ID,
    }
    cartography.intel.snipeit.user.load_users(
        neo4j_session,
        common_job_parameters,
        tests.data.snipeit.users.USERS["simpson_corp"],
    )


def test_load_snipeit_user_relationship(neo4j_session):
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_SNIPEIT_TENANT_ID,
    }
    data = tests.data.snipeit.users.USERS["simpson_corp"]

    # Act
    cartography.intel.snipeit.user.load_users(
        neo4j_session,
        common_job_parameters,
        data,
    )

    # Assert
    # Make sure the expected Tenant is created
    expected_nodes = {
        ("SimpsonCorp",),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SnipeitTenant",
            ["id"],
        )
        == expected_nodes
    )

    # Make sure the expected Devices are created
    expected_nodes = {
        (1, "mbsimpson@simpson.corp"),
        (2, "hjsimpson@simpson.corp"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SnipeitUser",
            ["id", "email"],
        )
        == expected_nodes
    )

    # Make sure the expected relationships are created
    expected_nodes_relationships = {
        ("SimpsonCorp", 1),
        ("SimpsonCorp", 2),
    }
    assert (
        check_rels(
            neo4j_session,
            "SnipeitTenant",
            "id",
            "SnipeitUser",
            "id",
            "HAS_USER",
            rel_direction_right=True,
        )
        == expected_nodes_relationships
    )

    # Cleanup test data
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1234,
        "TENANT_ID": TEST_SNIPEIT_TENANT_ID,
    }
    cartography.intel.snipeit.user.cleanup(
        neo4j_session,
        common_job_parameters,
    )


def test_cleanup_snipeit_users(neo4j_session):
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_SNIPEIT_TENANT_ID,
    }
    data = tests.data.snipeit.users.USERS["simpson_corp"]

    # Act
    cartography.intel.snipeit.user.load_users(
        neo4j_session,
        common_job_parameters,
        data,
    )

    # Arrange: load in an unrelated data with different UPDATE_TAG
    UNRELATED_UPDATE_TAG = TEST_UPDATE_TAG + 1
    OTHER_TENANT_ID = tests.data.snipeit.tenants.TENANTS["south_park"]["id"]
    common_job_parameters = {
        "UPDATE_TAG": UNRELATED_UPDATE_TAG,
        "TENANT_ID": OTHER_TENANT_ID,
    }
    data = tests.data.snipeit.users.USERS["south_park"]

    cartography.intel.snipeit.user.load_users(
        neo4j_session,
        common_job_parameters,
        data,
    )

    # # [Pre-test] Assert

    # [Pre-test] Assert that the related and unrelated data exists
    expected_nodes_relationships = {
        ("SimpsonCorp", 1),
        ("SimpsonCorp", 2),
        ("SouthPark", 3),
        ("SouthPark", 4),
    }
    assert (
        check_rels(
            neo4j_session,
            "SnipeitTenant",
            "id",
            "SnipeitUser",
            "id",
            "HAS_USER",
            rel_direction_right=True,
        )
        == expected_nodes_relationships
    )

    # Act: run the cleanup job to remove all nodes except the unrelated data
    common_job_parameters = {
        "UPDATE_TAG": UNRELATED_UPDATE_TAG,
        "TENANT_ID": TEST_SNIPEIT_TENANT_ID,
    }
    cartography.intel.snipeit.user.cleanup(
        neo4j_session,
        common_job_parameters,
    )

    # Assert: Expect unrelated data nodes remains
    expected_nodes_unrelated = {
        (3, "kbroflovski@south.park"),
        (4, "ecartman@south.park"),
    }

    assert (
        check_nodes(
            neo4j_session,
            "SnipeitUser",
            ["id", "email"],
        )
        == expected_nodes_unrelated
    )

    # Cleanup test data
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 9999,
        "TENANT_ID": TEST_SNIPEIT_TENANT_ID,
    }
    cartography.intel.snipeit.user.cleanup(
        neo4j_session,
        common_job_parameters,
    )
