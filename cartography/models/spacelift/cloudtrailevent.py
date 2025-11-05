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
class CloudTrailEventNodeProperties(CartographyNodeProperties):
    """
    Properties for a CloudTrail Event node.
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
class CloudTrailEventToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudTrailEventToAccountRel(CartographyRelSchema):
    target_node_label: str = "SpaceliftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudTrailEventToAccountRelProperties = (
        CloudTrailEventToAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudTrailEventToRunRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudTrailEventToRunRel(CartographyRelSchema):
    """
    FROM_RUN relationship from a CloudTrailEvent to the SpaceliftRun that generated it.
    (:CloudTrailEvent)-[:FROM_RUN]->(:SpaceliftRun)
    """

    target_node_label: str = "SpaceliftRun"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("run_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FROM_RUN"
    properties: CloudTrailEventToRunRelProperties = CloudTrailEventToRunRelProperties()


@dataclass(frozen=True)
class CloudTrailEventToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudTrailEventToEC2InstanceRel(CartographyRelSchema):
    """
    AFFECTED relationship from a CloudTrailEvent to EC2Instances it affected.
    (:CloudTrailEvent)-[:AFFECTED]->(:EC2Instance)

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
    properties: CloudTrailEventToEC2InstanceRelProperties = (
        CloudTrailEventToEC2InstanceRelProperties()
    )


@dataclass(frozen=True)
class CloudTrailEventSchema(CartographyNodeSchema):
    """
    Represents CloudTrail events from Spacelift runs interacting with EC2 instances.
    """

    label: str = "CloudTrailEvent"
    properties: CloudTrailEventNodeProperties = CloudTrailEventNodeProperties()
    sub_resource_relationship: CloudTrailEventToAccountRel = (
        CloudTrailEventToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudTrailEventToRunRel(),
            CloudTrailEventToEC2InstanceRel(),
        ]
    )
