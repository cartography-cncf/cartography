import pytest

from cartography.client.core.tx import load
from cartography.models.github.branch_protection_rules import (
    GitHubBranchProtectionRuleSchema,
)
from cartography.models.github.codeowners import GitHubCodeOwnerRuleSchema
from cartography.models.github.codeowners import GitHubRepositoryCodeOwnersReadSchema
from cartography.models.github.repos import GitHubRepositorySchema
from cartography.models.github.ruleset_rules import GitHubRulesetRuleSchema
from cartography.models.github.rulesets import GitHubRulesetSchema
from cartography.rules.data.rules.github_posture import github_codeowners_coverage
from cartography.rules.data.rules.github_posture import github_default_branch_protection

UPDATE_TAG = 1
ORG_URL = "https://github.com/simpsoncorp"
REPO_URL = f"{ORG_URL}/sample_repo"
REPOSITORY_FACTS = (
    *github_default_branch_protection.facts,
    *github_codeowners_coverage.facts,
)

UNPROTECTED = "unprotected"
NO_REVIEWS = "no_required_reviews"
FORCE_PUSH = "force_push_allowed"
ADMINS = "admins_not_enforced"
CODEOWNERS_MISSING = "codeowners_missing"
CODEOWNER_REVIEW = "codeowners_review_not_required"
# Facts every unarchived repository with a default branch is evaluated against.
ALWAYS_EVALUATED = {UNPROTECTED, NO_REVIEWS, FORCE_PUSH, CODEOWNERS_MISSING}

STRONG_BRANCH_RULE = {
    "pattern": "main",
    "allows_force_pushes": False,
    "is_admin_enforced": True,
    "requires_approving_reviews": True,
    "required_approving_review_count": 1,
    "requires_code_owner_reviews": True,
    # GitHub's answer for which classic rule governs the default branch.
    "protects_default_branch": True,
}
STRONG_RULESET_RULES = [
    {
        "type": "PULL_REQUEST",
        "parameters_required_approving_review_count": 1,
        "parameters_require_code_owner_review": True,
    },
    {"type": "NON_FAST_FORWARD"},
]


def _ruleset(
    include,
    exclude=(),
    enforcement="ACTIVE",
    rules=STRONG_RULESET_RULES,
    applies=True,
):
    return {
        "conditions_ref_name_include": list(include),
        "conditions_ref_name_exclude": list(exclude),
        "enforcement": enforcement,
        "rules": rules,
        # GitHub's answer from the rules-for-a-branch endpoint.
        "applies_to_default_branch": applies,
    }


def _issue(fact):
    return fact.id.removeprefix("github_repository_default_branch_").removeprefix(
        "github_repository_"
    )


def _load_repository(
    neo4j_session,
    branch_rules,
    rulesets,
    has_codeowners,
    archived=False,
    protection_visible=(True, True),
):
    neo4j_session.run(
        "MATCH (n) WHERE n:GitHubRepository OR n:GitHubBranchProtectionRule "
        "OR n:GitHubRuleset OR n:GitHubRulesetRule OR n:GitHubCodeOwnerRule "
        "DETACH DELETE n",
    )
    load(
        neo4j_session,
        GitHubRepositorySchema(),
        [
            {
                "id": REPO_URL,
                "fullname": "simpsoncorp/sample_repo",
                "defaultbranch": "main",
                "archived": archived,
                "branch_protection_rules_visible": protection_visible[0],
                "rulesets_visible": protection_visible[1],
            }
        ],
        lastupdated=UPDATE_TAG,
    )
    load(
        neo4j_session,
        GitHubRepositoryCodeOwnersReadSchema(),
        # None stands for a failed read; "stale" for a failed read that kept the
        # rules an earlier sync loaded.
        [
            {
                "id": REPO_URL,
                "codeowners_readable": has_codeowners not in (None, "stale"),
            }
        ],
        lastupdated=UPDATE_TAG,
    )
    load(
        neo4j_session,
        GitHubBranchProtectionRuleSchema(),
        [
            {"id": f"bpr-{i}", "repo_url": REPO_URL, **rule}
            for i, rule in enumerate(branch_rules)
        ],
        lastupdated=UPDATE_TAG,
        owner_org_id=ORG_URL,
    )
    load(
        neo4j_session,
        GitHubRulesetSchema(),
        [
            {
                "id": f"ruleset-{i}",
                "target": "BRANCH",
                "repo_url": REPO_URL,
                **{k: v for k, v in ruleset.items() if k != "rules"},
            }
            for i, ruleset in enumerate(rulesets)
        ],
        lastupdated=UPDATE_TAG,
        owner_org_id=ORG_URL,
    )
    load(
        neo4j_session,
        GitHubRulesetRuleSchema(),
        [
            {"id": f"ruleset-{i}:rule:{j}", "ruleset_id": f"ruleset-{i}", **rule}
            for i, ruleset in enumerate(rulesets)
            for j, rule in enumerate(ruleset["rules"])
        ],
        lastupdated=UPDATE_TAG,
        owner_org_id=ORG_URL,
    )
    if has_codeowners:
        load(
            neo4j_session,
            GitHubCodeOwnerRuleSchema(),
            [{"id": f"{REPO_URL}#CODEOWNERS:1", "repo_url": REPO_URL, "pattern": "*"}],
            lastupdated=UPDATE_TAG,
            owner_org_id=ORG_URL,
        )


@pytest.mark.parametrize(
    "branch_rules,rulesets,has_codeowners,archived,protection_visible,failing,evaluated",
    [
        pytest.param(
            [],
            [],
            False,
            False,
            (True, True),
            {UNPROTECTED, NO_REVIEWS, FORCE_PUSH, CODEOWNERS_MISSING},
            ALWAYS_EVALUATED,
            id="no_protection",
        ),
        pytest.param(
            [STRONG_BRANCH_RULE],
            [],
            True,
            False,
            (True, True),
            set(),
            ALWAYS_EVALUATED | {ADMINS, CODEOWNER_REVIEW},
            id="strong_branch_rule",
        ),
        pytest.param(
            [
                {
                    **STRONG_BRANCH_RULE,
                    "pattern": "release/*",
                    "protects_default_branch": False,
                }
            ],
            [],
            False,
            False,
            (True, True),
            {UNPROTECTED, NO_REVIEWS, FORCE_PUSH, CODEOWNERS_MISSING},
            ALWAYS_EVALUATED,
            id="branch_rule_for_other_branch",
        ),
        pytest.param(
            [
                {
                    "pattern": "*",
                    "allows_force_pushes": True,
                    "is_admin_enforced": False,
                    "requires_approving_reviews": True,
                    "required_approving_review_count": 0,
                    "protects_default_branch": True,
                }
            ],
            [],
            True,
            False,
            (True, True),
            {NO_REVIEWS, FORCE_PUSH, ADMINS, CODEOWNER_REVIEW},
            ALWAYS_EVALUATED | {ADMINS, CODEOWNER_REVIEW},
            id="weak_wildcard_branch_rule",
        ),
        pytest.param(
            [
                {
                    "pattern": "main",
                    "allows_force_pushes": True,
                    "protects_default_branch": True,
                },
                {
                    **STRONG_BRANCH_RULE,
                    "pattern": "*",
                    "protects_default_branch": False,
                },
            ],
            [],
            True,
            False,
            (True, True),
            {NO_REVIEWS, FORCE_PUSH, ADMINS, CODEOWNER_REVIEW},
            ALWAYS_EVALUATED | {ADMINS, CODEOWNER_REVIEW},
            id="only_the_rule_github_applies_counts",
        ),
        pytest.param(
            [],
            [_ruleset(["~DEFAULT_BRANCH"])],
            True,
            False,
            (True, True),
            set(),
            ALWAYS_EVALUATED | {CODEOWNER_REVIEW},
            id="strong_default_branch_ruleset",
        ),
        pytest.param(
            [{**STRONG_BRANCH_RULE, "is_admin_enforced": False}],
            [_ruleset(["refs/heads/ma*"], rules=[{"type": "DELETION"}])],
            True,
            False,
            (True, True),
            set(),
            ALWAYS_EVALUATED | {CODEOWNER_REVIEW},
            id="ruleset_also_applies_so_admin_check_skipped",
        ),
        pytest.param(
            [],
            [_ruleset(["refs/heads/ma*"], rules=[{"type": "DELETION"}])],
            True,
            False,
            (True, True),
            {NO_REVIEWS, FORCE_PUSH, CODEOWNER_REVIEW},
            ALWAYS_EVALUATED | {CODEOWNER_REVIEW},
            id="glob_ruleset_without_review_or_force_push_rules",
        ),
        pytest.param(
            [],
            # The conditions are what GitHub resolved; the rule only reads its
            # answer. Before that, an excluded ~ALL was counted as protection.
            [
                _ruleset(["~DEFAULT_BRANCH"], enforcement="EVALUATE", applies=False),
                _ruleset(["~ALL"], exclude=["refs/heads/main"], applies=False),
                _ruleset(["~DEFAULT_BRANCH"], exclude=["~ALL"], applies=False),
            ],
            False,
            False,
            (True, True),
            {UNPROTECTED, NO_REVIEWS, FORCE_PUSH, CODEOWNERS_MISSING},
            ALWAYS_EVALUATED,
            id="rulesets_github_does_not_apply_to_default_branch",
        ),
        pytest.param(
            [{**STRONG_BRANCH_RULE, "pattern": "m[!x]in"}],
            [],
            True,
            False,
            (True, True),
            set(),
            ALWAYS_EVALUATED | {ADMINS, CODEOWNER_REVIEW},
            id="negated_bracket_rule_github_applies",
        ),
        pytest.param(
            [{**STRONG_BRANCH_RULE, "pattern": "mai[n[]"}],
            [],
            True,
            False,
            (True, True),
            set(),
            ALWAYS_EVALUATED | {ADMINS, CODEOWNER_REVIEW},
            id="unclosed_bracket_rule_github_applies",
        ),
        pytest.param(
            [],
            [_ruleset(["~DEFAULT_BRANCH"], rules=[{"type": "UPDATE"}])],
            True,
            False,
            (True, True),
            {NO_REVIEWS, CODEOWNER_REVIEW},
            ALWAYS_EVALUATED | {CODEOWNER_REVIEW},
            id="update_restriction_blocks_force_pushes",
        ),
        pytest.param(
            [],
            [],
            None,
            False,
            (True, True),
            {UNPROTECTED, NO_REVIEWS, FORCE_PUSH},
            {UNPROTECTED, NO_REVIEWS, FORCE_PUSH},
            id="codeowners_not_readable",
        ),
        pytest.param(
            [],
            [],
            "stale",
            False,
            (True, True),
            {UNPROTECTED, NO_REVIEWS, FORCE_PUSH},
            {UNPROTECTED, NO_REVIEWS, FORCE_PUSH},
            id="codeowners_rules_kept_from_an_earlier_read",
        ),
        pytest.param([], [], False, True, (True, True), set(), set(), id="archived"),
        pytest.param(
            [],
            [],
            False,
            False,
            (False, False),
            {CODEOWNERS_MISSING},
            {CODEOWNERS_MISSING},
            id="protection_not_visible",
        ),
        pytest.param(
            [],
            [],
            False,
            False,
            (True, False),
            {CODEOWNERS_MISSING},
            {CODEOWNERS_MISSING},
            id="rulesets_not_visible",
        ),
        pytest.param(
            [],
            [],
            False,
            False,
            (False, True),
            {CODEOWNERS_MISSING},
            {CODEOWNERS_MISSING},
            id="branch_rules_not_visible",
        ),
    ],
)
def test_github_repository_posture_facts(
    neo4j_session,
    branch_rules,
    rulesets,
    has_codeowners,
    archived,
    protection_visible,
    failing,
    evaluated,
):
    # Arrange
    _load_repository(
        neo4j_session,
        branch_rules,
        rulesets,
        has_codeowners,
        archived,
        protection_visible,
    )

    # Act
    failing_facts = {
        _issue(fact)
        for fact in REPOSITORY_FACTS
        if neo4j_session.run(fact.cypher_query).data()
    }
    visual_failing_facts = {
        _issue(fact)
        for fact in REPOSITORY_FACTS
        if neo4j_session.run(fact.cypher_visual_query).data()
    }
    evaluated_facts = {
        _issue(fact)
        for fact in REPOSITORY_FACTS
        if neo4j_session.run(fact.cypher_count_query).single()["count"]
    }

    # Assert
    assert failing_facts == failing
    assert visual_failing_facts == failing
    assert evaluated_facts == evaluated
