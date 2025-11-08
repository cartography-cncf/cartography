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
class CloudTrailSpaceliftEventNodeProperties(CartographyNodeProperties):
    """
    Properties for a CloudTrail Spacelift Event node.
    Represents a single CloudTrail event from a Spacelift run.
    One event can affect multiple EC2 instances (e.g., RunInstances creating multiple instances).
    """

    id: PropertyRef = PropertyRef("id")
    event_time: PropertyRef = PropertyRef("event_time")
    event_name: PropertyRef = PropertyRef("event_name")
    aws_account: PropertyRef = PropertyRef("aws_account")
    aws_region: PropertyRef = PropertyRef("aws_region")
    run_id: PropertyRef = PropertyRef("run_id")
    instance_ids: PropertyRef = PropertyRef("instance_ids")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudTrailSpaceliftEventToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudTrailSpaceliftEventToAccountRel(CartographyRelSchema):
    target_node_label: str = "SpaceliftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("spacelift_account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudTrailSpaceliftEventToAccountRelProperties = (
        CloudTrailSpaceliftEventToAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudTrailSpaceliftEventToRunRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudTrailSpaceliftEventToRunRel(CartographyRelSchema):
    """
    FROM_RUN relationship from a CloudTrailSpaceliftEvent to the SpaceliftRun that generated it.
    (:CloudTrailSpaceliftEvent)-[:FROM_RUN]->(:SpaceliftRun)
    """

    target_node_label: str = "SpaceliftRun"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("run_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FROM_RUN"
    properties: CloudTrailSpaceliftEventToRunRelProperties = (
        CloudTrailSpaceliftEventToRunRelProperties()
    )


@dataclass(frozen=True)
class CloudTrailSpaceliftEventToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudTrailSpaceliftEventToEC2InstanceRel(CartographyRelSchema):
    """
    AFFECTED relationship from a CloudTrailSpaceliftEvent to EC2Instances it affected.
    (:CloudTrailSpaceliftEvent)-[:AFFECTED]->(:EC2Instance)

    Uses one-to-many relationship since a single CloudTrail event can affect multiple instances.
    """

    target_node_label: str = "EC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "instanceid": PropertyRef("instance_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTED"
    properties: CloudTrailSpaceliftEventToEC2InstanceRelProperties = (
        CloudTrailSpaceliftEventToEC2InstanceRelProperties()
    )


@dataclass(frozen=True)
class CloudTrailSpaceliftEventSchema(CartographyNodeSchema):
    """
    Represents CloudTrail events from Spacelift runs interacting with EC2 instances.
    """

    label: str = "CloudTrailSpaceliftEvent"
    properties: CloudTrailSpaceliftEventNodeProperties = (
        CloudTrailSpaceliftEventNodeProperties()
    )
    sub_resource_relationship: CloudTrailSpaceliftEventToAccountRel = (
        CloudTrailSpaceliftEventToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudTrailSpaceliftEventToRunRel(),
            CloudTrailSpaceliftEventToEC2InstanceRel(),
        ]
    )
