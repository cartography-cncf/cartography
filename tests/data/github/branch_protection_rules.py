"""
Test data for GitHub protected branches.
https://docs.github.com/en/graphql/reference/objects#branchprotectionrule
"""

from typing import Any

PROTECTED_BRANCH_STRONG = {
    "id": "BPR_kwDOAbc123==",
    "pattern": "main",
    "allowsDeletions": False,
    "allowsForcePushes": False,
    "dismissesStaleReviews": True,
    "isAdminEnforced": True,
    "requiresApprovingReviews": True,
    "requiredApprovingReviewCount": 2,
    "requiresCodeOwnerReviews": True,
    "requiresCommitSignatures": True,
    "requiresLinearHistory": True,
    "requiresStatusChecks": True,
    "requiresStrictStatusChecks": True,
    "restrictsPushes": True,
    "restrictsReviewDismissals": True,
}

PROTECTED_BRANCH_WEAK = {
    "id": "BPR_kwDOWeak001==",
    "pattern": "main",
    "allowsDeletions": True,
    "allowsForcePushes": True,
    "dismissesStaleReviews": False,
    "isAdminEnforced": False,
    "requiresApprovingReviews": False,
    "requiredApprovingReviewCount": 0,
    "requiresCodeOwnerReviews": False,
    "requiresCommitSignatures": False,
    "requiresLinearHistory": False,
    "requiresStatusChecks": False,
    "requiresStrictStatusChecks": False,
    "restrictsPushes": False,
    "restrictsReviewDismissals": False,
}

PROTECTED_BRANCH_RELEASE = {
    "id": "BPR_kwDORel456==",
    "pattern": "release/*",
    "allowsDeletions": False,
    "allowsForcePushes": False,
    "dismissesStaleReviews": True,
    "isAdminEnforced": False,
    "requiresApprovingReviews": True,
    "requiredApprovingReviewCount": 1,
    "requiresCodeOwnerReviews": False,
    "requiresCommitSignatures": False,
    "requiresLinearHistory": False,
    "requiresStatusChecks": True,
    "requiresStrictStatusChecks": False,
    "restrictsPushes": False,
    "restrictsReviewDismissals": False,
}

PROTECTED_BRANCHES_DATA: list[dict[str, Any]] = [
    PROTECTED_BRANCH_STRONG,
    PROTECTED_BRANCH_WEAK,
    PROTECTED_BRANCH_RELEASE,
]

NO_PROTECTED_BRANCHES: list[dict[str, Any]] = []
