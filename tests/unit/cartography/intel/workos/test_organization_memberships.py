from unittest.mock import MagicMock

import cartography.intel.workos.organization_memberships
import tests.data.workos.organization_memberships


class _OrganizationMembershipClient:
    def __init__(self):
        self.calls = []

    def list_organization_memberships(self, **kwargs):
        self.calls.append(kwargs)
        return (
            tests.data.workos.organization_memberships.WORKOS_ORGANIZATION_MEMBERSHIPS
        )


def test_get_workos_organization_memberships_uses_workos8_client_path():
    client = MagicMock()
    client.organization_membership = _OrganizationMembershipClient()
    org_ids = ["org_01HXYZ1234567890ABCDEFGHIJ"]

    result = cartography.intel.workos.organization_memberships.get(client, org_ids)

    assert (
        result
        == tests.data.workos.organization_memberships.WORKOS_ORGANIZATION_MEMBERSHIPS
    )
    assert client.organization_membership.calls == [{"organization_id": org_ids[0]}]
    assert not client.user_management.list_organization_memberships.called
