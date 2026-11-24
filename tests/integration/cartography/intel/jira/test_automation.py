from collections.abc import Iterator
from copy import deepcopy
from typing import Any
from unittest.mock import Mock

import neo4j
import pytest
import requests

from cartography.intel.jira.access import resource_id
from cartography.intel.jira.automation import sync
from cartography.intel.jira.util import JiraClient
from tests.data.jira.access import CLOUD_ID
from tests.data.jira.automation import FAKE_SECRET
from tests.data.jira.automation import GITHUB_REPO_ID
from tests.data.jira.automation import RULE_DETAIL_GLOBAL
from tests.data.jira.automation import RULE_DETAIL_PROJECT
from tests.data.jira.automation import RULE_UUID_GLOBAL
from tests.data.jira.automation import RULE_UUID_PROJECT
from tests.data.jira.automation import SLACK_TEAM_ID
from tests.data.jira.automation import SUMMARY_PAGE_1
from tests.data.jira.automation import SUMMARY_PAGE_2
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


@pytest.fixture(autouse=True)  # type: ignore[misc]
def clean_graph(neo4j_session: neo4j.Session) -> Iterator[None]:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    try:
        yield
    finally:
        neo4j_session.run("MATCH (n) DETACH DELETE n")


def _seed_target_nodes(neo4j_session: neo4j.Session) -> None:
    user_id = resource_id(CLOUD_ID, "user", "user-1")
    project_id = resource_id(CLOUD_ID, "project", "100")
    neo4j_session.run(
        """
        MERGE (:JiraTenant {id: $cloud_id})
        MERGE (:JiraUser {id: $user_id, account_id: 'user-1'})
        MERGE (:JiraProject {id: $project_id, project_id: '100'})
        MERGE (:GitHubRepository {id: $github_repo_id})
        MERGE (:SlackTeam {id: $slack_team_id})
        """,
        cloud_id=CLOUD_ID,
        user_id=user_id,
        project_id=project_id,
        github_repo_id=GITHUB_REPO_ID,
        slack_team_id=SLACK_TEAM_ID,
    )


def _mock_client(pages: list[dict], details: dict[str, dict]) -> JiraClient:
    client = Mock(spec=JiraClient)
    client.cloud_id = CLOUD_ID
    client.automation_base_url = (
        f"https://api.atlassian.com/automation/public/jira/{CLOUD_ID}/rest/v1"
    )
    summary_url = f"{client.automation_base_url}/rule/summary"

    def get_automation(url: str, **params: object) -> dict:
        if url == summary_url:
            return deepcopy(pages[0])
        if url.startswith(f"{summary_url}?"):
            return deepcopy(pages[1])
        for rule_uuid, detail in details.items():
            if url == f"{client.automation_base_url}/rule/{rule_uuid}":
                return deepcopy(detail)
        raise AssertionError(f"Unexpected URL: {url}")

    client.get_automation.side_effect = get_automation
    return client


def test_sync_automation_rules_and_cleanup(neo4j_session: neo4j.Session) -> None:
    # Arrange
    _seed_target_nodes(neo4j_session)
    client = _mock_client(
        [SUMMARY_PAGE_1, SUMMARY_PAGE_2],
        {
            RULE_UUID_PROJECT: RULE_DETAIL_PROJECT,
            RULE_UUID_GLOBAL: RULE_DETAIL_GLOBAL,
        },
    )

    # Act
    sync(neo4j_session, client, 1)

    # Assert timestamps are stored as native datetimes, not epoch milliseconds
    types = neo4j_session.run(
        "MATCH (r:JiraAutomationRule) "
        "RETURN collect(DISTINCT valueType(r.created)) + "
        "collect(DISTINCT valueType(r.updated)) AS types"
    ).single()["types"]
    assert set(types) == {"ZONED DATETIME NOT NULL"}

    # Assert all five relationship kinds
    assert check_rels(
        neo4j_session,
        "JiraTenant",
        "id",
        "JiraAutomationRule",
        "uuid",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (CLOUD_ID, RULE_UUID_PROJECT),
        (CLOUD_ID, RULE_UUID_GLOBAL),
    }
    assert check_rels(
        neo4j_session,
        "JiraAutomationRule",
        "uuid",
        "JiraUser",
        "account_id",
        "RUNS_AS",
        rel_direction_right=True,
    ) == {(RULE_UUID_PROJECT, "user-1")}
    assert check_rels(
        neo4j_session,
        "JiraAutomationRule",
        "uuid",
        "JiraProject",
        "project_id",
        "APPLIES_TO",
        rel_direction_right=True,
    ) == {(RULE_UUID_PROJECT, "100")}
    assert check_rels(
        neo4j_session,
        "JiraAutomationRule",
        "uuid",
        "GitHubRepository",
        "id",
        "SENDS_REQUESTS_TO",
        rel_direction_right=True,
    ) == {(RULE_UUID_PROJECT, GITHUB_REPO_ID)}
    assert check_rels(
        neo4j_session,
        "JiraAutomationRule",
        "uuid",
        "SlackTeam",
        "id",
        "SENDS_REQUESTS_TO",
        rel_direction_right=True,
    ) == {(RULE_UUID_PROJECT, SLACK_TEAM_ID)}

    # Assert no secret or full Slack webhook URL is stored on any node property
    rows = neo4j_session.run(
        "MATCH (r:JiraAutomationRule) RETURN properties(r) AS props"
    ).data()
    assert len(rows) == 2
    serialized_props = repr(rows)
    assert FAKE_SECRET not in serialized_props
    assert "hooks.slack.com/services" not in serialized_props

    # Act 2: second sync removes stale global rule
    single_page: dict[str, Any] = deepcopy(SUMMARY_PAGE_1)
    single_page["links"]["next"] = None
    client_v2 = _mock_client([single_page], {RULE_UUID_PROJECT: RULE_DETAIL_PROJECT})
    sync(neo4j_session, client_v2, 2)

    assert check_nodes(neo4j_session, "JiraAutomationRule", ["uuid"]) == {
        (RULE_UUID_PROJECT,)
    }

    # Act 3: 403 on summary preserves existing nodes
    forbidden_response = requests.Response()
    forbidden_response.status_code = 403
    client_403 = Mock(spec=JiraClient)
    client_403.cloud_id = CLOUD_ID
    client_403.automation_base_url = client.automation_base_url
    client_403.get_automation.side_effect = requests.HTTPError(
        "Forbidden", response=forbidden_response
    )
    sync(neo4j_session, client_403, 3)

    assert check_nodes(neo4j_session, "JiraAutomationRule", ["uuid"]) == {
        (RULE_UUID_PROJECT,)
    }
