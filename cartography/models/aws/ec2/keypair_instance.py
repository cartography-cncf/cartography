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
class EC2KeyPairInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("KeyPairArn", description="same as `arn`")
    arn: PropertyRef = PropertyRef(
        "KeyPairArn",
        extra_index=True,
        description="AWS-unique identifier for this object",
    )
    keyname: PropertyRef = PropertyRef(
        "KeyName", description="The name of the key pair"
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class EC2KeyPairInstanceToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2KeyPairInstanceToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEC2KeyPair`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2KeyPairInstanceToAWSAccountRelRelProperties = (
        EC2KeyPairInstanceToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class EC2KeyPairInstanceToEC2InstanceRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2KeyPairInstanceToEC2InstanceRel(CartographyRelSchema):
    "Represents a `SSH_LOGIN_TO` relationship from `AWSEC2KeyPair` to `AWSEC2Instance`."

    target_node_label: str = "AWSEC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("InstanceId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SSH_LOGIN_TO"
    properties: EC2KeyPairInstanceToEC2InstanceRelRelProperties = (
        EC2KeyPairInstanceToEC2InstanceRelRelProperties()
    )


@dataclass(frozen=True)
class EC2KeyPairInstanceSchema(CartographyNodeSchema):
    "Represents an Amazon EC2 key pair."

    # Implementation note:
    # EC2 keypairs as known by describe-instances.

    label: str = "AWSEC2KeyPair"
    # DEPRECATED: legacy EC2KeyPair node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EC2KeyPair", "KeyPair"])
    properties: EC2KeyPairInstanceNodeProperties = EC2KeyPairInstanceNodeProperties()
    sub_resource_relationship: EC2KeyPairInstanceToAWSAccountRel = (
        EC2KeyPairInstanceToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2KeyPairInstanceToEC2InstanceRel(),
        ],
    )
