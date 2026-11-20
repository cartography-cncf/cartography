from copy import deepcopy
from unittest.mock import patch

import pytest

from cartography.intel.github import codeowners
from cartography.intel.github import dependabot_alerts
from cartography.intel.github import repos
from cartography.intel.github import supply_chain
from cartography.intel.github import webhooks
from cartography.intel.github.util import PaginatedGraphqlData
from tests.data.github.dependabot_alerts import GET_DEPENDABOT_ALERTS
from tests.data.github.repos import GET_REPOS

ORG_URL = "https://github.com/simpsoncorp"
REPO_URL = f"{ORG_URL}/sample_repo"
ARCHIVED_URL = f"{ORG_URL}/SampleRepo2"
API_URL = "https://api.github.com/graphql"


def test_dependabot_excludes_archived_alerts_without_filtering_inactive_repos():
    # Arrange
    alerts = deepcopy(GET_DEPENDABOT_ALERTS)
    for alert in alerts:
        alert["repository"]["pushed_at"] = "2000-01-01T00:00:00Z"

    # Act
    result = dependabot_alerts.transform(alerts, excluded_repo_urls={ARCHIVED_URL})

    # Assert
    assert {alert["repository_url"] for alert in result["alerts"]} == {REPO_URL}
    assert len(result["alerts"]) == 2


@pytest.mark.parametrize("flag", ["archived", "disabled"])
def test_dependabot_uses_payload_archive_flags_when_inventory_omits_repo(flag):
    # Arrange
    alert = deepcopy(GET_DEPENDABOT_ALERTS[0])
    alert["repository"][flag] = True

    # Act
    incremental = dependabot_alerts.transform([alert], excluded_repo_urls=set())
    full = dependabot_alerts.transform([alert])

    # Assert
    assert incremental == {"alerts": [], "users": []}
    assert len(full["alerts"]) == 1


def test_webhooks_fetches_inactive_but_not_excluded_repositories():
    # Arrange
    repositories = [
        {"fullname": "simpsoncorp/sample_repo", "url": REPO_URL},
        {"fullname": "simpsoncorp/SampleRepo2", "url": ARCHIVED_URL},
    ]
    with (
        patch.object(webhooks, "get_organization_webhooks", return_value=[]),
        patch.object(webhooks, "get_repository_webhooks", return_value=[]) as fetch,
    ):
        # Act
        _, repo_hooks, complete = webhooks.get(
            "token",
            API_URL,
            "simpsoncorp",
            repositories,
            excluded_repo_urls={ARCHIVED_URL},
        )

    # Assert
    fetch.assert_called_once_with("token", API_URL, "simpsoncorp/sample_repo")
    assert repo_hooks == {REPO_URL: []}
    assert complete is True


def test_codeowners_excludes_only_archived_repositories():
    # Arrange
    repositories = [
        {"id": REPO_URL, "owner_org_id": ORG_URL},
        {"id": ARCHIVED_URL, "owner_org_id": ORG_URL},
    ]

    # Act
    result = codeowners.transform_repositories_for_codeowners(
        repositories,
        ORG_URL,
        excluded_repo_urls={ARCHIVED_URL},
    )

    # Assert
    assert [repo["repo_url"] for repo in result] == [REPO_URL]


@pytest.mark.parametrize("flag", ["isArchived", "isDisabled"])
def test_archived_repo_transform_retains_inventory_without_detail_refresh(flag):
    # Arrange
    repo = deepcopy(GET_REPOS[0])
    repo["isArchived"] = False
    repo["isDisabled"] = False
    repo[flag] = True
    repo["branchProtectionRules"] = {"nodes": [{"id": "stale-rule"}]}

    # Act
    result = repos.transform([repo], {}, {}, skip_archived_repos=True)

    # Assert
    assert [item["id"] for item in result["repos"]] == [repo["url"]]
    assert result["manifests"] == []
    assert result["dependencies"] == []
    assert result["python_requirements"] == []
    assert result["branch_protection_rules"] == []
    assert result["rulesets"] == []


def test_privileged_enrichment_avoids_archived_repository_ruleset_requests():
    # Arrange
    repositories = [
        {"name": "sample_repo", "url": REPO_URL},
        {"name": "SampleRepo2", "url": ARCHIVED_URL},
    ]
    with (
        patch.object(
            repos,
            "fetch_all",
            return_value=(PaginatedGraphqlData(repositories, []), None),
        ),
        patch.object(repos, "fetch_all_rest_api_pages", return_value=[]) as fetch,
    ):
        # Act
        result = repos.get_repo_privileged_details_by_url(
            "token",
            API_URL,
            "simpsoncorp",
            excluded_repo_urls={ARCHIVED_URL},
        )

    # Assert
    assert set(result) == {REPO_URL}
    assert fetch.call_count == 1
    assert fetch.call_args.args[2] == "/repos/simpsoncorp/sample_repo/rulesets"


def test_dockerfile_fetch_excludes_archived_repositories():
    # Arrange
    repositories = [
        {"url": REPO_URL, "nameWithOwner": "simpsoncorp/sample_repo"},
        {"url": ARCHIVED_URL, "nameWithOwner": "simpsoncorp/SampleRepo2"},
    ]
    items = [
        {
            "path": "Dockerfile",
            "repository": {"full_name": "simpsoncorp/SampleRepo2"},
        },
    ]
    with (
        patch.object(supply_chain, "search_dockerfiles_in_org", return_value=items),
        patch.object(supply_chain, "get_file_content") as fetch,
    ):
        # Act
        result = supply_chain.get_dockerfiles_for_repos(
            "token",
            repositories,
            "simpsoncorp",
            excluded_repo_urls={ARCHIVED_URL},
        )

    # Assert
    fetch.assert_not_called()
    assert result == []
