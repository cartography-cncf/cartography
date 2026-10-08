import pytest

from cartography.client.core.tx import load
from cartography.models.github.app_installations import GitHubAppInstallationSchema
from cartography.models.github.orgs import GitHubOrganizationSchema
from cartography.models.github.repos import GitHubRepositorySchema
from cartography.models.github.webhooks import GitHubWebhookSchema
from cartography.rules.data.rules.github_security_configuration import (
    github_actions_permissive_policy,
)
from cartography.rules.data.rules.github_security_configuration import (
    github_app_sensitive_permissions,
)
from cartography.rules.data.rules.github_security_configuration import (
    github_organization_security_settings,
)
from cartography.rules.data.rules.github_security_configuration import (
    github_secret_scanning_disabled,
)
from cartography.rules.data.rules.github_security_configuration import (
    github_webhook_insecure_delivery,
)

UPDATE_TAG = 1
ORG_URL = "https://github.com/simpsoncorp"
GITHUB_RULES = (
    github_secret_scanning_disabled,
    github_organization_security_settings,
    github_actions_permissive_policy,
    github_app_sensitive_permissions,
    github_webhook_insecure_delivery,
)


def _fact(fact_id):
    for rule in GITHUB_RULES:
        fact = rule.get_fact_by_id(fact_id)
        if fact is not None:
            return rule, fact
    raise AssertionError(f"unknown fact {fact_id}")


def _reset(neo4j_session):
    neo4j_session.run(
        "MATCH (n) WHERE n:GitHubOrganization OR n:GitHubRepository "
        "OR n:GitHubAppInstallation OR n:GitHubWebhook DETACH DELETE n",
    )


def _load_orgs(neo4j_session, rows):
    load(
        neo4j_session,
        GitHubOrganizationSchema(),
        [
            {"url": f"{ORG_URL}-{i}", "login": f"simpsoncorp-{i}", **row}
            for i, row in enumerate(rows)
        ],
        lastupdated=UPDATE_TAG,
    )


def _load_repos(neo4j_session, rows):
    load(
        neo4j_session,
        GitHubRepositorySchema(),
        [
            {
                "id": f"{ORG_URL}/repo-{i}",
                "fullname": f"simpsoncorp/repo-{i}",
                "visibility": "private",
                **row,
            }
            for i, row in enumerate(rows)
        ],
        lastupdated=UPDATE_TAG,
    )


def _load_installations(neo4j_session, rows):
    _load_orgs(neo4j_session, [{}])
    load(
        neo4j_session,
        GitHubAppInstallationSchema(),
        [
            {
                "id": f"{ORG_URL}/installations/{i}",
                "app_slug": f"app-{i}",
                "repository_selection": "all",
                **row,
            }
            for i, row in enumerate(rows)
        ],
        lastupdated=UPDATE_TAG,
        org_url=f"{ORG_URL}-0",
    )


def _load_webhooks(neo4j_session, rows):
    _load_orgs(neo4j_session, [{}])
    load(
        neo4j_session,
        GitHubWebhookSchema(),
        [
            {
                "id": f"https://api.github.com/orgs/simpsoncorp/hooks/{i}",
                "hook_id": i,
                "scope": "organization",
                "target_scheme": "https",
                "target_host": f"hooks-{i}.example",
                **row,
            }
            for i, row in enumerate(rows)
        ],
        lastupdated=UPDATE_TAG,
        org_url=f"{ORG_URL}-0",
    )


_SAFE_WEBHOOK = {
    "active": True,
    "has_secret": True,
    "insecure_ssl": False,
    "uses_https": True,
}


@pytest.mark.parametrize(
    "fact_id,loader,positive,negatives,expected_count",
    [
        (
            "github_repository_secret_scanning_disabled",
            _load_repos,
            {"secret_scanning_enabled": False},
            [
                {"secret_scanning_enabled": True},
                {"secret_scanning_enabled": None},
                {"secret_scanning_enabled": False, "archived": True},
            ],
            2,
        ),
        (
            "github_repository_push_protection_disabled",
            _load_repos,
            {"secret_scanning_push_protection_enabled": False},
            [
                {"secret_scanning_push_protection_enabled": True},
                {"secret_scanning_push_protection_enabled": None},
                {
                    "secret_scanning_push_protection_enabled": False,
                    "archived": True,
                },
            ],
            2,
        ),
        (
            "github_org_two_factor_not_required",
            _load_orgs,
            {"two_factor_requirement_enabled": False},
            [
                {"two_factor_requirement_enabled": True},
                {"two_factor_requirement_enabled": None},
            ],
            2,
        ),
        (
            "github_org_base_permission_write",
            _load_orgs,
            {"default_repository_permission": "write"},
            [
                {"default_repository_permission": "read"},
                {"default_repository_permission": "none"},
                {"default_repository_permission": None},
            ],
            3,
        ),
        (
            "github_org_members_can_create_public_repositories",
            _load_orgs,
            {"members_can_create_public_repositories": True},
            [
                {"members_can_create_public_repositories": False},
                {"members_can_create_public_repositories": None},
            ],
            2,
        ),
        (
            "github_org_members_can_fork_private_repositories",
            _load_orgs,
            {"members_can_fork_private_repositories": True},
            [
                {"members_can_fork_private_repositories": False},
                {"members_can_fork_private_repositories": None},
            ],
            2,
        ),
        (
            "github_org_no_verified_domain",
            _load_orgs,
            {"verified_domain_count": 0},
            [{"verified_domain_count": 1}, {"verified_domain_count": None}],
            2,
        ),
        (
            "github_org_notifications_not_restricted",
            _load_orgs,
            {"notification_delivery_restricted": False},
            [
                {"notification_delivery_restricted": True},
                {"notification_delivery_restricted": None},
            ],
            2,
        ),
        (
            "github_org_copilot_public_code_suggestions",
            _load_orgs,
            {"copilot_public_code_suggestions": "allow"},
            [
                {"copilot_public_code_suggestions": "block"},
                {"copilot_public_code_suggestions": None},
            ],
            2,
        ),
        (
            "github_org_actions_all_actions_allowed",
            _load_orgs,
            {"actions_allowed_actions": "all", "actions_enabled_repositories": "all"},
            [
                {
                    "actions_allowed_actions": "selected",
                    "actions_enabled_repositories": "all",
                },
                {
                    "actions_allowed_actions": "all",
                    "actions_enabled_repositories": "none",
                },
                {"actions_allowed_actions": None},
                # Unknown enablement is not a finding.
                {"actions_allowed_actions": "all"},
            ],
            3,
        ),
        (
            "github_org_actions_default_token_write",
            _load_orgs,
            {"actions_default_workflow_permissions": "write"},
            [
                {"actions_default_workflow_permissions": "read"},
                {"actions_default_workflow_permissions": None},
            ],
            2,
        ),
        (
            "github_org_actions_can_approve_pull_requests",
            _load_orgs,
            {"actions_can_approve_pull_request_reviews": True},
            [
                {"actions_can_approve_pull_request_reviews": False},
                {"actions_can_approve_pull_request_reviews": None},
            ],
            2,
        ),
        (
            "github_app_installation_sensitive_write_permissions",
            _load_installations,
            {"enabled": True, "write_permissions": ["checks", "contents"]},
            [
                {"enabled": True, "write_permissions": ["checks", "issues"]},
                {"enabled": True, "write_permissions": []},
                {"enabled": False, "write_permissions": ["administration"]},
                {"enabled": True, "write_permissions": None},
            ],
            3,
        ),
        (
            "github_webhook_without_secret",
            _load_webhooks,
            {**_SAFE_WEBHOOK, "has_secret": False},
            [
                _SAFE_WEBHOOK,
                {**_SAFE_WEBHOOK, "has_secret": None},
                {**_SAFE_WEBHOOK, "has_secret": False, "active": False},
            ],
            2,
        ),
        (
            "github_webhook_insecure_ssl",
            _load_webhooks,
            {**_SAFE_WEBHOOK, "insecure_ssl": True},
            [
                _SAFE_WEBHOOK,
                {**_SAFE_WEBHOOK, "insecure_ssl": None},
                {**_SAFE_WEBHOOK, "insecure_ssl": True, "active": False},
            ],
            2,
        ),
        (
            "github_webhook_not_https",
            _load_webhooks,
            {**_SAFE_WEBHOOK, "uses_https": False, "target_scheme": "http"},
            [
                _SAFE_WEBHOOK,
                {**_SAFE_WEBHOOK, "uses_https": None},
                {**_SAFE_WEBHOOK, "uses_https": False, "active": False},
            ],
            2,
        ),
    ],
)
def test_github_security_configuration_fact(
    neo4j_session, fact_id, loader, positive, negatives, expected_count
):
    # Arrange
    _reset(neo4j_session)
    rule, fact = _fact(fact_id)
    loader(neo4j_session, [positive, *negatives])

    # Act
    rows = neo4j_session.run(fact.cypher_query).data()
    visual = neo4j_session.run(fact.cypher_visual_query).data()
    count = neo4j_session.run(fact.cypher_count_query).single()["count"]
    findings = rule.parse_results(fact, rows)

    # Assert - only the first (positive) asset fails, and every known asset counts.
    assert len(rows) == 1
    assert rows[0]["asset_id"].endswith("0")
    assert len(visual) == 1
    assert visual[0]["n"]["id"] == rows[0]["asset_id"]
    assert count == expected_count
    assert len(findings) == 1
    finding = findings[0]
    assert finding.asset_name
    assert finding.organization
    assert finding.current_value
    assert finding.source == "GitHub"


def test_github_app_sensitive_permissions_lists_matching_permissions(neo4j_session):
    # Arrange
    _reset(neo4j_session)
    _load_installations(
        neo4j_session,
        [
            {
                "enabled": True,
                "write_permissions": ["checks", "contents", "workflows"],
            },
        ],
    )
    rule, fact = _fact("github_app_installation_sensitive_write_permissions")

    # Act
    findings = rule.parse_results(fact, neo4j_session.run(fact.cypher_query).data())

    # Assert
    assert len(findings) == 1
    assert findings[0].current_value == "contents, workflows"
    assert findings[0].repository_selection == "all"
    assert findings[0].organization == "simpsoncorp-0"
