from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class CloudTrailSpaceliftEventNodeProperties(CartographyNodeProperties):
    """
    Properties for a Spacelift CloudTrail Event node.
    Represents a single CloudTrail event from a Spacelift run.
    One event can affect multiple EC2 instances (e.g., RunInstances creating multiple instances).
    """

    id: PropertyRef = PropertyRef("id", description="CloudTrail event ID.")
    event_time: PropertyRef = PropertyRef(
        "event_time", description="Timestamp of the CloudTrail event."
    )
    event_name: PropertyRef = PropertyRef(
        "event_name", description="AWS API action recorded by CloudTrail."
    )
    aws_account: PropertyRef = PropertyRef(
        "aws_account", description="AWS account ID associated with the event."
    )
    aws_region: PropertyRef = PropertyRef(
        "aws_region", description="AWS region associated with the event."
    )
    run_id: PropertyRef = PropertyRef(
        "run_id", description="ID of the Spacelift run that produced the event."
    )
    instance_ids: PropertyRef = PropertyRef(
        "instance_ids", description="EC2 instance IDs affected by the event."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class CloudTrailSpaceliftEventToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudTrailSpaceliftEventToAccountRel(CartographyRelSchema):
    """A Spacelift account contains a CloudTrail event attributed to a run."""

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
    A CloudTrail Spacelift event comes from the Spacelift run that generated it.

    (:SpaceliftCloudTrailEvent)-[:FROM_RUN]->(:SpaceliftRun)
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
    A CloudTrail Spacelift event affected one or more EC2 instances.

    (:SpaceliftCloudTrailEvent)-[:AFFECTED]->(:AWSEC2Instance)

    Uses a one-to-many relationship because a single event can affect multiple
    instances.
    """

    target_node_label: str = "AWSEC2Instance"
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
    """A CloudTrail event from a Spacelift run that interacted with EC2."""

    label: str = "SpaceliftCloudTrailEvent"
    # DEPRECATED: legacy CloudTrailSpaceliftEvent node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["CloudTrailSpaceliftEvent"])
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
