from unittest.mock import MagicMock

import requests

from cartography.intel.infisical import api
from cartography.intel.infisical import projects
from tests.data.infisical import API_URL
from tests.data.infisical import ORGANIZATION_ID
from tests.data.infisical import PROJECTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def _sync(neo4j_session, session, update_tag: int) -> None:
    projects.sync(
        neo4j_session,
        session,
        API_URL,
        ORGANIZATION_ID,
        update_tag,
        {
            "UPDATE_TAG": update_tag,
            "INFISICAL_ORGANIZATION_ID": ORGANIZATION_ID,
        },
    )


def test_sync_projects_loads_graph_and_cleans_up_stale_projects(
    neo4j_session,
    mocker,
) -> None:
    # Arrange
    get_projects = mocker.patch.object(api, "get_projects", return_value=PROJECTS)
    session = MagicMock(spec=requests.Session)

    # Act
    _sync(neo4j_session, session, 123456789)

    # Assert
    assert check_nodes(
        neo4j_session,
        "InfisicalOrganization",
        ["id", "api_url"],
    ) == {(ORGANIZATION_ID, API_URL)}
    assert check_nodes(
        neo4j_session,
        "InfisicalProject",
        ["id", "name", "slug", "organization_id"],
    ) == {
        ("project-1", "Payments", "payments", ORGANIZATION_ID),
        ("project-2", "Data Platform", "data-platform", ORGANIZATION_ID),
    }
    assert check_rels(
        neo4j_session,
        "InfisicalOrganization",
        "id",
        "InfisicalProject",
        "id",
        "RESOURCE",
    ) == {
        (ORGANIZATION_ID, "project-1"),
        (ORGANIZATION_ID, "project-2"),
    }

    # Arrange
    get_projects.return_value = PROJECTS[:1]

    # Act
    _sync(neo4j_session, session, 223456789)

    # Assert
    assert check_nodes(
        neo4j_session,
        "InfisicalProject",
        ["id"],
    ) == {("project-1",)}
    assert check_rels(
        neo4j_session,
        "InfisicalOrganization",
        "id",
        "InfisicalProject",
        "id",
        "RESOURCE",
    ) == {(ORGANIZATION_ID, "project-1")}
