import logging

import cartography.intel.snipeit
import tests.data.snipeit.assets
import tests.data.snipeit.tenants
import tests.data.snipeit.users
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

logger = logging.getLogger(__name__)
TEST_UPDATE_TAG = 1234
TEST_SNIPEIT_TENANT_ID = tests.data.snipeit.tenants.TENANTS["simpson_corp"]["id"]


def _ensure_local_neo4j_has_test_snipeit_assets(neo4j_session):
    """Helper function to populate Neo4j with test SnipeIt assets."""
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_SNIPEIT_TENANT_ID,
    }
    cartography.intel.snipeit.asset.load_assets(
        neo4j_session,
        common_job_parameters,
        tests.data.snipeit.assets.ASSETS["simpson_corp"],
    )


def test_load_snipeit_assets_relationship(neo4j_session):
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_SNIPEIT_TENANT_ID,
    }

    # Load test users for the relationship
    data = tests.data.snipeit.users.USERS["simpson_corp"]
    cartography.intel.snipeit.user.load_users(
        neo4j_session,
        common_job_parameters,
        data,
    )

    data = tests.data.snipeit.assets.ASSETS["simpson_corp"]

    # Act
    cartography.intel.snipeit.asset.load_assets(
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

    # Make sure the expected assets are created
    expected_nodes = {
        (1373, "SIMP-MAC-HOMER-01", "Ready to Deploy"),
        (1375, "SIMP-IOS-HOMER-01", "Ready to Deploy"),
        (1372, "SIMP-WIN-MARGE-01", "Ready to Deploy"),
        (1376, "SIMP-ANDROID-MARGE-01", "Ready to Deploy"),
        (1371, "SIMP-LINUX-MARGE-017", "Ready to Deploy"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SnipeitAsset",
            ["id", "serial", "status"],
        )
        == expected_nodes
    )

    # Make sure the expected relationships are created
    expected_nodes_relationships = {
        ("SimpsonCorp", "SIMP-ANDROID-MARGE-01"),
        ("SimpsonCorp", "SIMP-MAC-HOMER-01"),
        ("SimpsonCorp", "SIMP-WIN-MARGE-01"),
        ("SimpsonCorp", "SIMP-LINUX-MARGE-017"),
        ("SimpsonCorp", "SIMP-IOS-HOMER-01"),
    }
    assert (
        check_rels(
            neo4j_session,
            "SnipeitTenant",
            "id",
            "SnipeitAsset",
            "serial",
            "HAS_ASSET",
            rel_direction_right=True,
        )
        == expected_nodes_relationships
    )

    expected_nodes_relationships = {
        ("mbsimpson@simpson.corp", "SIMP-LINUX-MARGE-017"),
        ("mbsimpson@simpson.corp", "SIMP-WIN-MARGE-01"),
        ("mbsimpson@simpson.corp", "SIMP-ANDROID-MARGE-01"),
        ("hjsimpson@simpson.corp", "SIMP-MAC-HOMER-01"),
        ("hjsimpson@simpson.corp", "SIMP-IOS-HOMER-01"),
    }
    assert (
        check_rels(
            neo4j_session,
            "SnipeitUser",
            "email",
            "SnipeitAsset",
            "serial",
            "HAS_CHECKED_OUT",
            rel_direction_right=True,
        )
        == expected_nodes_relationships
    )

    # Cleanup test data
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1234,
        "TENANT_ID": TEST_SNIPEIT_TENANT_ID,
    }
    cartography.intel.snipeit.asset.cleanup(
        neo4j_session,
        common_job_parameters,
    )


def test_cleanup_snipeit_assets(neo4j_session):
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_SNIPEIT_TENANT_ID,
    }
    data = tests.data.snipeit.assets.ASSETS["simpson_corp"]

    # Act
    cartography.intel.snipeit.asset.load_assets(
        neo4j_session,
        common_job_parameters,
        data,
    )

    # Arrange: load in an unrelated data with different UPDATE_TAG
    UNRELATED_UPDATE_TAG = TEST_UPDATE_TAG + 1
    TENANT_ID = tests.data.snipeit.tenants.TENANTS["south_park"]["id"]
    common_job_parameters = {
        "UPDATE_TAG": UNRELATED_UPDATE_TAG,
        "TENANT_ID": TENANT_ID,
    }
    data = tests.data.snipeit.assets.ASSETS["south_park"]

    cartography.intel.snipeit.asset.load_assets(
        neo4j_session,
        common_job_parameters,
        data,
    )

    # # [Pre-test] Assert

    # [Pre-test] Assert that the unrelated data exists
    expected_nodes_relationships = {
        ("SimpsonCorp", 1373),
        ("SimpsonCorp", 1372),
        ("SimpsonCorp", 1375),
        ("SimpsonCorp", 1376),
        ("SimpsonCorp", 1371),
        ("SouthPark", 2598),
    }
    assert (
        check_rels(
            neo4j_session,
            "SnipeitTenant",
            "id",
            "SnipeitAsset",
            "id",
            "HAS_ASSET",
            rel_direction_right=True,
        )
        == expected_nodes_relationships
    )

    # Act: run the cleanup job to remove all nodes except the unrelated data
    common_job_parameters = {
        "UPDATE_TAG": UNRELATED_UPDATE_TAG,
        "TENANT_ID": TEST_SNIPEIT_TENANT_ID,
    }
    cartography.intel.snipeit.asset.cleanup(
        neo4j_session,
        common_job_parameters,
    )

    # Assert: Expect unrelated data nodes remains
    expected_nodes_unrelated = {
        (2598,),
    }

    assert (
        check_nodes(
            neo4j_session,
            "SnipeitAsset",
            ["id"],
        )
        == expected_nodes_unrelated
    )

    # Cleanup all test data
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 9999,
        "TENANT_ID": TEST_SNIPEIT_TENANT_ID,
    }
    cartography.intel.snipeit.asset.cleanup(
        neo4j_session,
        common_job_parameters,
    )
