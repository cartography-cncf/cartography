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
class RenderIPAllowRuleNodeProperties(CartographyNodeProperties):
    # Render's ipAllowList entries have no id of their own; the governed resource's id
    # plus the CIDR block is unique per resource and stable across syncs.
    id: PropertyRef = PropertyRef(
        "id", description="Synthetic id: `<governed resource id>/<CIDR block>`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cidr_block: PropertyRef = PropertyRef(
        "cidrBlock", extra_index=True, description="Allowed CIDR block."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Free-text label for this rule, e.g. `everywhere`."
    )
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    resource_id: PropertyRef = PropertyRef(
        "resourceId",
        extra_index=True,
        description="ID of the resource this rule governs.",
    )
    resource_type: PropertyRef = PropertyRef(
        "resourceType",
        description="Node label of the resource this rule governs (e.g. `RenderService`).",
    )


@dataclass(frozen=True)
class RenderIPAllowRuleToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderIPAllowRule)
class RenderIPAllowRuleToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to an IP allow rule that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderIPAllowRuleToTenantRelProperties = (
        RenderIPAllowRuleToTenantRelProperties()
    )


# A single RenderIPAllowRule row only ever has one of environment_id / service_id /
# postgres_id / key_value_id populated (see cartography/intel/render/ipallowrules.py);
# the other three matchers below are simply absent on that row, so only the one
# matching target label produces an edge. This mirrors the optional-match pattern
# already used elsewhere (e.g. RenderEnvironment's optional project_id).


@dataclass(frozen=True)
class RenderIPAllowRuleToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderEnvironment)-[:GOVERNS]->(:RenderIPAllowRule)
class RenderIPAllowRuleToEnvironmentRel(CartographyRelSchema):
    """Connects a Render environment to an IP allow rule that governs access to it."""

    target_node_label: str = "RenderEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("environment_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "GOVERNS"
    properties: RenderIPAllowRuleToEnvironmentRelProperties = (
        RenderIPAllowRuleToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class RenderIPAllowRuleToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderService)-[:GOVERNS]->(:RenderIPAllowRule)
class RenderIPAllowRuleToServiceRel(CartographyRelSchema):
    """Connects a Render service to an IP allow rule that governs access to it."""

    target_node_label: str = "RenderService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "GOVERNS"
    properties: RenderIPAllowRuleToServiceRelProperties = (
        RenderIPAllowRuleToServiceRelProperties()
    )


@dataclass(frozen=True)
class RenderIPAllowRuleToPostgresRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderPostgres)-[:GOVERNS]->(:RenderIPAllowRule)
class RenderIPAllowRuleToPostgresRel(CartographyRelSchema):
    """Connects a Render Postgres instance to an IP allow rule that governs access to it."""

    target_node_label: str = "RenderPostgres"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("postgres_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "GOVERNS"
    properties: RenderIPAllowRuleToPostgresRelProperties = (
        RenderIPAllowRuleToPostgresRelProperties()
    )


@dataclass(frozen=True)
class RenderIPAllowRuleToKeyValueRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderKeyValue)-[:GOVERNS]->(:RenderIPAllowRule)
class RenderIPAllowRuleToKeyValueRel(CartographyRelSchema):
    """Connects a Render Key Value instance to an IP allow rule that governs access to it."""

    target_node_label: str = "RenderKeyValue"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("key_value_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "GOVERNS"
    properties: RenderIPAllowRuleToKeyValueRelProperties = (
        RenderIPAllowRuleToKeyValueRelProperties()
    )


@dataclass(frozen=True)
class RenderIPAllowRuleSchema(CartographyNodeSchema):
    """
    An IP allow-list rule (CIDR block) governing access to a Render environment,
    service, Postgres instance, or Key Value instance.
    """

    label: str = "RenderIPAllowRule"
    properties: RenderIPAllowRuleNodeProperties = RenderIPAllowRuleNodeProperties()
    sub_resource_relationship: RenderIPAllowRuleToTenantRel = (
        RenderIPAllowRuleToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RenderIPAllowRuleToEnvironmentRel(),
            RenderIPAllowRuleToServiceRel(),
            RenderIPAllowRuleToPostgresRel(),
            RenderIPAllowRuleToKeyValueRel(),
        ],
    )
