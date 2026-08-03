from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AnthropicFederationRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic federation rule ID.")
    name: PropertyRef = PropertyRef("name", description="Federation rule name.")
    description: PropertyRef = PropertyRef(
        "description",
        description="Free-text description of the federation rule.",
    )
    oauth_scope: PropertyRef = PropertyRef(
        "oauth_scope",
        description=(
            "Scope ceiling for tokens minted through this rule: org:admin, "
            "workspace:developer, workspace:inference, or workspace:manage_tunnels. "
            "Effective permissions are the intersection of this scope and the target "
            "service account's role."
        ),
    )
    token_lifetime_seconds: PropertyRef = PropertyRef(
        "token_lifetime_seconds",
        description="Lifetime of tokens minted through this rule, in seconds.",
    )
    applies_to_all_workspaces: PropertyRef = PropertyRef(
        "applies_to_all_workspaces",
        description=(
            "Whether the rule is enabled for every workspace in the organization, "
            "including workspaces created after it. Ignored for org:admin rules, "
            "which span the whole organization regardless."
        ),
    )
    match_subject_prefix: PropertyRef = PropertyRef(
        "match.subject_prefix",
        description=(
            "Prefix the assertion's sub claim must match. A trailing '*' makes it a "
            "prefix match, which can be far broader than intended: a GitHub Actions "
            "prefix ending in '*' also matches pull_request runs from forks."
        ),
    )
    match_audience: PropertyRef = PropertyRef(
        "match.audience",
        description=(
            "Value the assertion's aud claim must match. When empty, aud must equal "
            "Anthropic's default expected audience for the issuer."
        ),
    )
    match_condition: PropertyRef = PropertyRef(
        "match.condition",
        description="CEL expression evaluated against the assertion's claims.",
    )
    match_claims: PropertyRef = PropertyRef(
        "match_claims",
        description=(
            "Claims the assertion must carry exactly, as sorted 'key=value' entries. "
            "Flattened from a map, which Neo4j cannot store as a node property."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="RFC 3339 timestamp when the rule was created.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="RFC 3339 timestamp when the rule was last updated.",
    )
    archived_at: PropertyRef = PropertyRef(
        "archived_at",
        description=(
            "RFC 3339 timestamp when the rule was archived. Empty while the rule is "
            "live."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicFederationRuleToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicOrganization)-[:RESOURCE]->(:AnthropicFederationRule)
class AnthropicFederationRuleToOrganizationRel(CartographyRelSchema):
    """The organization contains the federation rule."""

    target_node_label: str = "AnthropicOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicFederationRuleToOrganizationRelProperties = (
        AnthropicFederationRuleToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AnthropicFederationRuleToIssuerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicFederationRule)-[:AUTHENTICATED_BY]->(:AnthropicFederationIssuer)
class AnthropicFederationRuleToIssuerRel(CartographyRelSchema):
    """The rule only accepts assertions signed by this issuer."""

    target_node_label: str = "AnthropicFederationIssuer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("issuer_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AUTHENTICATED_BY"
    properties: AnthropicFederationRuleToIssuerRelProperties = (
        AnthropicFederationRuleToIssuerRelProperties()
    )


@dataclass(frozen=True)
class AnthropicFederationRuleToServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicFederationRule)-[:ASSUMES]->(:AnthropicServiceAccount)
class AnthropicFederationRuleToServiceAccountRel(CartographyRelSchema):
    """Tokens minted through this rule act as this service account."""

    target_node_label: str = "AnthropicServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target.service_account_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMES"
    properties: AnthropicFederationRuleToServiceAccountRelProperties = (
        AnthropicFederationRuleToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class AnthropicFederationRuleToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicFederationRule)-[:ENABLED_ON]->(:AnthropicWorkspace)
class AnthropicFederationRuleToWorkspaceRel(CartographyRelSchema):
    """The rule can mint tokens scoped to this workspace.

    Only the explicitly enabled workspaces are edged. A rule with
    applies_to_all_workspaces set covers every workspace without enumerating them,
    so read that property rather than counting these edges.
    """

    target_node_label: str = "AnthropicWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENABLED_ON"
    properties: AnthropicFederationRuleToWorkspaceRelProperties = (
        AnthropicFederationRuleToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AnthropicFederationRuleSchema(CartographyNodeSchema):
    """A rule binding external OIDC identities to an Anthropic service account.

    A federation rule states which assertions, from which issuer, may mint a token
    acting as which service account, and with which scope. Only readable with an
    org:admin OAuth token, never with an Admin API key.
    """

    label: str = "AnthropicFederationRule"
    properties: AnthropicFederationRuleNodeProperties = (
        AnthropicFederationRuleNodeProperties()
    )
    sub_resource_relationship: AnthropicFederationRuleToOrganizationRel = (
        AnthropicFederationRuleToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AnthropicFederationRuleToIssuerRel(),
            AnthropicFederationRuleToServiceAccountRel(),
            AnthropicFederationRuleToWorkspaceRel(),
        ],
    )
