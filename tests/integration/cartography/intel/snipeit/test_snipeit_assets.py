import logging

import cartography.intel.snipeit
import tests.data.snipeit.assets
import tests.data.snipeit.tenants
import tests.data.snipeit.users
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

logger = logging.getLogger(__name__)


def test_load_snipeit_assets_relationship(neo4j_session):
    # Arrange
    TEST_UPDATE_TAG = 1234
    TEST_snipeit_TENANT_ID = tests.data.snipeit.tenants.TENANTS["company_a"]["id"]
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_snipeit_TENANT_ID,
    }

    # Load test users for the relationship
    data = tests.data.snipeit.users.USERS['company_a']
    cartography.intel.snipeit.user.load_users(
        neo4j_session,
        common_job_parameters,
        data,
    )

    data = tests.data.snipeit.assets.ASSETS['company_a']

    # Act
    cartography.intel.snipeit.asset.load_assets(
        neo4j_session,
        common_job_parameters,
        data,
    )

    # Assert

    # Make sure the expected Tenant is created
    expected_nodes = {
        ('Company A',),
    }
    check_nodes(
        neo4j_session,
        'snipeitTenant',
        ['id'],
    )

    # Make sure the expected assets are created
    expected_nodes = {
        (1373, "C02ZJ48XXXXX"),
        (1372, "72ec94a8-b6dc-37f1-b2a9-0907806e8db7"),
    }
    assert check_nodes(
        neo4j_session,
        "SnipeitAsset",
        ["id", "serial"],
    ) == expected_nodes

    # Make sure the expected relationships are created
    expected_nodes_relationships = {
        ('Company A', "C02ZJ48XXXXX"),
        ('Company A', "72ec94a8-b6dc-37f1-b2a9-0907806e8db7"),
    }
    assert check_rels(
        neo4j_session,
        'SnipeitTenant',
        'id',
        'SnipeitAsset',
        'serial',
        'HAS_ASSET',
        rel_direction_right=True,
    ) == expected_nodes_relationships

    expected_nodes_relationships = {
        ("mcarter@example.net", "C02ZJ48XXXXX"),
    }
    assert check_rels(
        neo4j_session,
        'SnipeitUser',
        'email',
        'SnipeitAsset',
        'serial',
        'HAS_CHECKED_OUT',
        rel_direction_right=True,
    ) == expected_nodes_relationships

    # Cleanup test data
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1234,
        "TENANT_ID": TEST_snipeit_TENANT_ID,
    }
    cartography.intel.snipeit.asset.cleanup(
        neo4j_session,
        common_job_parameters,
    )


def test_cleanup_snipeit_assets(neo4j_session):
    # Arrange
    TEST_UPDATE_TAG = 1234
    TEST_snipeit_TENANT_ID = tests.data.snipeit.tenants.TENANTS["company_a"]["id"]
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_snipeit_TENANT_ID,
    }
    data = tests.data.snipeit.assets.ASSETS['company_a']

    # Act
    cartography.intel.snipeit.asset.load_assets(
        neo4j_session,
        common_job_parameters,
        data,
    )

    # Arrange: load in an unrelated data with different UPDATE_TAG
    UNRELATED_UPDATE_TAG = TEST_UPDATE_TAG + 1
    TENANT_ID = tests.data.snipeit.tenants.TENANTS["company_b"]["id"]
    common_job_parameters = {
        "UPDATE_TAG": UNRELATED_UPDATE_TAG,
        "TENANT_ID": TENANT_ID,
    }
    data = tests.data.snipeit.assets.ASSETS["company_b"]

    cartography.intel.snipeit.asset.load_assets(
        neo4j_session,
        common_job_parameters,
        data,
    )

    # # [Pre-test] Assert

    # [Pre-test] Assert that the unrelated data exists
    expected_nodes_relationships = {
        ("Company A", 1373),
        ('Company A', 1372),
        ('Company B', 2598),
        ('Company B', 2597),

    }
    assert check_rels(
        neo4j_session,
        'SnipeitTenant',
        'id',
        'SnipeitAsset',
        'id',
        'HAS_ASSET',
        rel_direction_right=True,
    ) == expected_nodes_relationships

    # Act: run the cleanup job to remove all nodes except the unrelated data
    common_job_parameters = {
        "UPDATE_TAG": UNRELATED_UPDATE_TAG,
        "TENANT_ID": TEST_snipeit_TENANT_ID,
    }
    cartography.intel.snipeit.asset.cleanup(
        neo4j_session,
        common_job_parameters,
    )

    # Assert: Expect unrelated data nodes remains
    expected_nodes_unrelated = {
        (2597,),
        (2598,),
    }

    assert check_nodes(
        neo4j_session,
        "SnipeitAsset",
        ["id"],
    ) == expected_nodes_unrelated

    # Cleanup all test data
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 9999,
        "TENANT_ID": TEST_snipeit_TENANT_ID,
    }
    cartography.intel.snipeit.asset.cleanup(
        neo4j_session,
        common_job_parameters,
    )
