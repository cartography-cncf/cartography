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
class DopplerTrustedIPNodeProperties(CartographyNodeProperties):
    # id is the composite "{project}/{config}/{cidr}" built in transform.
    id: PropertyRef = PropertyRef("id")
    cidr: PropertyRef = PropertyRef("cidr")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerTrustedIPToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerTrustedIP)
class DopplerTrustedIPToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerTrustedIPToWorkplaceRelProperties = (
        DopplerTrustedIPToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerTrustedIPToConfigRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerConfig)-[:TRUSTS]->(:DopplerTrustedIP)
class DopplerTrustedIPToConfigRel(CartographyRelSchema):
    target_node_label: str = "DopplerConfig"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("config_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TRUSTS"
    properties: DopplerTrustedIPToConfigRelProperties = (
        DopplerTrustedIPToConfigRelProperties()
    )


@dataclass(frozen=True)
class DopplerTrustedIPSchema(CartographyNodeSchema):
    label: str = "DopplerTrustedIP"
    properties: DopplerTrustedIPNodeProperties = DopplerTrustedIPNodeProperties()
    sub_resource_relationship: DopplerTrustedIPToWorkplaceRel = (
        DopplerTrustedIPToWorkplaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DopplerTrustedIPToConfigRel()],
    )
