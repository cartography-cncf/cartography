from copy import deepcopy
from datetime import datetime
from datetime import timezone
from unittest.mock import Mock

import pytest
import requests

from cartography.intel.jira import automation
from cartography.intel.jira.access import resource_id
from cartography.intel.jira.automation import get
from cartography.intel.jira.automation import parse_outgoing_target
from cartography.intel.jira.automation import transform
from cartography.intel.jira.util import JiraClient
from tests.data.jira.access import CLOUD_ID
from tests.data.jira.automation import FAKE_SECRET
from tests.data.jira.automation import GITHUB_API_URL
from tests.data.jira.automation import GITHUB_REPO_ID
from tests.data.jira.automation import RULE_DETAIL_GLOBAL
from tests.data.jira.automation import RULE_DETAIL_PROJECT
from tests.data.jira.automation import RULE_UUID_GLOBAL
from tests.data.jira.automation import RULE_UUID_PROJECT
from tests.data.jira.automation import SLACK_TEAM_ID
from tests.data.jira.automation import SLACK_TOKEN_PART
from tests.data.jira.automation import SLACK_WEBHOOK_URL
from tests.data.jira.automation import SMART_VALUE_URL
from tests.data.jira.automation import SUMMARY_PAGE_1
from tests.data.jira.automation import SUMMARY_PAGE_2
from tests.data.jira.automation import UNRELATED_WEBHOOK_URL


def _http_error(status: int) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status
    return requests.HTTPError(f"HTTP {status}", response=response)


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://api.github.com/repos/Example-Org/Repo-Name/issues",
            ("api.github.com", "https://github.com/Example-Org/Repo-Name", None),
        ),
        (
            "https://api.github.com/users/octocat",
            ("api.github.com", None, None),
        ),
        (
            "https://hooks.slack.com/services/T01234567/B09876543/secretToken123",
            ("hooks.slack.com", None, "T01234567"),
        ),
        (
            "https://hooks.slack.com/api/chat.postMessage",
            ("hooks.slack.com", None, None),
        ),
        ("not-a-url", ("", None, None)),
        ("ftp://example.com/resource", ("", None, None)),
        ("", ("", None, None)),
        ("https://{{webhook.host}}/hook", ("", None, None)),
        ("https://api.github.com/repos/{{owner}}/{{repo}}", ("", None, None)),
        ("{{baseUrl}}/hook", ("", None, None)),
        (
            "HTTPS://API.GITHUB.COM/repos/Octo/Repo",
            ("api.github.com", "https://github.com/Octo/Repo", None),
        ),
    ],
)
def test_parse_outgoing_target(url, expected):
    assert parse_outgoing_target(url) == expected


def test_transform_extracts_fields_and_strips_secrets():
    # Arrange
    rules = [
        deepcopy(RULE_DETAIL_PROJECT["rule"]),
        deepcopy(RULE_DETAIL_GLOBAL["rule"]),
    ]

    # Act
    result = transform(rules, CLOUD_ID)

    # Assert
    assert result == [
        {
            "id": resource_id(CLOUD_ID, "automation_rule", RULE_UUID_PROJECT),
            "uuid": RULE_UUID_PROJECT,
            "name": "Notify GitHub and Slack on issue create",
            "state": "ENABLED",
            "description": "Project-scoped rule",
            "write_access_type": "OWNER_ONLY",
            "created": datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc),
            "updated": datetime(2023, 11, 14, 22, 15, 0, tzinfo=timezone.utc),
            "trigger_type": "jira.issue.event.trigger:created",
            "has_incoming_webhook_trigger": False,
            "is_global": False,
            "outgoing_request_hosts": ["api.github.com", "hooks.slack.com"],
            "outgoing_request_count": 2,
            "actor_user_id": resource_id(CLOUD_ID, "user", "user-1"),
            "project_ids": [resource_id(CLOUD_ID, "project", "100")],
            "github_repository_ids": [GITHUB_REPO_ID],
            "slack_team_ids": [SLACK_TEAM_ID],
        },
        {
            "id": resource_id(CLOUD_ID, "automation_rule", RULE_UUID_GLOBAL),
            "uuid": RULE_UUID_GLOBAL,
            "name": "Global incoming webhook relay",
            "state": "DISABLED",
            "description": "Global rule with incoming webhook",
            "write_access_type": "ADMIN_ONLY",
            "created": datetime(2023, 11, 14, 22, 16, 40, tzinfo=timezone.utc),
            "updated": datetime(2023, 11, 14, 22, 18, 20, tzinfo=timezone.utc),
            "trigger_type": "jira.incoming.webhook",
            "has_incoming_webhook_trigger": True,
            "is_global": True,
            "outgoing_request_hosts": ["hooks.example.com"],
            "outgoing_request_count": 2,
            "actor_user_id": None,
            "project_ids": [],
            "github_repository_ids": [],
            "slack_team_ids": [],
        },
    ]

    serialized = repr(result)
    for forbidden in (
        FAKE_SECRET,
        SLACK_TOKEN_PART,
        SLACK_WEBHOOK_URL,
        GITHUB_API_URL,
        UNRELATED_WEBHOOK_URL,
        SMART_VALUE_URL,
    ):
        assert forbidden not in serialized


def test_get_follows_relative_next_link_and_fetches_details():
    # Arrange
    client = JiraClient(
        CLOUD_ID,
        "reader@example.com",
        "test-token",
        site_url="https://example.atlassian.net",
    )
    summary_url = f"https://api.atlassian.com/automation/public/jira/{CLOUD_ID}/rest/v1/rule/summary"
    responses = {
        (summary_url, (("limit", 100),)): deepcopy(SUMMARY_PAGE_1),
        (f"{summary_url}?cursor=cursor-page-2&limit=100", ()): deepcopy(SUMMARY_PAGE_2),
        (
            f"https://api.atlassian.com/automation/public/jira/{CLOUD_ID}/rest/v1/rule/{RULE_UUID_PROJECT}",
            (("redactSensitiveFields", "true"),),
        ): deepcopy(RULE_DETAIL_PROJECT),
        (
            f"https://api.atlassian.com/automation/public/jira/{CLOUD_ID}/rest/v1/rule/{RULE_UUID_GLOBAL}",
            (("redactSensitiveFields", "true"),),
        ): deepcopy(RULE_DETAIL_GLOBAL),
    }

    def fake_get_automation(url, **params):
        key = (url, tuple(sorted(params.items())))
        return responses[key]

    client.get_automation = Mock(side_effect=fake_get_automation)

    # Act
    result = get(client)

    # Assert
    assert result is not None
    rules, is_complete = result
    assert [r["uuid"] for r in rules] == [RULE_UUID_PROJECT, RULE_UUID_GLOBAL]
    assert is_complete is True


def test_get_raises_on_repeated_cursor():
    # Arrange
    client = JiraClient(CLOUD_ID, "reader@example.com", "test-token")
    page = deepcopy(SUMMARY_PAGE_1)
    client.get_automation = Mock(return_value=page)

    # Act and assert
    with pytest.raises(ValueError, match="repeated cursor"):
        get(client)


@pytest.mark.parametrize("status", [401, 403, 404])
def test_get_skips_without_detail_calls_on_auth_or_missing_summary(status):
    # Arrange
    client = JiraClient(CLOUD_ID, "reader@example.com", "test-token")
    client.get_automation = Mock(side_effect=_http_error(status))

    # Act
    result = get(client)

    # Assert
    assert result is None
    assert client.get_automation.call_count == 1


def test_get_raises_on_detail_server_error():
    # Arrange
    client = JiraClient(CLOUD_ID, "reader@example.com", "test-token")
    page = deepcopy(SUMMARY_PAGE_1)
    page["links"]["next"] = None
    client.get_automation = Mock(side_effect=[page, _http_error(500)])

    # Act and assert
    with pytest.raises(requests.HTTPError):
        get(client)


@pytest.mark.parametrize("status", [403, 404])
def test_get_skips_rule_whose_detail_is_unreadable_and_marks_incomplete(status):
    # Arrange: the second rule was deleted (404) or hidden (403) after the summary call
    client = JiraClient(CLOUD_ID, "reader@example.com", "test-token")
    page = deepcopy(SUMMARY_PAGE_1)
    page["links"]["next"] = None
    page["data"] = [{"uuid": RULE_UUID_PROJECT}, {"uuid": RULE_UUID_GLOBAL}]
    client.get_automation = Mock(
        side_effect=[page, deepcopy(RULE_DETAIL_PROJECT), _http_error(status)]
    )

    # Act
    result = get(client)

    # Assert
    assert result is not None
    rules, is_complete = result
    assert [r["uuid"] for r in rules] == [RULE_UUID_PROJECT]
    assert is_complete is False


@pytest.mark.parametrize(
    ("scope_aris", "expected_global"),
    [
        ([f"ari:cloud:jira::site/{CLOUD_ID}"], True),
        ([f"ari:cloud:jira:{CLOUD_ID}:site/{CLOUD_ID}"], True),
        ([f"ari:cloud:jira-software::site/{CLOUD_ID}"], False),
        ([f"ari:cloud:jira-core::site/{CLOUD_ID}"], False),
        ([f"ari:cloud:jira:{CLOUD_ID}:project/100"], False),
        (["unexpected-scope"], False),
        ([], False),
    ],
)
def test_transform_is_global_only_for_site_scope(scope_aris, expected_global):
    # Arrange
    rule = deepcopy(RULE_DETAIL_GLOBAL["rule"])
    rule["ruleScopeARIs"] = scope_aris

    # Act
    result = transform([rule], CLOUD_ID)

    # Assert
    assert result[0]["is_global"] is expected_global


def test_sync_skips_cleanup_when_some_rules_were_unreadable(monkeypatch):
    # Arrange
    client = JiraClient(CLOUD_ID, "reader@example.com", "test-token")
    monkeypatch.setattr(
        automation,
        "get",
        Mock(return_value=([deepcopy(RULE_DETAIL_PROJECT["rule"])], False)),
    )
    load = Mock()
    graph_job = Mock()
    monkeypatch.setattr(automation, "load", load)
    monkeypatch.setattr(automation, "GraphJob", graph_job)

    # Act
    automation.sync(Mock(), client, 123)

    # Assert
    load.assert_called_once()
    graph_job.from_node_schema.assert_not_called()


def test_transform_leaves_missing_timestamps_empty():
    # Arrange
    rule = deepcopy(RULE_DETAIL_GLOBAL["rule"])
    rule.pop("created")
    rule["updated"] = None

    # Act
    result = transform([rule], CLOUD_ID)

    # Assert
    assert result[0]["created"] is None
    assert result[0]["updated"] is None


def test_transform_ignores_non_dict_component_value():
    # Arrange
    rule = deepcopy(RULE_DETAIL_PROJECT["rule"])
    rule["components"] = [
        {"type": "jira.issue.outgoing.webhook", "value": "not-a-dict"},
    ]

    # Act
    result = transform([rule], CLOUD_ID)

    # Assert
    assert result[0]["outgoing_request_count"] == 1
    assert result[0]["outgoing_request_hosts"] == []
    assert result[0]["github_repository_ids"] == []
    assert result[0]["slack_team_ids"] == []
