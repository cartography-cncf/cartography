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
class AnthropicRateLimitNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Synthesised from the scope, group type, models and limit type. The API "
            "returns no identifier for a rate limit."
        ),
    )
    group_type: PropertyRef = PropertyRef(
        "group_type",
        description=(
            "Family the limit applies to: batch, files, model_group, skills, "
            "token_count, or web_search."
        ),
    )
    limit_type: PropertyRef = PropertyRef(
        "limit_type",
        description="Quantity being limited, e.g. requests or tokens per minute.",
    )
    value: PropertyRef = PropertyRef("value", description="The configured limit.")
    org_limit: PropertyRef = PropertyRef(
        "org_limit",
        description=(
            "Organization-level value this workspace limit overrides. Empty on "
            "organization-level limits."
        ),
    )
    models: PropertyRef = PropertyRef(
        "models",
        description="Models the limit applies to. Empty when it applies to all.",
    )
    workspace_id: PropertyRef = PropertyRef(
        "workspace_id",
        description=(
            "Workspace this limit overrides, or empty for an organization-level "
            "limit."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicRateLimitToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicOrganization)-[:RESOURCE]->(:AnthropicRateLimit)
class AnthropicRateLimitToOrganizationRel(CartographyRelSchema):
    """The organization the rate limit belongs to."""

    target_node_label: str = "AnthropicOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicRateLimitToOrganizationRelProperties = (
        AnthropicRateLimitToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AnthropicRateLimitToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicWorkspace)-[:CONTAINS]->(:AnthropicRateLimit)
class AnthropicRateLimitToWorkspaceRel(CartographyRelSchema):
    """The workspace this limit overrides. Absent on organization-level limits."""

    target_node_label: str = "AnthropicWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AnthropicRateLimitToWorkspaceRelProperties = (
        AnthropicRateLimitToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AnthropicRateLimitSchema(CartographyNodeSchema):
    """A configured rate limit on an Anthropic organization or workspace.

    Only overrides are returned: a group with no node here inherits the
    organization's limit, which is not the same as being unlimited.
    """

    label: str = "AnthropicRateLimit"
    properties: AnthropicRateLimitNodeProperties = AnthropicRateLimitNodeProperties()
    sub_resource_relationship: AnthropicRateLimitToOrganizationRel = (
        AnthropicRateLimitToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AnthropicRateLimitToWorkspaceRel(),
        ],
    )
