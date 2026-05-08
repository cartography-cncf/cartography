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
class RedshiftClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("arn")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    arn: PropertyRef = PropertyRef("arn", extra_index=True)
    availability_zone: PropertyRef = PropertyRef("AvailabilityZone")
    cluster_create_time: PropertyRef = PropertyRef("ClusterCreateTime")
    cluster_identifier: PropertyRef = PropertyRef("ClusterIdentifier")
    cluster_revision_number: PropertyRef = PropertyRef("ClusterRevisionNumber")
    cluster_status: PropertyRef = PropertyRef("ClusterStatus")
    db_name: PropertyRef = PropertyRef("DBName")
    encrypted: PropertyRef = PropertyRef("Encrypted")
    endpoint_address: PropertyRef = PropertyRef("_endpoint_address")
    endpoint_port: PropertyRef = PropertyRef("_endpoint_port")
    master_username: PropertyRef = PropertyRef("MasterUsername")
    node_type: PropertyRef = PropertyRef("NodeType")
    number_of_nodes: PropertyRef = PropertyRef("NumberOfNodes")
    publicly_accessible: PropertyRef = PropertyRef("PubliclyAccessible")
    vpc_id: PropertyRef = PropertyRef("VpcId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)


@dataclass(frozen=True)
class RedshiftClusterToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:AWSAccount)-[:RESOURCE]->(:RedshiftCluster)
@dataclass(frozen=True)
class RedshiftClusterToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RedshiftClusterToAWSAccountRelProperties = (
        RedshiftClusterToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class RedshiftClusterToEC2SecurityGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:RedshiftCluster)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:EC2SecurityGroup)
@dataclass(frozen=True)
class RedshiftClusterToEC2SecurityGroupRel(CartographyRelSchema):
    target_node_label: str = "EC2SecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_security_group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: RedshiftClusterToEC2SecurityGroupRelProperties = (
        RedshiftClusterToEC2SecurityGroupRelProperties()
    )


@dataclass(frozen=True)
class RedshiftClusterToAWSPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:RedshiftCluster)-[:STS_ASSUMEROLE_ALLOW]->(:AWSPrincipal)
@dataclass(frozen=True)
class RedshiftClusterToAWSPrincipalRel(CartographyRelSchema):
    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("_iam_role_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "STS_ASSUMEROLE_ALLOW"
    properties: RedshiftClusterToAWSPrincipalRelProperties = (
        RedshiftClusterToAWSPrincipalRelProperties()
    )


@dataclass(frozen=True)
class RedshiftClusterToAWSVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:RedshiftCluster)-[:MEMBER_OF_AWS_VPC]->(:AWSVpc)
@dataclass(frozen=True)
class RedshiftClusterToAWSVpcRel(CartographyRelSchema):
    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VpcId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_AWS_VPC"
    properties: RedshiftClusterToAWSVpcRelProperties = (
        RedshiftClusterToAWSVpcRelProperties()
    )


@dataclass(frozen=True)
class RedshiftClusterSchema(CartographyNodeSchema):
    label: str = "RedshiftCluster"
    properties: RedshiftClusterNodeProperties = RedshiftClusterNodeProperties()
    sub_resource_relationship: RedshiftClusterToAWSAccountRel = (
        RedshiftClusterToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RedshiftClusterToEC2SecurityGroupRel(),
            RedshiftClusterToAWSPrincipalRel(),
            RedshiftClusterToAWSVpcRel(),
        ]
    )
