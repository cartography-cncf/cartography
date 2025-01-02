import logging

import cartography.intel.snipeit
import tests.data.snipeit.tenants
import tests.data.snipeit.users
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

logger = logging.getLogger(__name__)


def test_load_snipeit_user_relationship(neo4j_session):
    # Arrange
    TEST_UPDATE_TAG = 1234
    TEST_snipeit_TENANT_ID = tests.data.snipeit.tenants.TENANTS["company_a"]["id"]
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_snipeit_TENANT_ID,
    }
    data = tests.data.snipeit.users.USERS['company_a']

    # Act
    cartography.intel.snipeit.user.load_users(
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
        'SnipeitTenant',
        ['id'],
    )

    # Make sure the expected Devices are created
    expected_nodes = {
        (1, 'mcarter@example.net'),
        (2, 'snipe@snipe.net'),
    }
    assert check_nodes(
        neo4j_session,
        "SnipeitUser",
        ["id", "email"],
    ) == expected_nodes

    # Make sure the expected relationships are created
    expected_nodes_relationships = {
        ('Company A', 1),
        ('Company A', 2),
    }
    assert check_rels(
        neo4j_session,
        'SnipeitTenant',
        'id',
        'SnipeitUser',
        'id',
        'HAS_USER',
        rel_direction_right=True,
    ) == expected_nodes_relationships

    # Cleanup test data
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1234,
        "TENANT_ID": TEST_snipeit_TENANT_ID,
    }
    cartography.intel.snipeit.user.cleanup(
        neo4j_session,
        common_job_parameters,
    )


def test_cleanup_snipeit_users(neo4j_session):
    # Arrange
    TEST_UPDATE_TAG = 1234
    TEST_snipeit_TENANT_ID = tests.data.snipeit.tenants.TENANTS["company_a"]["id"]
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_snipeit_TENANT_ID,
    }
    data = tests.data.snipeit.users.USERS['company_a']

    # Act
    cartography.intel.snipeit.user.load_users(
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
    data = tests.data.snipeit.users.USERS['company_b']

    cartography.intel.snipeit.user.load_users(
        neo4j_session,
        common_job_parameters,
        data,
    )

    # # [Pre-test] Assert

    # [Pre-test] Assert that the related and unrelated data exists
    expected_nodes_relationships = {
        ('Company A', 1),
        ('Company A', 2),
        ('Company B', 3),
        ('Company B', 4),
    }
    assert check_rels(
        neo4j_session,
        'SnipeitTenant',
        'id',
        'SnipeitUser',
        'id',
        'HAS_USER',
        rel_direction_right=True,
    ) == expected_nodes_relationships

    # Act: run the cleanup job to remove all nodes except the unrelated data
    common_job_parameters = {
        "UPDATE_TAG": UNRELATED_UPDATE_TAG,
        "TENANT_ID": TEST_snipeit_TENANT_ID,
    }
    cartography.intel.snipeit.user.cleanup(
        neo4j_session,
        common_job_parameters,
    )

    # Assert: Expect unrelated data nodes remains
    expected_nodes_unrelated = {
        (3, "agianotto@grokability.com"),
        (4, "sparisian@example.net"),
    }

    assert check_nodes(
        neo4j_session,
        "SnipeitUser",
        ["id", "email"],
    ) == expected_nodes_unrelated

    # Cleanup test data
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 9999,
        "TENANT_ID": TEST_snipeit_TENANT_ID,
    }
    cartography.intel.snipeit.user.cleanup(
        neo4j_session,
        common_job_parameters,
    )
