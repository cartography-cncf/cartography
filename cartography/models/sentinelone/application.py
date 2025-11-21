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
class S1ApplicationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    vendor: PropertyRef = PropertyRef("vendor")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S1ApplicationToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:S1Application)<-[:RESOURCE]-(:S1Account)
class S1ApplicationToAccount(CartographyRelSchema):
    target_node_label: str = "S1Account"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("S1_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: S1ApplicationToAccountRelProperties = (
        S1ApplicationToAccountRelProperties()
    )


@dataclass(frozen=True)
class S1ApplicationSchema(CartographyNodeSchema):
    label: str = "S1Application"
    properties: S1ApplicationNodeProperties = S1ApplicationNodeProperties()
    sub_resource_relationship: S1ApplicationToAccount = S1ApplicationToAccount()
