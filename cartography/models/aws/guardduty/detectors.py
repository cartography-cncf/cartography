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
class GuardDutyDetectorNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    accountid: PropertyRef = PropertyRef("accountid")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    status: PropertyRef = PropertyRef("status")
    findingpublishingfrequency: PropertyRef = PropertyRef("findingpublishingfrequency")
    service_role: PropertyRef = PropertyRef("service_role")
    createdat: PropertyRef = PropertyRef("createdat")
    updatedat: PropertyRef = PropertyRef("updatedat")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyDetectorToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyDetectorToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GuardDutyDetectorToAWSAccountRelRelProperties = (
        GuardDutyDetectorToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class GuardDutyDetectorSchema(CartographyNodeSchema):
    label: str = "GuardDutyDetector"
    properties: GuardDutyDetectorNodeProperties = GuardDutyDetectorNodeProperties()
    sub_resource_relationship: GuardDutyDetectorToAWSAccountRel = (
        GuardDutyDetectorToAWSAccountRel()
    )
