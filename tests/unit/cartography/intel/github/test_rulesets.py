"""
Unit tests for GitHub repository rulesets transformation logic.
"""

import json
import logging
from copy import deepcopy

import pytest

from cartography.intel.github.repos import _transform_rulesets
from cartography.intel.github.repos import _warn_if_github_connection_truncated
from tests.data.github.rulesets import NO_RULESETS
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

    _transform_rulesets(
        RULESETS_DATA,
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
    )

    assert len(output_rulesets) == 3
    assert len(output_rules) == 5

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

    _transform_rulesets(
        SINGLE_RULESET,
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
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
    assert ruleset["conditions_repository_name_include"] == ["important-*"]
    assert ruleset["conditions_repository_name_exclude"] == ["important-archive"]
    assert ruleset["conditions_repository_name_protected"] is False
    assert ruleset["conditions_repository_ids"] == [123456789]
    assert json.loads(ruleset["conditions_repository_property_include"]) == [
        {"name": "visibility", "propertyValues": ["private"], "source": "custom"}
    ]
    assert json.loads(ruleset["conditions_repository_property_exclude"]) == []
    assert json.loads(ruleset["conditions_organization_property_include"]) == [
        {"name": "environment", "propertyValues": ["prod"]}
    ]
    assert json.loads(ruleset["conditions_organization_property_exclude"]) == [
        {"name": "lifecycle", "propertyValues": ["deprecated"]}
    ]
    assert ruleset["repo_url"] == TEST_REPO_URL


def test_transform_rulesets_rules():
    """
    Test that rules within rulesets are correctly transformed.
    """
    output_rulesets = []
    output_rules = []

    _transform_rulesets(
        SINGLE_RULESET,
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
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
    assert pr_rule["parameters_required_approving_review_count"] == 2
    assert pr_rule["parameters_dismiss_stale_reviews_on_push"] is True
    assert pr_rule["parameters_require_code_owner_review"] is True

    status_rule = next(r for r in output_rules if r["type"] == "REQUIRED_STATUS_CHECKS")
    assert status_rule["parameters_required_status_checks"] == ["ci/tests"]


def test_transform_rulesets_requires_ruleset_id():
    """
    Test that malformed ruleset nodes fail fast on missing required IDs.
    """
    ruleset_without_id = deepcopy(RULESET_PRODUCTION)
    ruleset_without_id.pop("id")
    output_rulesets = []
    output_rules = []

    with pytest.raises(KeyError):
        _transform_rulesets(
            [ruleset_without_id],
            TEST_REPO_URL,
            output_rulesets,
            output_rules,
        )


def test_transform_rulesets_requires_rule_id():
    """
    Test that malformed ruleset rule nodes fail fast on missing required IDs.
    """
    ruleset_with_rule_without_id = deepcopy(RULESET_PRODUCTION)
    ruleset_with_rule_without_id["rules"]["nodes"].append(
        {
            "type": "DELETION",
            "parameters": None,
        }
    )
    output_rulesets = []
    output_rules = []

    with pytest.raises(KeyError):
        _transform_rulesets(
            [ruleset_with_rule_without_id],
            TEST_REPO_URL,
            output_rulesets,
            output_rules,
        )


def test_transform_rulesets_skips_null_nodes():
    """
    Test that null ruleset and rule nodes are skipped.
    """
    ruleset_with_null_rule = deepcopy(RULESET_PRODUCTION)
    ruleset_with_null_rule["rules"]["nodes"].append(None)
    output_rulesets = []
    output_rules = []

    _transform_rulesets(
        [None, ruleset_with_null_rule],
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
    )

    assert len(output_rulesets) == 1
    assert len(output_rules) == 3


def test_warn_if_github_connection_truncated_handles_null_nodes(caplog):
    """
    Test that explicit null connection nodes do not crash truncation warnings.
    """
    caplog.set_level(logging.WARNING)

    _warn_if_github_connection_truncated(
        {"totalCount": 2, "nodes": None},
        "ruleset rules",
        "ruleset-id",
    )

    assert "received 0 of 2" in caplog.text


def test_warn_if_github_connection_truncated_only_warns_on_truncated(caplog):
    """
    Test that complete and count-less connections do not emit warnings.
    """
    caplog.set_level(logging.WARNING)

    _warn_if_github_connection_truncated(
        {"totalCount": 1, "nodes": [{"id": "node-id"}]},
        "ruleset rules",
        "ruleset-id",
    )
    _warn_if_github_connection_truncated(
        {"nodes": []},
        "ruleset rules",
        "ruleset-id",
    )

    assert "truncated" not in caplog.text


def test_transform_rulesets_empty_list():
    """
    Test that transformation handles repos with no rulesets.
    """
    output_rulesets = []
    output_rules = []

    _transform_rulesets(
        NO_RULESETS,
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
    )

    assert len(output_rulesets) == 0
    assert len(output_rules) == 0


def test_transform_rulesets_target_types():
    """
    Test that different target types (BRANCH, TAG) are preserved.
    """
    output_rulesets = []
    output_rules = []

    _transform_rulesets(
        RULESETS_DATA,
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
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

    _transform_rulesets(
        RULESETS_DATA,
        TEST_REPO_URL,
        output_rulesets,
        output_rules,
    )

    enforcements = {r["enforcement"] for r in output_rulesets}
    assert "ACTIVE" in enforcements
    assert "EVALUATE" in enforcements
