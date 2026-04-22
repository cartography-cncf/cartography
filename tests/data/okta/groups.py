from unittest.mock import MagicMock

from okta.models.group import Group
from okta.models.group_profile import GroupProfile
from okta.models.okta_user_group_profile import OktaUserGroupProfile


def create_test_group():
    """Create a mock OktaGroup object for testing."""
    group = MagicMock(spec=Group)
    group.id = "group_id_value"
    group.created = "2019-01-01T00:00:01.000Z"
    group.last_membership_updated = "2019-01-01T00:00:01.000Z"
    group.last_updated = "2019-01-01T00:00:01.000Z"
    group.object_class = ["okta:user_group"]

    # Type enum
    group.type = MagicMock()
    group.type.value = "OKTA_GROUP"

    # Profile — mirror the SDK shape: GroupProfile is a discriminated-union
    # wrapper whose concrete fields live on `actual_instance`
    # (OktaUserGroupProfile | OktaActiveDirectoryGroupProfile).
    group.profile = MagicMock(spec=GroupProfile)
    group.profile.actual_instance = MagicMock(spec=OktaUserGroupProfile)
    group.profile.actual_instance.name = "group_profile_name_value"
    group.profile.actual_instance.description = "group_profile_description_value"

    return group


def create_test_group_member():
    """Create a mock OktaUser object representing a group member."""
    member = MagicMock()
    member.id = "member_user_id"
    return member


def create_test_group_role():
    """Create a mock OktaGroupRole object for testing."""
    role = MagicMock()
    role.id = "role_id_value"
    role.created = "2019-01-01T00:00:01.000Z"
    role.description = "Role description"
    role.label = "Role Label"
    role.last_updated = "2019-01-01T00:00:01.000Z"

    role.assignment_type = MagicMock()
    role.assignment_type.value = "GROUP"

    role.status = MagicMock()
    role.status.value = "ACTIVE"

    role.type = MagicMock()
    role.type.value = "APP_ADMIN"

    return role
