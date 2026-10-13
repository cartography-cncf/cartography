from copy import deepcopy

from cartography.intel.googleworkspace.groups import transform_groups
from tests.data.googleworkspace.api import MOCK_GOOGLEWORKSPACE_GROUPS_RESPONSE
from tests.data.googleworkspace.api import MOCK_GOOGLEWORKSPACE_MEMBERS_BY_GROUP_EMAIL


def test_transform_groups_infers_group_membership_when_type_missing():
    # Arrange
    groups = deepcopy(MOCK_GOOGLEWORKSPACE_GROUPS_RESPONSE)
    group_memberships = deepcopy(MOCK_GOOGLEWORKSPACE_MEMBERS_BY_GROUP_EMAIL)
    del group_memberships["groups/group-engineering"][2]["type"]

    # Act
    transformed_groups, group_member_relationships, group_owner_relationships = (
        transform_groups(
            groups,
            group_memberships,
        )
    )

    # Assert
    assert {group["name"] for group in transformed_groups} == {
        "groups/group-engineering",
        "groups/group-operations",
    }
    assert group_owner_relationships == []
    assert group_member_relationships == [
        {
            "parent_group_id": "groups/group-engineering",
            "subgroup_email": "operations@simpson.corp",
        },
    ]
