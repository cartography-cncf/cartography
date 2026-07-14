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
class SubImageFrameworkNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Framework ID.")
    name: PropertyRef = PropertyRef("name", description="Full framework name.")
    short_name: PropertyRef = PropertyRef(
        "short_name",
        description="Short framework name.",
    )
    scope: PropertyRef = PropertyRef(
        "scope",
        description="Framework scope, such as aws or all.",
    )
    revision: PropertyRef = PropertyRef(
        "revision",
        description="Framework revision.",
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="Whether the framework is enabled.",
    )
    enabled_at: PropertyRef = PropertyRef(
        "enabled_at",
        description="Timestamp when the framework was enabled.",
    )
    disabled_at: PropertyRef = PropertyRef(
        "disabled_at",
        description="Timestamp when the framework was disabled.",
    )
    rule_count: PropertyRef = PropertyRef(
        "rule_count",
        description="Number of rules in the framework.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class SubImageFrameworkToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SubImageTenant)-[:RESOURCE]->(:SubImageFramework)
class SubImageFrameworkToTenantRel(CartographyRelSchema):
    """The tenant contains the compliance framework."""

    target_node_label: str = "SubImageTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SubImageFrameworkToTenantRelProperties = (
        SubImageFrameworkToTenantRelProperties()
    )


@dataclass(frozen=True)
class SubImageFrameworkSchema(CartographyNodeSchema):
    """A compliance framework configured in SubImage."""

    label: str = "SubImageFramework"
    properties: SubImageFrameworkNodeProperties = SubImageFrameworkNodeProperties()
    sub_resource_relationship: SubImageFrameworkToTenantRel = (
        SubImageFrameworkToTenantRel()
    )
