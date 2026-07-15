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
class RedshiftClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("arn", description="Same as arn")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) for the Redshift cluster",
    )
    availability_zone: PropertyRef = PropertyRef(
        "AvailabilityZone",
        description="Specifies the name of the Availability Zone the cluster is located in",
    )
    cluster_create_time: PropertyRef = PropertyRef(
        "ClusterCreateTime",
        description="Provides the date and time the cluster was created",
    )
    cluster_identifier: PropertyRef = PropertyRef(
        "ClusterIdentifier", description="The unique identifier of the cluster."
    )
    cluster_revision_number: PropertyRef = PropertyRef(
        "ClusterRevisionNumber",
        description="The specific revision number of the database in the cluster.",
    )
    cluster_status: PropertyRef = PropertyRef(
        "ClusterStatus", description="The current state of the cluster."
    )
    db_name: PropertyRef = PropertyRef(
        "DBName",
        description="The name of the initial database that was created when the cluster was created. This same name is returned for the life of the cluster. If an initial database was not specified, a database named devdev was created by default.",
    )
    encrypted: PropertyRef = PropertyRef(
        "Encrypted", description="Specifies whether the cluster has encryption enabled"
    )
    endpoint_address: PropertyRef = PropertyRef(
        "_endpoint_address", description="DNS name of the Redshift cluster endpoint"
    )
    endpoint_port: PropertyRef = PropertyRef(
        "_endpoint_port",
        description="The port that the Redshift cluster's endpoint is listening on",
    )
    master_username: PropertyRef = PropertyRef(
        "MasterUsername",
        description="The master user name for the cluster. This name is used to connect to the database that is specified in the DBName parameter.",
    )
    node_type: PropertyRef = PropertyRef(
        "NodeType", description="The node type for the nodes in the cluster."
    )
    number_of_nodes: PropertyRef = PropertyRef(
        "NumberOfNodes", description="The number of compute nodes in the cluster."
    )
    publicly_accessible: PropertyRef = PropertyRef(
        "PubliclyAccessible",
        description="A boolean value that, if true, indicates that the cluster can be accessed from a public network.",
    )
    vpc_id: PropertyRef = PropertyRef(
        "VpcId",
        description="The identifier of the VPC the cluster is in, if the cluster is in a VPC.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS Region containing this `AWSRedshiftCluster` node.",
    )


@dataclass(frozen=True)
class RedshiftClusterToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:AWSAccount)-[:RESOURCE]->(:AWSRedshiftCluster)
@dataclass(frozen=True)
class RedshiftClusterToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSRedshiftCluster`."

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


# (:AWSRedshiftCluster)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)
@dataclass(frozen=True)
class RedshiftClusterToEC2SecurityGroupRel(CartographyRelSchema):
    "Represents a `MEMBER_OF_EC2_SECURITY_GROUP` relationship from `AWSRedshiftCluster` to `AWSEC2SecurityGroup`."

    target_node_label: str = "AWSEC2SecurityGroup"
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


# (:AWSRedshiftCluster)-[:STS_ASSUMEROLE_ALLOW]->(:AWSPrincipal)
@dataclass(frozen=True)
class RedshiftClusterToAWSPrincipalRel(CartographyRelSchema):
    "Represents a `STS_ASSUMEROLE_ALLOW` relationship from `AWSRedshiftCluster` to `AWSPrincipal`."

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


# (:AWSRedshiftCluster)-[:MEMBER_OF_AWS_VPC]->(:AWSVpc)
@dataclass(frozen=True)
class RedshiftClusterToAWSVpcRel(CartographyRelSchema):
    "Represents a `MEMBER_OF_AWS_VPC` relationship from `AWSRedshiftCluster` to `AWSVpc`."

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
    "Represents an `AWSRedshiftCluster` node in the AWS graph."

    label: str = "AWSRedshiftCluster"
    # DEPRECATED: legacy RedshiftCluster node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["RedshiftCluster"])
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
