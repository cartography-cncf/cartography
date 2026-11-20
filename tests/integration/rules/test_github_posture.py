import pytest

from cartography.client.core.tx import load
from cartography.models.github.branch_protection_rules import (
    GitHubBranchProtectionRuleSchema,
)
from cartography.models.github.codeowners import GitHubCodeOwnerRuleSchema
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
}
STRONG_RULESET_RULES = [
    {
        "type": "PULL_REQUEST",
        "parameters_required_approving_review_count": 1,
        "parameters_require_code_owner_review": True,
    },
    {"type": "NON_FAST_FORWARD"},
]


def _ruleset(include, exclude=(), enforcement="ACTIVE", rules=STRONG_RULESET_RULES):
    return {
        "conditions_ref_name_include": list(include),
        "conditions_ref_name_exclude": list(exclude),
        "enforcement": enforcement,
        "rules": rules,
    }


def _issue(fact):
    return fact.id.removeprefix("github_repository_default_branch_").removeprefix(
        "github_repository_"
    )


def _load_repository(
    neo4j_session, branch_rules, rulesets, has_codeowners, archived=False
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
    "branch_rules,rulesets,has_codeowners,archived,failing,evaluated",
    [
        pytest.param(
            [],
            [],
            False,
            False,
            {UNPROTECTED, NO_REVIEWS, FORCE_PUSH, CODEOWNERS_MISSING},
            ALWAYS_EVALUATED,
            id="no_protection",
        ),
        pytest.param(
            [STRONG_BRANCH_RULE],
            [],
            True,
            False,
            set(),
            ALWAYS_EVALUATED | {ADMINS, CODEOWNER_REVIEW},
            id="strong_branch_rule",
        ),
        pytest.param(
            [{**STRONG_BRANCH_RULE, "pattern": "release/*"}],
            [],
            False,
            False,
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
                }
            ],
            [],
            True,
            False,
            {NO_REVIEWS, FORCE_PUSH, ADMINS, CODEOWNER_REVIEW},
            ALWAYS_EVALUATED | {ADMINS, CODEOWNER_REVIEW},
            id="weak_wildcard_branch_rule",
        ),
        pytest.param(
            [],
            [_ruleset(["~DEFAULT_BRANCH"])],
            True,
            False,
            set(),
            ALWAYS_EVALUATED | {CODEOWNER_REVIEW},
            id="strong_default_branch_ruleset",
        ),
        pytest.param(
            [{**STRONG_BRANCH_RULE, "is_admin_enforced": False}],
            [_ruleset(["refs/heads/ma*"], rules=[{"type": "DELETION"}])],
            True,
            False,
            set(),
            ALWAYS_EVALUATED | {CODEOWNER_REVIEW},
            id="ruleset_also_applies_so_admin_check_skipped",
        ),
        pytest.param(
            [],
            [_ruleset(["refs/heads/ma*"], rules=[{"type": "DELETION"}])],
            True,
            False,
            {NO_REVIEWS, FORCE_PUSH, CODEOWNER_REVIEW},
            ALWAYS_EVALUATED | {CODEOWNER_REVIEW},
            id="glob_ruleset_without_review_or_force_push_rules",
        ),
        pytest.param(
            [],
            [
                _ruleset(["~DEFAULT_BRANCH"], enforcement="EVALUATE"),
                _ruleset(["~ALL"], exclude=["refs/heads/main"]),
            ],
            False,
            False,
            {UNPROTECTED, NO_REVIEWS, FORCE_PUSH, CODEOWNERS_MISSING},
            ALWAYS_EVALUATED,
            id="rulesets_not_enforced_or_excluding_default_branch",
        ),
        pytest.param([], [], False, True, set(), set(), id="archived"),
    ],
)
def test_github_repository_posture_facts(
    neo4j_session,
    branch_rules,
    rulesets,
    has_codeowners,
    archived,
    failing,
    evaluated,
):
    # Arrange
    _load_repository(neo4j_session, branch_rules, rulesets, has_codeowners, archived)

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
