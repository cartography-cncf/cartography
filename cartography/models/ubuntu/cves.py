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
class UbuntuCVENodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    description: PropertyRef = PropertyRef("description")
    ubuntu_description: PropertyRef = PropertyRef("ubuntu_description")
    priority: PropertyRef = PropertyRef("priority", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    cvss3: PropertyRef = PropertyRef("cvss3")
    published: PropertyRef = PropertyRef("published")
    updated_at: PropertyRef = PropertyRef("updated_at")
    codename: PropertyRef = PropertyRef("codename")
    mitigation: PropertyRef = PropertyRef("mitigation")
    attack_vector: PropertyRef = PropertyRef("attack_vector")
    attack_complexity: PropertyRef = PropertyRef("attack_complexity")
    base_score: PropertyRef = PropertyRef("base_score")
    base_severity: PropertyRef = PropertyRef("base_severity")
    confidentiality_impact: PropertyRef = PropertyRef("confidentiality_impact")
    integrity_impact: PropertyRef = PropertyRef("integrity_impact")
    availability_impact: PropertyRef = PropertyRef("availability_impact")


@dataclass(frozen=True)
class UbuntuCVEToUbuntuCVEFeedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class UbuntuCVEToUbuntuCVEFeedRel(CartographyRelSchema):
    """(:UbuntuCVE)<-[:RESOURCE]-(:UbuntuCVEFeed)"""
    target_node_label: str = "UbuntuCVEFeed"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FEED_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UbuntuCVEToUbuntuCVEFeedRelProperties = UbuntuCVEToUbuntuCVEFeedRelProperties()


@dataclass(frozen=True)
class UbuntuCVESchema(CartographyNodeSchema):
    label: str = "UbuntuCVE"
    properties: UbuntuCVENodeProperties = UbuntuCVENodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["CVE"])
    sub_resource_relationship: UbuntuCVEToUbuntuCVEFeedRel = UbuntuCVEToUbuntuCVEFeedRel()
