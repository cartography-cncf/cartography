import logging

import cartography.intel.kandji
import tests.data.kandji.devices
import tests.data.kandji.tenant
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

logger = logging.getLogger(__name__)


def test_load_kandji_devices_relationship(neo4j_session):
    # Arrange
    TEST_UPDATE_TAG = 1234
    TEST_KANDJI_TENANT_ID = tests.data.kandji.tenant.TENANT["company_a"]["id"]
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_KANDJI_TENANT_ID,
    }
    data = tests.data.kandji.devices.DEVICES['company_a_devices']

    # Act
    cartography.intel.kandji.devices.load_devices(
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
        'KandjiTenant',
        ['id'],
    )

    # Make sure the expected Devices are created
    expected_nodes = {
        ('fc60decb-30cb-4db1-b3ec-2fa8ea1b83ed',),
        ('f27bcd08-f653-4930-83b0-51970e923b98',),
    }
    assert check_nodes(
        neo4j_session,
        "KandjiDevice",
        ["id"],
    ) == expected_nodes

    # Make sure the expected relationships are created
    expected_nodes_relationships = {
        ('Company A', 'fc60decb-30cb-4db1-b3ec-2fa8ea1b83ed'),
        ('Company A', 'f27bcd08-f653-4930-83b0-51970e923b98'),
    }
    assert check_rels(
        neo4j_session,
        'KandjiTenant',
        'id',
        'KandjiDevice',
        'id',
        'ENROLLED_TO',
        rel_direction_right=False,
    ) == expected_nodes_relationships

    # Cleanup test data
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1234,
        "TENANT_ID": TEST_KANDJI_TENANT_ID,
    }
    cartography.intel.kandji.devices.cleanup(
        neo4j_session,
        common_job_parameters,
    )


def test_cleanup_kandji_devices(neo4j_session):
    # Arrange
    TEST_UPDATE_TAG = 1234
    TEST_KANDJI_TENANT_ID = tests.data.kandji.tenant.TENANT["company_a"]["id"]
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_KANDJI_TENANT_ID,
    }
    data = tests.data.kandji.devices.DEVICES['company_a_devices']

    # Act
    cartography.intel.kandji.devices.load_devices(
        neo4j_session,
        common_job_parameters,
        data,
    )

    # Arrange: load in an unrelated data with different UPDATE_TAG
    UNRELATED_UPDATE_TAG = TEST_UPDATE_TAG + 1
    TENANT_ID = tests.data.kandji.tenant.TENANT["company_b"]["id"]
    common_job_parameters = {
        "UPDATE_TAG": UNRELATED_UPDATE_TAG,
        "TENANT_ID": TENANT_ID,
    }
    data = tests.data.kandji.devices.DEVICES["company_b_devices"]

    cartography.intel.kandji.devices.load_devices(
        neo4j_session,
        common_job_parameters,
        data,
    )

    # # [Pre-test] Assert

    # [Pre-test] Assert that the unrelated data exists
    expected_nodes_relationships = {
        ("Company A", 'fc60decb-30cb-4db1-b3ec-2fa8ea1b83ed'),
        ('Company A', 'f27bcd08-f653-4930-83b0-51970e923b98'),
        ('Company B', '748C5E49-134E-486C-A609-88A66A1BE4A1'),
        ('Company B', '706AF44A-9F51-4E84-B336-C4924097FFB6'),

    }
    assert check_rels(
        neo4j_session,
        'KandjiTenant',
        'id',
        'KandjiDevice',
        'id',
        'ENROLLED_TO',
        rel_direction_right=False,
    ) == expected_nodes_relationships

    # Act: run the cleanup job to remove all nodes except the unrelated data
    common_job_parameters = {
        "UPDATE_TAG": UNRELATED_UPDATE_TAG,
        "TENANT_ID": TEST_KANDJI_TENANT_ID,
    }
    cartography.intel.kandji.devices.cleanup(
        neo4j_session,
        common_job_parameters,
    )

    # Assert: Expect unrelated data nodes remains
    expected_nodes_unrelated = {
        ('748C5E49-134E-486C-A609-88A66A1BE4A1',),
        ('706AF44A-9F51-4E84-B336-C4924097FFB6',),
    }

    assert check_nodes(
        neo4j_session,
        "KandjiDevice",
        ["id"],
    ) == expected_nodes_unrelated

    # Cleanup test data
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1234,
        "TENANT_ID": TEST_KANDJI_TENANT_ID,
    }
    cartography.intel.kandji.devices.cleanup(
        neo4j_session,
        common_job_parameters,
    )
