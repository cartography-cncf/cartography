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
class GuardDutyDetectorNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="The unique identifier for the GuardDuty detector"
    )
    accountid: PropertyRef = PropertyRef(
        "accountid", description="The AWS Account ID the detector belongs to"
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS Region where the detector is deployed",
    )
    status: PropertyRef = PropertyRef(
        "status", description="Whether the detector is enabled or disabled"
    )
    findingpublishingfrequency: PropertyRef = PropertyRef(
        "findingpublishingfrequency",
        description="Frequency with which GuardDuty publishes findings",
    )
    service_role: PropertyRef = PropertyRef(
        "service_role", description="IAM service role used by GuardDuty"
    )
    createdat: PropertyRef = PropertyRef(
        "createdat", description="Timestamp when the detector was created"
    )
    updatedat: PropertyRef = PropertyRef(
        "updatedat", description="Timestamp when the detector was last updated"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class GuardDutyDetectorToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyDetectorToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSGuardDutyDetector`."

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
    "Represents an `AWSGuardDutyDetector` node in the AWS graph."

    label: str = "AWSGuardDutyDetector"
    # DEPRECATED: legacy GuardDutyDetector node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["GuardDutyDetector"])
    properties: GuardDutyDetectorNodeProperties = GuardDutyDetectorNodeProperties()
    sub_resource_relationship: GuardDutyDetectorToAWSAccountRel = (
        GuardDutyDetectorToAWSAccountRel()
    )
