from dataclasses import dataclass

from cartography.models.aws.extra_labels import KEY_PAIR
from cartography.models.aws.extra_labels import LEGACY_EC2_KEY_PAIR
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
class EC2KeyPairNodeProperties(CartographyNodeProperties):
    """
    Properties for EC2 keypairs from describe-key-pairs
    """

    id: PropertyRef = PropertyRef("KeyPairArn", description="same as `arn`")
    arn: PropertyRef = PropertyRef(
        "KeyPairArn",
        extra_index=True,
        description="AWS-unique identifier for this object",
    )
    keyname: PropertyRef = PropertyRef(
        "KeyName", description="The name of the key pair"
    )
    keyfingerprint: PropertyRef = PropertyRef(
        "KeyFingerprint",
        extra_index=True,
        description="The fingerprint of the public key",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2KeyPairToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2KeyPairToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2KeyPairToAWSAccountRelRelProperties = (
        EC2KeyPairToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class EC2KeyPairSchema(CartographyNodeSchema):
    """Representation of an AWS [EC2 Key Pair](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_KeyPairInfo.html)"""

    # Implementation note:
    # Schema for EC2 keypairs from describe-key-pairs

    label: str = "AWSEC2KeyPair"
    # DEPRECATED: legacy EC2KeyPair node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [LEGACY_EC2_KEY_PAIR, KEY_PAIR]
    )
    properties: EC2KeyPairNodeProperties = EC2KeyPairNodeProperties()
    sub_resource_relationship: EC2KeyPairToAWSAccountRel = EC2KeyPairToAWSAccountRel()
