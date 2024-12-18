from cartography.intel.opal.opal_common import parse_opal_resource_access_configuration
from tests.data.opal.opal_aws import OPAL_ADMIN_TO_OKTA_MAP
from tests.data.opal.opal_aws import OPAL_RESOURCES
from tests.data.opal.opal_aws import OPAL_TO_OKTA_MAP


def test_parse_opal_resource_access_configuration():

    # Act: Call the function
    auto_approved_access, manual_approved_access = parse_opal_resource_access_configuration(
        OPAL_RESOURCES, OPAL_TO_OKTA_MAP, OPAL_ADMIN_TO_OKTA_MAP,
    )

    # Assert: Verify the results
    expected_auto_approved_access = [
        {'resource_id': 'resource_1', 'okta_group_id': 'okta_group_1'},
        {'resource_id': 'resource_1', 'okta_group_id': 'okta_group_2'},
        {'resource_id': 'resource_2', 'okta_group_id': 'okta_group_3'},
    ]
    expected_manual_approved_access = [
        {'resource_id': 'resource_1', 'okta_group_id': 'okta_group_4', 'num_of_approvals': 1},
        {'resource_id': 'resource_1', 'okta_group_id': 'okta_group_5', 'num_of_approvals': 1},
        {'resource_id': 'resource_2', 'okta_group_id': 'okta_group_4', 'num_of_approvals': 2},
        {'resource_id': 'resource_2', 'okta_group_id': 'okta_group_6', 'num_of_approvals': 2},
    ]

    assert auto_approved_access == expected_auto_approved_access
    assert manual_approved_access == expected_manual_approved_access
