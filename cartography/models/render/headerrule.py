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
class RenderHeaderRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Render header rule.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    service_id: PropertyRef = PropertyRef(
        "serviceId",
        extra_index=True,
        description="ID of the service this rule applies to.",
    )
    path: PropertyRef = PropertyRef(
        "path", description="Request path this header rule applies to."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="HTTP response header name."
    )
    value: PropertyRef = PropertyRef("value", description="HTTP response header value.")


@dataclass(frozen=True)
class RenderHeaderRuleToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderHeaderRule)
class RenderHeaderRuleToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to a header rule that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderHeaderRuleToTenantRelProperties = (
        RenderHeaderRuleToTenantRelProperties()
    )


@dataclass(frozen=True)
class RenderHeaderRuleToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderService)-[:HAS_HEADER_RULE]->(:RenderHeaderRule)
class RenderHeaderRuleToServiceRel(CartographyRelSchema):
    """Connects a Render service to a response header rule configured on it."""

    target_node_label: str = "RenderService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("serviceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_HEADER_RULE"
    properties: RenderHeaderRuleToServiceRelProperties = (
        RenderHeaderRuleToServiceRelProperties()
    )


@dataclass(frozen=True)
class RenderHeaderRuleSchema(CartographyNodeSchema):
    """
    A custom HTTP response header rule configured on a Render service.

    Header values here are sent to every client on every response - by definition not
    secret - so unlike RenderSecretFile/RenderEnvVar, the value is safe to ingest as-is.
    """

    label: str = "RenderHeaderRule"
    properties: RenderHeaderRuleNodeProperties = RenderHeaderRuleNodeProperties()
    sub_resource_relationship: RenderHeaderRuleToTenantRel = (
        RenderHeaderRuleToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [RenderHeaderRuleToServiceRel()],
    )
