"""
Unit tests for GitHub protected branches transformation logic.
"""

from cartography.intel.github.repos import _transform_protected_branches
from tests.data.github.protected_branches import NO_PROTECTED_BRANCHES
from tests.data.github.protected_branches import PROTECTED_BRANCH_RELEASE
from tests.data.github.protected_branches import PROTECTED_BRANCH_STRONG
from tests.data.github.protected_branches import PROTECTED_BRANCH_WEAK
from tests.data.github.protected_branches import PROTECTED_BRANCHES_DATA

TEST_REPO_URL = "https://github.com/test-org/test-repo"


def test_transform_protected_branches_with_data():
    """
    Test that protected branches are correctly transformed from GitHub API format.
    """
    # Arrange
    output = []

    # Act
    _transform_protected_branches(
        PROTECTED_BRANCHES_DATA,
        TEST_REPO_URL,
        output,
    )

    # Assert: Check we got 3 protected branches
    assert len(output) == 3

    # Assert: Check the IDs are present
    ids = {pb["id"] for pb in output}
    expected_ids = {
        PROTECTED_BRANCH_STRONG["id"],
        PROTECTED_BRANCH_WEAK["id"],
        PROTECTED_BRANCH_RELEASE["id"],
    }
    assert ids == expected_ids


def test_transform_protected_branches_field_mapping():
    """
    Test that field names are correctly mapped from camelCase to snake_case.
    """
    # Arrange
    output = []

    # Act
    _transform_protected_branches(
        [PROTECTED_BRANCH_STRONG],
        TEST_REPO_URL,
        output,
    )

    # Assert: Check that a specific protected branch has expected properties
    assert len(output) == 1
    pb = output[0]

    assert pb["id"] == PROTECTED_BRANCH_STRONG["id"]
    assert pb["pattern"] == PROTECTED_BRANCH_STRONG["pattern"]
    assert pb["allows_deletions"] == PROTECTED_BRANCH_STRONG["allowsDeletions"]
    assert pb["allows_force_pushes"] == PROTECTED_BRANCH_STRONG["allowsForcePushes"]
    assert (
        pb["dismisses_stale_reviews"]
        == PROTECTED_BRANCH_STRONG["dismissesStaleReviews"]
    )
    assert pb["is_admin_enforced"] == PROTECTED_BRANCH_STRONG["isAdminEnforced"]
    assert (
        pb["requires_approving_reviews"]
        == PROTECTED_BRANCH_STRONG["requiresApprovingReviews"]
    )
    assert (
        pb["required_approving_review_count"]
        == PROTECTED_BRANCH_STRONG["requiredApprovingReviewCount"]
    )
    assert (
        pb["requires_code_owner_reviews"]
        == PROTECTED_BRANCH_STRONG["requiresCodeOwnerReviews"]
    )
    assert (
        pb["requires_commit_signatures"]
        == PROTECTED_BRANCH_STRONG["requiresCommitSignatures"]
    )
    assert (
        pb["requires_linear_history"]
        == PROTECTED_BRANCH_STRONG["requiresLinearHistory"]
    )
    assert (
        pb["requires_status_checks"] == PROTECTED_BRANCH_STRONG["requiresStatusChecks"]
    )
    assert (
        pb["requires_strict_status_checks"]
        == PROTECTED_BRANCH_STRONG["requiresStrictStatusChecks"]
    )
    assert pb["restricts_pushes"] == PROTECTED_BRANCH_STRONG["restrictsPushes"]
    assert (
        pb["restricts_review_dismissals"]
        == PROTECTED_BRANCH_STRONG["restrictsReviewDismissals"]
    )
    assert pb["repo_url"] == TEST_REPO_URL


def test_transform_protected_branches_empty_list():
    """
    Test that transformation handles repos with no branch protection.
    """
    # Arrange
    output = []

    # Act
    _transform_protected_branches(
        NO_PROTECTED_BRANCHES,
        TEST_REPO_URL,
        output,
    )

    # Assert
    assert len(output) == 0


def test_transform_protected_branches_pattern_handling():
    """
    Test that different branch patterns are correctly preserved.
    """
    # Arrange
    output = []

    # Act
    _transform_protected_branches(
        PROTECTED_BRANCHES_DATA,
        TEST_REPO_URL,
        output,
    )

    # Assert: Check patterns are preserved
    patterns = {pb["pattern"] for pb in output}
    expected_patterns = {"main", "release/*"}
    assert patterns == expected_patterns
