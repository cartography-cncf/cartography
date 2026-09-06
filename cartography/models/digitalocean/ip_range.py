from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.extra_labels import IP_RANGE


@dataclass(frozen=True)
class DOIpRangeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="IP address or CIDR used as the identifier for this selector.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    range: PropertyRef = PropertyRef(
        "range",
        extra_index=True,
        description="IP address or CIDR selected by a DigitalOcean firewall rule.",
    )


@dataclass(frozen=True)
class DOIpRangeToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DOIpRangeToAccountRel(CartographyRelSchema):
    """A DigitalOcean account contains the IP range selector as a resource."""

    target_node_label: str = "DOAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DOIpRangeToAccountRelProperties = DOIpRangeToAccountRelProperties()


@dataclass(frozen=True)
class DOIpRangeSchema(CartographyNodeSchema):
    """An IP address or CIDR selector used by a DigitalOcean firewall rule."""

    label: str = "DOIpRange"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([IP_RANGE])
    properties: DOIpRangeProperties = DOIpRangeProperties()
    sub_resource_relationship: DOIpRangeToAccountRel = DOIpRangeToAccountRel()
