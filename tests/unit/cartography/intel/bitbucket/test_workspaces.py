from cartography.intel.bitbucket.workspaces import transform_workspaces
from tests.data.bitbucket.workspaces import MOCK_WORKSPACES


def test_transform_workspaces():
    result = transform_workspaces(MOCK_WORKSPACES["values"])

    assert result == [
        {
            "id": "workspace-uuid-1",
            "slug": "my-workspace",
            "name": "My Workspace",
            "is_private": True,
            "created_on": "2020-01-01T00:00:00.000000+00:00",
            "link_html": "https://bitbucket.org/my-workspace",
        },
    ]
