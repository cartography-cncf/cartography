"""
Unit tests for GitHub repository rulesets transformation logic.
"""

import json

from cartography.intel.github.repos import _transform_rulesets
from tests.data.github.rulesets import NO_RULESETS
from tests.data.github.rulesets import RULESET_BOOLEAN_ACTORS
from tests.data.github.rulesets import RULESET_EVALUATE
from tests.data.github.rulesets import RULESET_PRODUCTION
from tests.data.github.rulesets import RULESET_TAGS
from tests.data.github.rulesets import RULESETS_DATA
from tests.data.github.rulesets import SINGLE_RULESET

TEST_REPO_URL = "https://github.com/test-org/test-repo"


def test_transform_rulesets_with_multiple_rulesets():
    """
    Test that multiple rulesets are correctly transformed from GitHub API format.
    """
    output_rulesets = []
    output_rules = []
    output_bypass_actors = []

    _transform_rulesets(
        RULESETS_DATA,
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
        output_bypass_actors,
    )

    assert len(output_rulesets) == 3
    assert len(output_rules) == 5
    assert len(output_bypass_actors) == 2

    ruleset_ids = {r["id"] for r in output_rulesets}
    expected_ids = {
        RULESET_PRODUCTION["id"],
        RULESET_EVALUATE["id"],
        RULESET_TAGS["id"],
    }
    assert ruleset_ids == expected_ids


def test_transform_rulesets_field_mapping():
    """
    Test that ruleset fields are correctly mapped from camelCase to snake_case.
    """
    output_rulesets = []
    output_rules = []
    output_bypass_actors = []

    _transform_rulesets(
        SINGLE_RULESET,
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
        output_bypass_actors,
    )

    assert len(output_rulesets) == 1
    ruleset = output_rulesets[0]

    assert ruleset["id"] == RULESET_PRODUCTION["id"]
    assert ruleset["database_id"] == RULESET_PRODUCTION["databaseId"]
    assert ruleset["name"] == RULESET_PRODUCTION["name"]
    assert ruleset["target"] == RULESET_PRODUCTION["target"]
    assert ruleset["enforcement"] == RULESET_PRODUCTION["enforcement"]
    assert ruleset["created_at"] == RULESET_PRODUCTION["createdAt"]
    assert ruleset["updated_at"] == RULESET_PRODUCTION["updatedAt"]
    assert ruleset["conditions_ref_name_include"] == ["~DEFAULT_BRANCH"]
    assert ruleset["conditions_ref_name_exclude"] == []
    assert ruleset["repo_url"] == TEST_REPO_URL


def test_transform_rulesets_rules():
    """
    Test that rules within rulesets are correctly transformed.
    """
    output_rulesets = []
    output_rules = []
    output_bypass_actors = []

    _transform_rulesets(
        SINGLE_RULESET,
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
        output_bypass_actors,
    )

    assert len(output_rules) == 3

    rule_types = {r["type"] for r in output_rules}
    expected_types = {"DELETION", "PULL_REQUEST", "REQUIRED_STATUS_CHECKS"}
    assert rule_types == expected_types

    for rule in output_rules:
        assert rule["id"] is not None
        assert rule["ruleset_id"] == RULESET_PRODUCTION["id"]

    deletion_rule = next(r for r in output_rules if r["type"] == "DELETION")
    assert deletion_rule["parameters"] is None

    pr_rule = next(r for r in output_rules if r["type"] == "PULL_REQUEST")
    params = json.loads(pr_rule["parameters"])
    assert params["requiredApprovingReviewCount"] == 2
    assert params["dismissStaleReviewsOnPush"] is True


def test_transform_rulesets_bypass_actors():
    """
    Test that bypass actors are correctly transformed.
    """
    output_rulesets = []
    output_rules = []
    output_bypass_actors = []

    _transform_rulesets(
        SINGLE_RULESET,
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
        output_bypass_actors,
    )

    assert len(output_bypass_actors) == 2

    team_actor = next(a for a in output_bypass_actors if a["actor_type"] == "Team")
    assert team_actor["id"] == "RBA_kwDOBypass001"
    assert team_actor["bypass_mode"] == "ALWAYS"
    assert team_actor["actor_id"] == "T_kwDOAbc123"
    assert team_actor["actor_database_id"] == 456
    assert team_actor["actor_name"] == "maintainers"
    assert team_actor["actor_slug"] is None
    assert team_actor["ruleset_id"] == RULESET_PRODUCTION["id"]

    app_actor = next(a for a in output_bypass_actors if a["actor_type"] == "App")
    assert app_actor["id"] == "RBA_kwDOBypass002"
    assert app_actor["bypass_mode"] == "PULL_REQUEST"
    assert app_actor["actor_id"] == "A_kwDOAbc789"
    assert app_actor["actor_name"] == "Dependabot"
    assert app_actor["actor_slug"] == "dependabot"
    assert app_actor["ruleset_id"] == RULESET_PRODUCTION["id"]


def test_transform_rulesets_empty_list():
    """
    Test that transformation handles repos with no rulesets.
    """
    output_rulesets = []
    output_rules = []
    output_bypass_actors = []

    _transform_rulesets(
        NO_RULESETS,
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
        output_bypass_actors,
    )

    assert len(output_rulesets) == 0
    assert len(output_rules) == 0
    assert len(output_bypass_actors) == 0


def test_transform_rulesets_no_bypass_actors():
    """
    Test rulesets with no bypass actors.
    """
    output_rulesets = []
    output_rules = []
    output_bypass_actors = []

    _transform_rulesets(
        [RULESET_EVALUATE],
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
        output_bypass_actors,
    )

    assert len(output_rulesets) == 1
    assert len(output_rules) == 1
    assert len(output_bypass_actors) == 0


def test_transform_rulesets_target_types():
    """
    Test that different target types (BRANCH, TAG) are preserved.
    """
    output_rulesets = []
    output_rules = []
    output_bypass_actors = []

    _transform_rulesets(
        RULESETS_DATA,
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
        output_bypass_actors,
    )

    targets = {r["target"] for r in output_rulesets}
    assert "BRANCH" in targets
    assert "TAG" in targets


def test_transform_rulesets_enforcement_modes():
    """
    Test that different enforcement modes are preserved.
    """
    output_rulesets = []
    output_rules = []
    output_bypass_actors = []

    _transform_rulesets(
        RULESETS_DATA,
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
        output_bypass_actors,
    )

    enforcements = {r["enforcement"] for r in output_rulesets}
    assert "ACTIVE" in enforcements
    assert "EVALUATE" in enforcements


def test_transform_rulesets_boolean_bypass_actors():
    """
    Test that boolean bypass actor types are correctly transformed.
    Tests organizationAdmin, enterpriseOwner, deployKey, and repositoryRoleName.
    """
    output_rulesets = []
    output_rules = []
    output_bypass_actors = []

    _transform_rulesets(
        [RULESET_BOOLEAN_ACTORS],
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
        output_bypass_actors,
    )

    assert len(output_rulesets) == 1
    assert len(output_bypass_actors) == 4

    org_admin = next(
        a for a in output_bypass_actors if a["actor_type"] == "OrganizationAdmin"
    )
    assert org_admin["id"] == "RBA_kwDOBypassOrgAdmin"
    assert org_admin["bypass_mode"] == "ALWAYS"
    assert org_admin["actor_id"] is None
    assert org_admin["actor_name"] is None

    ent_owner = next(
        a for a in output_bypass_actors if a["actor_type"] == "EnterpriseOwner"
    )
    assert ent_owner["id"] == "RBA_kwDOBypassEntOwner"
    assert ent_owner["bypass_mode"] == "ALWAYS"
    assert ent_owner["actor_id"] is None

    deploy_key = next(a for a in output_bypass_actors if a["actor_type"] == "DeployKey")
    assert deploy_key["id"] == "RBA_kwDOBypassDeployKey"
    assert deploy_key["bypass_mode"] == "PULL_REQUEST"
    assert deploy_key["actor_id"] is None

    repo_role = next(
        a for a in output_bypass_actors if a["actor_type"] == "RepositoryRole"
    )
    assert repo_role["id"] == "RBA_kwDOBypassRepoRole"
    assert repo_role["bypass_mode"] == "ALWAYS"
    assert repo_role["actor_name"] == "maintain"
    assert repo_role["actor_database_id"] == 12345
    assert repo_role["actor_id"] is None
