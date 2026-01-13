"""
Unit tests for GitHub branch protection rules transformation logic.
"""

from cartography.intel.github.repos import _transform_branch_protection_rules
from tests.data.github.branch_protection_rules import NO_PROTECTED_BRANCHES
from tests.data.github.branch_protection_rules import PROTECTED_BRANCH_RELEASE
from tests.data.github.branch_protection_rules import PROTECTED_BRANCH_STRONG
from tests.data.github.branch_protection_rules import PROTECTED_BRANCH_WEAK
from tests.data.github.branch_protection_rules import PROTECTED_BRANCHES_DATA

TEST_REPO_URL = "https://github.com/test-org/test-repo"


def test_transform_branch_protection_rules_with_data():
    """
    Test that branch protection rules are correctly transformed from GitHub API format.
    """
    # Arrange
    output = []

    # Act
    _transform_branch_protection_rules(
        PROTECTED_BRANCHES_DATA,
        TEST_REPO_URL,
        output,
    )

    # Assert: Check we got 3 branch protection rules
    assert len(output) == 3

    # Assert: Check the IDs are present
    ids = {rule["id"] for rule in output}
    expected_ids = {
        PROTECTED_BRANCH_STRONG["id"],
        PROTECTED_BRANCH_WEAK["id"],
        PROTECTED_BRANCH_RELEASE["id"],
    }
    assert ids == expected_ids


def test_transform_branch_protection_rules_field_mapping():
    """
    Test that field names are correctly mapped from camelCase to snake_case.
    """
    # Arrange
    output = []

    # Act
    _transform_branch_protection_rules(
        [PROTECTED_BRANCH_STRONG],
        TEST_REPO_URL,
        output,
    )

    # Assert: Check that a specific branch protection rule has expected properties
    assert len(output) == 1
    rule = output[0]

    assert rule["id"] == PROTECTED_BRANCH_STRONG["id"]
    assert rule["pattern"] == PROTECTED_BRANCH_STRONG["pattern"]
    assert rule["allows_deletions"] == PROTECTED_BRANCH_STRONG["allowsDeletions"]
    assert rule["allows_force_pushes"] == PROTECTED_BRANCH_STRONG["allowsForcePushes"]
    assert (
        rule["dismisses_stale_reviews"]
        == PROTECTED_BRANCH_STRONG["dismissesStaleReviews"]
    )
    assert rule["is_admin_enforced"] == PROTECTED_BRANCH_STRONG["isAdminEnforced"]
    assert (
        rule["requires_approving_reviews"]
        == PROTECTED_BRANCH_STRONG["requiresApprovingReviews"]
    )
    assert (
        rule["required_approving_review_count"]
        == PROTECTED_BRANCH_STRONG["requiredApprovingReviewCount"]
    )
    assert (
        rule["requires_code_owner_reviews"]
        == PROTECTED_BRANCH_STRONG["requiresCodeOwnerReviews"]
    )
    assert (
        rule["requires_commit_signatures"]
        == PROTECTED_BRANCH_STRONG["requiresCommitSignatures"]
    )
    assert (
        rule["requires_linear_history"]
        == PROTECTED_BRANCH_STRONG["requiresLinearHistory"]
    )
    assert (
        rule["requires_status_checks"]
        == PROTECTED_BRANCH_STRONG["requiresStatusChecks"]
    )
    assert (
        rule["requires_strict_status_checks"]
        == PROTECTED_BRANCH_STRONG["requiresStrictStatusChecks"]
    )
    assert rule["restricts_pushes"] == PROTECTED_BRANCH_STRONG["restrictsPushes"]
    assert (
        rule["restricts_review_dismissals"]
        == PROTECTED_BRANCH_STRONG["restrictsReviewDismissals"]
    )
    assert rule["repo_url"] == TEST_REPO_URL


def test_transform_branch_protection_rules_empty_list():
    """
    Test that transformation handles repos with no branch protection.
    """
    # Arrange
    output = []

    # Act
    _transform_branch_protection_rules(
        NO_PROTECTED_BRANCHES,
        TEST_REPO_URL,
        output,
    )

    # Assert
    assert len(output) == 0


def test_transform_branch_protection_rules_pattern_handling():
    """
    Test that different branch patterns are correctly preserved.
    """
    # Arrange
    output = []

    # Act
    _transform_branch_protection_rules(
        PROTECTED_BRANCHES_DATA,
        TEST_REPO_URL,
        output,
    )

    # Assert: Check patterns are preserved
    patterns = {rule["pattern"] for rule in output}
    expected_patterns = {"main", "release/*"}
    assert patterns == expected_patterns
