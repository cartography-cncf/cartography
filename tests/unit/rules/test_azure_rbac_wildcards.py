"""
Logic-level regression tests for the Azure RBAC wildcard expansion used in
the new Azure facts under `identity_administration_privileges`,
`policy_administration_privileges`, and `delegation_boundary_modifiable`.

The Cypher implementation builds a case-insensitive regex from each
action / not_action via `replace(replace(toLower(x), '.', '[.]'), '*', '.*')`
and matches it against the literal pattern with `=~`. This mirrors that
formula in Python so we can assert the Contributor regression case directly.
"""

import re

from cartography.rules.data.rules.delegation_boundary_modifiable import (
    delegation_boundary_modifiable,
)
from cartography.rules.data.rules.identity_administration_privileges import (
    identity_administration_privileges,
)
from cartography.rules.data.rules.policy_administration_privileges import (
    policy_administration_privileges,
)


def _to_regex(action_or_not_action: str) -> str:
    """Mirror of the Cypher transform applied in the Azure RBAC facts."""
    return action_or_not_action.lower().replace(".", "[.]").replace("*", ".*")


def _glob_matches(pattern: str, wildcard: str) -> bool:
    """True iff Azure RBAC `wildcard` (with optional `*`) covers `pattern`."""
    return re.fullmatch(_to_regex(wildcard), pattern.lower()) is not None


# Pattern lists the facts search for. Most are literal Azure RBAC
# actions, but Microsoft documents the managed-identity assign action
# with a `*` segment for the identity name (Managed Identity Operator
# carries it verbatim), so the search pattern needs to match that form.
IDENTITY_PATTERNS = [
    "Microsoft.Authorization/roleAssignments/write",
    "Microsoft.Authorization/roleAssignments/delete",
    "Microsoft.Authorization/roleDefinitions/write",
    "Microsoft.Authorization/roleDefinitions/delete",
    "Microsoft.ManagedIdentity/userAssignedIdentities/*/assign/action",
]


# A subset of the documented Contributor not_actions, which include
# inner-wildcard entries (`Microsoft.Authorization/*/Write` etc.).
CONTRIBUTOR_ACTIONS = ["*"]
CONTRIBUTOR_NOT_ACTIONS = [
    "Microsoft.Authorization/*/Write",
    "Microsoft.Authorization/*/Delete",
    "Microsoft.Authorization/elevateAccess/Action",
    "Microsoft.Blueprint/blueprintAssignments/write",
    "Microsoft.Blueprint/blueprintAssignments/delete",
    "Microsoft.Compute/galleries/share/action",
]


def _shadow(pattern: str, actions: list[str], not_actions: list[str]) -> bool:
    """True iff the role grants `pattern` after subtracting not_actions."""
    granted = any(_glob_matches(pattern, a) for a in actions)
    shadowed = any(_glob_matches(pattern, na) for na in not_actions)
    return granted and not shadowed


def test_contributor_role_does_not_grant_role_assignment_write() -> None:
    # Contributor: actions=['*'], not_actions cover Microsoft.Authorization/*/Write
    pattern = "Microsoft.Authorization/roleAssignments/write"
    assert _shadow(pattern, CONTRIBUTOR_ACTIONS, CONTRIBUTOR_NOT_ACTIONS) is False


def test_contributor_role_does_not_grant_role_definitions_write() -> None:
    pattern = "Microsoft.Authorization/roleDefinitions/write"
    assert _shadow(pattern, CONTRIBUTOR_ACTIONS, CONTRIBUTOR_NOT_ACTIONS) is False


def test_contributor_role_grants_managed_identity_assign() -> None:
    # Contributor's not_actions don't shadow managed-identity assign, and
    # the role's `*` should match the wildcard pattern.
    pattern = "Microsoft.ManagedIdentity/userAssignedIdentities/*/assign/action"
    assert _shadow(pattern, CONTRIBUTOR_ACTIONS, CONTRIBUTOR_NOT_ACTIONS) is True


def test_managed_identity_operator_role_grants_managed_identity_assign() -> None:
    """
    Microsoft documents Managed Identity Operator with the action verbatim
    as `Microsoft.ManagedIdentity/userAssignedIdentities/*/assign/action`,
    plus `.../*/read`. With a literal `.../assign/action` pattern (no `*/`
    segment) this role would silently miss the rule; assert that the
    wildcard pattern matches it.
    """
    pattern = "Microsoft.ManagedIdentity/userAssignedIdentities/*/assign/action"
    operator_actions = [
        "Microsoft.ManagedIdentity/userAssignedIdentities/*/read",
        "Microsoft.ManagedIdentity/userAssignedIdentities/*/assign/action",
    ]
    assert _shadow(pattern, operator_actions, []) is True


def test_managed_identity_operator_does_not_grant_role_assignment_write() -> None:
    """Negative control: MIO must not flag the role-assignment patterns."""
    operator_actions = [
        "Microsoft.ManagedIdentity/userAssignedIdentities/*/read",
        "Microsoft.ManagedIdentity/userAssignedIdentities/*/assign/action",
    ]
    for pattern in (
        "Microsoft.Authorization/roleAssignments/write",
        "Microsoft.Authorization/roleDefinitions/write",
    ):
        assert _shadow(pattern, operator_actions, []) is False


def test_owner_role_grants_role_assignment_write() -> None:
    # Owner: actions=['*'], no not_actions blocking auth writes.
    pattern = "Microsoft.Authorization/roleAssignments/write"
    assert _shadow(pattern, ["*"], []) is True


def test_user_access_administrator_grants_role_assignment_write() -> None:
    # actions=['Microsoft.Authorization/*'], no not_actions
    pattern = "Microsoft.Authorization/roleAssignments/write"
    assert _shadow(pattern, ["Microsoft.Authorization/*"], []) is True


def test_case_insensitive_match() -> None:
    # The regex transform lower-cases both sides.
    pattern = "Microsoft.Authorization/RoleAssignments/Write"
    actions = ["MICROSOFT.AUTHORIZATION/*"]
    assert _shadow(pattern, actions, []) is True


def test_facts_use_regex_wildcard_expansion() -> None:
    """
    Sanity-check that the Cypher queries in the three Azure facts contain
    the regex-based wildcard expansion. If someone reverts to plain
    string equality, this test will fail.
    """
    expected_snippet = "replace(replace(toLower(a), '.', '[.]'), '*', '.*')"
    for rule in (
        identity_administration_privileges,
        policy_administration_privileges,
        delegation_boundary_modifiable,
    ):
        azure_facts = [f for f in rule.facts if f.id.startswith("azure_")]
        assert azure_facts, f"no Azure facts in {rule.id}"
        for fact in azure_facts:
            assert (
                expected_snippet in fact.cypher_query
            ), f"{fact.id} no longer expands actions via regex"
