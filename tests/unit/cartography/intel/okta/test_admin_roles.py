from cartography.intel.okta.roles import transform_group_roles_data
from cartography.intel.okta.roles import transform_user_roles_data
from tests.data.okta.adminroles import LIST_ASSIGNED_GROUP_ROLE_RESPONSE
from tests.data.okta.adminroles import LIST_ASSIGNED_USER_ROLE_RESPONSE


def test_transform_user_roles():
    org_id = "example_org"
    result = transform_user_roles_data(LIST_ASSIGNED_USER_ROLE_RESPONSE, org_id)

    expected = [
        {
            "id": "example_org-APP_ADMIN",
            "label": "Application Administrator",
            "type": "APP_ADMIN",
        },
        {
            "id": "example_org-HELP_DESK_ADMIN",
            "label": "Help Desk Administrator",
            "type": "HELP_DESK_ADMIN",
        },
    ]

    assert result == expected


def test_transform_group_roles():
    org_id = "example_org"
    result = transform_group_roles_data(LIST_ASSIGNED_GROUP_ROLE_RESPONSE, org_id)

    expected = [
        {
            "id": "example_org-APP_ADMIN",
            "label": "Application Administrator",
            "type": "APP_ADMIN",
        },
        {
            "id": "example_org-HELP_DESK_ADMIN",
            "label": "Help Desk Administrator",
            "type": "HELP_DESK_ADMIN",
        },
    ]

    assert result == expected
