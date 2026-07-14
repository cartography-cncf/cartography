from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class CircleCIPolicyNodeProperties(CartographyNodeProperties):
    # Synthesized stable id: "{org_id}:{context}:{name}".
    id: PropertyRef = PropertyRef("id", description="Synthesized CircleCI policy ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Policy name."
    )
    context: PropertyRef = PropertyRef(
        "context", description="CircleCI policy context."
    )
    content: PropertyRef = PropertyRef("content", description="Policy source in Rego.")
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Policy creation timestamp."
    )
    created_by: PropertyRef = PropertyRef(
        "created_by", description="Identity that created the policy."
    )
    # Per-context decision toggle (same for every policy in the context).
    decision_enabled: PropertyRef = PropertyRef(
        "decision_enabled",
        description="Whether policy decisions are enabled for the context.",
    )


@dataclass(frozen=True)
class CircleCIPolicyToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIOrganization)-[:RESOURCE]->(:CircleCIPolicy)
class CircleCIPolicyToOrganizationRel(CartographyRelSchema):
    """The CircleCI organization contains the configuration policy."""

    target_node_label: str = "CircleCIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIPolicyToOrganizationRelProperties = (
        CircleCIPolicyToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class CircleCIPolicySchema(CartographyNodeSchema):
    """A CircleCI configuration policy in an organization policy bundle."""

    label: str = "CircleCIPolicy"
    properties: CircleCIPolicyNodeProperties = CircleCIPolicyNodeProperties()
    sub_resource_relationship: CircleCIPolicyToOrganizationRel = (
        CircleCIPolicyToOrganizationRel()
    )
