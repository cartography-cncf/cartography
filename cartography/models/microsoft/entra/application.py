from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EntraApplicationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    app_id: PropertyRef = PropertyRef("app_id")
    display_name: PropertyRef = PropertyRef("display_name")
    publisher_domain: PropertyRef = PropertyRef("publisher_domain")
    sign_in_audience: PropertyRef = PropertyRef("sign_in_audience")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraApplicationToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraApplicationToTenantRel(CartographyRelSchema):
    target_node_label: str = "EntraTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EntraApplicationToTenantRelProperties = (
        EntraApplicationToTenantRelProperties()
    )


@dataclass(frozen=True)
class EntraApplicationSchema(CartographyNodeSchema):
    label: str = "EntraApplication"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ThirdPartyApp"])
    properties: EntraApplicationNodeProperties = EntraApplicationNodeProperties()
    sub_resource_relationship: EntraApplicationToTenantRel = (
        EntraApplicationToTenantRel()
    )
