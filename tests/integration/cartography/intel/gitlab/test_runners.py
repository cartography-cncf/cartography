"""Integration tests for GitLab runners module."""

from unittest.mock import patch

import requests

from cartography.intel.gitlab.runners import sync_gitlab_runners
from tests.data.gitlab.runners import GET_GROUP_RUNNERS_LIST
from tests.data.gitlab.runners import GET_INSTANCE_RUNNERS_LIST
from tests.data.gitlab.runners import GET_PROJECT_RUNNERS_LIST
from tests.data.gitlab.runners import RUNNER_DETAILS
from tests.data.gitlab.runners import TEST_GITLAB_URL
from tests.data.gitlab.runners import TEST_GROUP_ID
from tests.data.gitlab.runners import TEST_ORG_ID
from tests.data.gitlab.runners import TEST_PROJECT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _create_org_group_project(neo4j_session):
    # Wipe shared state from prior tests in this module — neo4j_session is
    # module-scoped, so without this the 403-tolerance test inherits runners
    # loaded by an earlier test.
    neo4j_session.run("MATCH (n) DETACH DELETE n;")
    neo4j_session.run(
        """
        MERGE (o:GitLabOrganization{id: $org_id})
        ON CREATE SET o.firstseen = timestamp()
        SET o.lastupdated = $update_tag, o.gitlab_url = $gitlab_url
        MERGE (g:GitLabGroup{id: $group_id, gitlab_url: $gitlab_url})
        ON CREATE SET g.firstseen = timestamp()
        SET g.lastupdated = $update_tag
        MERGE (p:GitLabProject{id: $project_id, gitlab_url: $gitlab_url})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $update_tag
        """,
        org_id=TEST_ORG_ID,
        group_id=TEST_GROUP_ID,
        project_id=TEST_PROJECT_ID,
        gitlab_url=TEST_GITLAB_URL,
        update_tag=TEST_UPDATE_TAG,
    )


def _common_job_parameters():
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORGANIZATION_ID": TEST_ORG_ID,
        "org_id": TEST_ORG_ID,
        "gitlab_url": TEST_GITLAB_URL,
    }


def _http_error(status_code: int) -> requests.exceptions.HTTPError:
    response = requests.Response()
    response.status_code = status_code
    return requests.exceptions.HTTPError(response=response)


def _patched_paginated(endpoint, **_kwargs):
    """Pick the right list response based on the endpoint."""
    if endpoint == "/api/v4/runners/all":
        return list(GET_INSTANCE_RUNNERS_LIST)
    if endpoint == f"/api/v4/groups/{TEST_GROUP_ID}/runners":
        return list(GET_GROUP_RUNNERS_LIST)
    if endpoint == f"/api/v4/projects/{TEST_PROJECT_ID}/runners":
        return list(GET_PROJECT_RUNNERS_LIST)
    return []


@patch("cartography.intel.gitlab.runners.get_single")
@patch("cartography.intel.gitlab.runners.get_paginated")
def test_sync_runners_creates_all_three_scopes(
    mock_get_paginated, mock_get_single, neo4j_session
):
    _create_org_group_project(neo4j_session)
    mock_get_paginated.side_effect = (
        lambda _url, _tok, endpoint, **kw: _patched_paginated(endpoint, **kw)
    )
    mock_get_single.side_effect = lambda _url, _tok, endpoint: RUNNER_DETAILS[
        int(endpoint.rsplit("/", 1)[1])
    ]

    sync_gitlab_runners(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_UPDATE_TAG,
        _common_job_parameters(),
        groups=[{"id": TEST_GROUP_ID}],
        projects=[{"id": TEST_PROJECT_ID}],
    )

    expected_runners = {
        (1001, "instance_type", True, "not_protected"),
        (2001, "group_type", False, "ref_protected"),
        (3001, "project_type", True, "not_protected"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "GitLabRunner",
            ["id", "runner_type", "run_untagged", "access_level"],
        )
        == expected_runners
    )

    # Instance runner -> Organization
    assert check_rels(
        neo4j_session,
        "GitLabOrganization",
        "id",
        "GitLabRunner",
        "id",
        "RESOURCE",
    ) == {(TEST_ORG_ID, 1001)}

    # Group runner -> Group
    assert check_rels(
        neo4j_session,
        "GitLabGroup",
        "id",
        "GitLabRunner",
        "id",
        "RESOURCE",
    ) == {(TEST_GROUP_ID, 2001)}

    # Project runner -> Project
    assert check_rels(
        neo4j_session,
        "GitLabProject",
        "id",
        "GitLabRunner",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, 3001)}


@patch("cartography.intel.gitlab.runners.get_single")
@patch("cartography.intel.gitlab.runners.get_paginated")
def test_sync_runners_tolerates_403_on_instance_scope(
    mock_get_paginated, mock_get_single, neo4j_session
):
    """A token without admin scope should not break the sync."""
    _create_org_group_project(neo4j_session)

    def paginated_side_effect(_url, _tok, endpoint, **_kw):
        if endpoint == "/api/v4/runners/all":
            raise _http_error(403)
        return _patched_paginated(endpoint)

    mock_get_paginated.side_effect = paginated_side_effect
    mock_get_single.side_effect = lambda _url, _tok, endpoint: RUNNER_DETAILS[
        int(endpoint.rsplit("/", 1)[1])
    ]

    sync_gitlab_runners(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_UPDATE_TAG,
        _common_job_parameters(),
        groups=[{"id": TEST_GROUP_ID}],
        projects=[{"id": TEST_PROJECT_ID}],
    )

    # No instance-level runner created
    runner_ids = {row[0] for row in check_nodes(neo4j_session, "GitLabRunner", ["id"])}
    assert 1001 not in runner_ids
    # But group + project runners are still loaded
    assert 2001 in runner_ids
    assert 3001 in runner_ids
