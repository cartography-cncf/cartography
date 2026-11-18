from cartography.intel.bitbucket.projects import transform_projects
from tests.data.bitbucket.projects import MOCK_PROJECTS


def test_transform_projects():
    result = transform_projects(MOCK_PROJECTS["values"])

    assert result == [
        {
            "id": "project-uuid-1",
            "key": "PROJ",
            "name": "Project One",
            "description": "The first project",
            "is_private": True,
            "created_on": "2020-01-01T00:00:00.000000+00:00",
            "updated_on": "2020-02-01T00:00:00.000000+00:00",
            "link_html": "https://bitbucket.org/my-workspace/workspace/projects/PROJ",
        },
    ]
