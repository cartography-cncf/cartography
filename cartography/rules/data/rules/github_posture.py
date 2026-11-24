from cartography.rules.data.rules.github_security_configuration import (
    GitHubSecurityConfigurationOutput,
)
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

# Binds, for every unarchived repository with a default branch, the classic branch
# protection rule (`bprs`, at most one) and the active rulesets (`rulesets`) that
# GitHub reports as applying to the default branch, plus the rules of those
# rulesets (`ruleset_rules`). GitHub resolves pattern matching, rule precedence
# and ruleset include and exclude conditions itself, so none of that is
# reimplemented here.
_DEFAULT_BRANCH_CONTROLS = """
    MATCH (n:GitHubRepository)
    WHERE coalesce(n.archived, false) = false AND n.defaultbranch IS NOT NULL
    WITH n,
        [(n)-[:HAS_RULE]->(b:GitHubBranchProtectionRule)
            WHERE b.protects_default_branch = true | b] AS bprs,
        [(n)-[h:HAS_RULESET]->(rs:GitHubRuleset)
            WHERE h.applies_to_default_branch = true | rs] AS rulesets
    WITH n, bprs, rulesets, reduce(
        acc = [], r IN rulesets
        | acc + [(r)-[:CONTAINS_RULE]->(x:GitHubRulesetRule) | x]
    ) AS ruleset_rules
"""

_REQUIRES_REVIEW = """(
    any(b IN bprs WHERE coalesce(b.requires_approving_reviews, false)
        AND coalesce(b.required_approving_review_count, 0) >= 1)
    OR any(x IN ruleset_rules WHERE x.type = 'PULL_REQUEST'
        AND coalesce(x.parameters_required_approving_review_count, 0) >= 1)
)"""

_BLOCKS_FORCE_PUSH = """(
    any(b IN bprs WHERE NOT coalesce(b.allows_force_pushes, true))
    OR any(x IN ruleset_rules WHERE x.type IN ['NON_FAST_FORWARD', 'UPDATE'])
)"""

_REQUIRES_CODE_OWNER_REVIEW = """(
    any(b IN bprs WHERE coalesce(b.requires_code_owner_reviews, false))
    OR any(x IN ruleset_rules WHERE x.type = 'PULL_REQUEST'
        AND coalesce(x.parameters_require_code_owner_review, false))
)"""

_HAS_CODEOWNERS = "EXISTS { (n)-[:HAS_CODEOWNER_RULE]->(:GitHubCodeOwnerRule) }"

# Without administration read access the sync cannot see branch protection rules
# or rulesets, and an absent control would otherwise read as no protection.
_PROTECTION_VISIBLE = (
    "n.branch_protection_rules_visible = true AND n.rulesets_visible = true"
)


def _default_branch_fact(
    issue: str,
    name: str,
    description: str,
    condition: str,
    current_value: str,
    evaluated: str = _PROTECTION_VISIBLE,
) -> Fact:
    return Fact(
        id=f"github_repository_{issue}",
        name=name,
        description=description,
        cypher_query=f"""
        {_DEFAULT_BRANCH_CONTROLS}
        WHERE {evaluated} AND {condition}
        RETURN n.fullname AS asset_name, n.id AS asset_id,
            split(n.fullname, '/')[0] AS organization,
            'repository_{issue}' AS issue,
            {current_value} AS current_value
        """,
        cypher_visual_query=f"""
        {_DEFAULT_BRANCH_CONTROLS}
        WHERE {evaluated} AND {condition}
        OPTIONAL MATCH (n)-[:HAS_RULE|HAS_RULESET]->(control)
        RETURN n, control
        """,
        cypher_count_query=f"""
        {_DEFAULT_BRANCH_CONTROLS}
        WHERE {evaluated}
        RETURN count(n) AS count
        """,
        asset_label="GitHubRepository",
        asset_id_field="asset_id",
        identity_fields=("asset_id", "issue"),
        module=Module.GITHUB,
        maturity=Maturity.EXPERIMENTAL,
    )


# Default branch protection

_default_branch_unprotected = _default_branch_fact(
    issue="default_branch_unprotected",
    name="Repositories whose default branch has no protection",
    description=(
        "Unarchived repositories where no classic branch protection rule and no "
        "active branch ruleset applies to the default branch, so anyone with write "
        "access can push to it directly."
    ),
    condition="size(bprs) = 0 AND size(rulesets) = 0",
    current_value=(
        "'No branch protection rule or active ruleset on ' + n.defaultbranch"
    ),
)

_default_branch_no_required_reviews = _default_branch_fact(
    issue="default_branch_no_required_reviews",
    name="Repositories whose default branch does not require an approving review",
    description=(
        "Unarchived repositories where neither a branch protection rule nor an "
        "active ruleset on the default branch requires at least one approving "
        "pull request review. Unprotected default branches are included."
    ),
    condition=f"NOT {_REQUIRES_REVIEW}",
    current_value="'No approving review required on ' + n.defaultbranch",
)

_default_branch_force_push_allowed = _default_branch_fact(
    issue="default_branch_force_push_allowed",
    name="Repositories whose default branch allows force pushes",
    description=(
        "Unarchived repositories where neither a branch protection rule nor an "
        "active ruleset on the default branch blocks force pushes or all updates, "
        "so its history can be rewritten. Unprotected default branches are "
        "included."
    ),
    condition=f"NOT {_BLOCKS_FORCE_PUSH}",
    current_value="'Force pushes allowed on ' + n.defaultbranch",
)

_default_branch_admins_not_enforced = _default_branch_fact(
    issue="default_branch_admins_not_enforced",
    name="Repositories whose default branch protection does not apply to admins",
    description=(
        "Unarchived repositories whose default branch is protected only by a classic "
        "branch protection rule that does not apply to administrators. Rulesets "
        "apply to administrators unless they are bypass actors, which Cartography "
        "does not ingest, so repositories with an active ruleset are not evaluated."
    ),
    evaluated=f"{_PROTECTION_VISIBLE} AND size(rulesets) = 0 AND size(bprs) > 0",
    condition="NOT any(b IN bprs WHERE coalesce(b.is_admin_enforced, false))",
    current_value="'Administrators can bypass protection on ' + n.defaultbranch",
)

github_default_branch_protection = Rule(
    id="github_default_branch_protection",
    name="GitHub Default Branch Protection",
    description=(
        "Checks that the default branch of every unarchived repository is protected "
        "by a classic branch protection rule or an active ruleset, requires an "
        "approving review, blocks force pushes and, for classic protection, applies "
        "to administrators. Branch protection rules and rulesets are only visible "
        "with repository administration read access; repositories where the sync "
        "could not read them are not evaluated."
    ),
    output_model=GitHubSecurityConfigurationOutput,
    facts=(
        _default_branch_unprotected,
        _default_branch_no_required_reviews,
        _default_branch_force_push_allowed,
        _default_branch_admins_not_enforced,
    ),
    tags=(
        "github",
        "supply_chain",
        "code_review",
        "configuration",
        "stride:tampering",
    ),
    version="0.1.0",
    references=[
        RuleReference(
            text="About protected branches",
            url="https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches",
        ),
        RuleReference(
            text="About rulesets",
            url="https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets",
        ),
    ],
)


# CODEOWNERS

_codeowners_missing = _default_branch_fact(
    issue="codeowners_missing",
    name="Repositories without CODEOWNERS",
    description=(
        "Unarchived repositories with no CODEOWNERS rule on the default branch, "
        "either because there is no CODEOWNERS file in `.github/`, the root or "
        "`docs/`, or because none of its lines name an owner. Repositories whose "
        "CODEOWNERS locations the sync could not read are not evaluated."
    ),
    evaluated="n.codeowners_readable = true",
    condition=f"NOT {_HAS_CODEOWNERS}",
    current_value="'No CODEOWNERS rules on ' + n.defaultbranch",
)

_codeowners_review_not_required = _default_branch_fact(
    issue="codeowners_review_not_required",
    name="Repositories with CODEOWNERS that do not require code owner review",
    description=(
        "Unarchived repositories with CODEOWNERS rules where neither a branch "
        "protection rule nor an active ruleset on the default branch requires "
        "review from code owners, so ownership is advisory."
    ),
    evaluated=f"{_PROTECTION_VISIBLE} AND n.codeowners_readable = true "
    f"AND {_HAS_CODEOWNERS}",
    condition=f"NOT {_REQUIRES_CODE_OWNER_REVIEW}",
    current_value="'Code owner review not required on ' + n.defaultbranch",
)

github_codeowners_coverage = Rule(
    id="github_codeowners_coverage",
    name="GitHub CODEOWNERS Coverage",
    description=(
        "Finds unarchived repositories without CODEOWNERS rules, and repositories "
        "whose CODEOWNERS are not enforced by a required code owner review on the "
        "default branch."
    ),
    output_model=GitHubSecurityConfigurationOutput,
    facts=(_codeowners_missing, _codeowners_review_not_required),
    tags=("github", "supply_chain", "code_review", "stride:tampering"),
    version="0.1.0",
    references=[
        RuleReference(
            text="About code owners",
            url="https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners",
        ),
    ],
)


# Personal access tokens

# GitHub keeps listing a classic PAT's SAML authorization after the token expires,
# and an expired token cannot authenticate, so it is neither a finding nor counted.
_TOKEN_ACTIVE = "(n.expires_at IS NULL OR n.expires_at > datetime())"

# Fine-grained tokens hang off their organization by RESOURCE; a classic token is
# shared and each organization that authorized it has an AUTHORIZED_CREDENTIAL edge.
_TOKEN_ORG_EDGE = ":RESOURCE|AUTHORIZED_CREDENTIAL"


def _personal_access_token_fact(
    issue: str,
    name: str,
    description: str,
    condition: str,
    current_value: str,
) -> Fact:
    return Fact(
        id=f"github_personal_access_token_{issue}",
        name=name,
        description=description,
        cypher_query=f"""
        MATCH (o:GitHubOrganization)-[{_TOKEN_ORG_EDGE}]->(n:GitHubPersonalAccessToken)
        WHERE {_TOKEN_ACTIVE} AND {condition}
        WITH n, collect(o.username) AS organizations
        RETURN n.token_name AS asset_name, n.id AS asset_id,
            reduce(s = head(organizations), x IN tail(organizations) | s + ', ' + x)
                AS organization, 'personal_access_token_{issue}' AS issue,
            {current_value} AS current_value,
            n.repository_selection AS repository_selection
        """,
        cypher_visual_query=f"""
        MATCH (o:GitHubOrganization)-[{_TOKEN_ORG_EDGE}]->(n:GitHubPersonalAccessToken)
        WHERE {_TOKEN_ACTIVE} AND {condition}
        OPTIONAL MATCH (n)-[:OWNED_BY]->(owner:GitHubUser)
        RETURN o, n, owner
        """,
        cypher_count_query=f"""
        MATCH (:GitHubOrganization)-[{_TOKEN_ORG_EDGE}]->(n:GitHubPersonalAccessToken)
        WHERE {_TOKEN_ACTIVE}
        RETURN count(DISTINCT n) AS count
        """,
        asset_label="GitHubPersonalAccessToken",
        asset_id_field="asset_id",
        identity_fields=("asset_id", "issue"),
        module=Module.GITHUB,
        maturity=Maturity.EXPERIMENTAL,
    )


_classic_personal_access_token = _personal_access_token_fact(
    issue="classic",
    name="Classic personal access tokens with organization access",
    description=(
        "Unexpired classic personal access tokens authorized for an organization. Classic "
        "tokens carry every repository and organization the owner can reach, at the "
        "breadth of their OAuth scopes. Cartography lists them only through SAML "
        "SSO credential authorizations, so they are not visible for organizations "
        "without SAML SSO or on GitHub Enterprise Server."
    ),
    condition="n.token_kind = 'classic'",
    current_value=(
        "'Classic PAT owned by ' + coalesce(n.owner_login, 'unknown user')"
        " + ' with scopes: ' + coalesce("
        "reduce(s = head(n.scopes), x IN tail(n.scopes) | s + ', ' + x), 'none')"
    ),
)

_personal_access_token_no_expiry = _personal_access_token_fact(
    issue="no_expiry",
    name="Personal access tokens without an expiration date",
    description=(
        "Fine-grained or classic personal access tokens with organization access "
        "that never expire."
    ),
    condition="n.expires_at IS NULL",
    current_value=(
        "n.token_kind + ' PAT owned by ' + coalesce(n.owner_login, 'unknown user')"
        " + ' has no expiration date'"
    ),
)

github_personal_access_token_hygiene = Rule(
    id="github_personal_access_token_hygiene",
    name="GitHub Personal Access Token Hygiene",
    description=(
        "Finds classic personal access tokens with organization access and "
        "personal access tokens that never expire. Replace classic tokens with "
        "fine-grained tokens or GitHub Apps scoped to the repositories they need, "
        "and require expiration through the organization's token policy."
    ),
    output_model=GitHubSecurityConfigurationOutput,
    facts=(_classic_personal_access_token, _personal_access_token_no_expiry),
    tags=(
        "github",
        "identity",
        "credentials",
        "stride:spoofing",
        "stride:elevation_of_privilege",
    ),
    version="0.1.0",
    references=[
        RuleReference(
            text="Setting a personal access token policy for your organization",
            url="https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/setting-a-personal-access-token-policy-for-your-organization",
        ),
        RuleReference(
            text="Managing your personal access tokens",
            url="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens",
        ),
    ],
)
