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
class EMRClusterNodeProperties(CartographyNodeProperties):
    arn: PropertyRef = PropertyRef(
        "ClusterArn",
        extra_index=True,
        description="AWS-unique identifier for this object",
    )
    auto_terminate: PropertyRef = PropertyRef(
        "AutoTerminate",
        description="Specifies whether the cluster should terminate after completing all steps.",
    )
    autoscaling_role: PropertyRef = PropertyRef(
        "AutoScalingRole", description="An IAM role for automatic scaling policies."
    )
    custom_ami_id: PropertyRef = PropertyRef(
        "CustomAmiId",
        description="The ID of a custom Amazon EBS-backed Linux AMI if the cluster uses a custom AMI.",
    )
    id: PropertyRef = PropertyRef("Id", description="The Id of the EMR Cluster.")
    instance_collection_type: PropertyRef = PropertyRef(
        "InstanceCollectionType",
        description="The instance group configuration of the cluster. A value of INSTANCE\\_GROUP indicates a uniform instance group configuration. A value of INSTANCE\\_FLEET indicates an instance fleets configuration.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    log_encryption_kms_key_id: PropertyRef = PropertyRef(
        "LogEncryptionKmsKeyId",
        description="The KMS key used for encrypting log files.",
    )
    log_uri: PropertyRef = PropertyRef(
        "LogUri",
        description="The path to the Amazon S3 location where logs for this cluster are stored.",
    )
    master_public_dns_name: PropertyRef = PropertyRef(
        "MasterPublicDnsName",
        description="The DNS name of the master node. If the cluster is on a private subnet, this is the private DNS name. On a public subnet, this is the public DNS name.",
    )
    name: PropertyRef = PropertyRef(
        "Name", description="Name of this `AWSEMRCluster` node."
    )
    outpost_arn: PropertyRef = PropertyRef(
        "OutpostArn",
        description="The Amazon Resource Name (ARN) of the Outpost where the cluster is launched.",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region"
    )
    release_label: PropertyRef = PropertyRef(
        "ReleaseLabel",
        description="The Amazon EMR release label, which determines the version of open-source application packages installed on the cluster.",
    )
    repo_upgrade_on_boot: PropertyRef = PropertyRef(
        "RepoUpgradeOnBoot",
        description="Specifies the type of updates that are applied from the Amazon Linux AMI package repositories when an instance boots using the AMI.",
    )
    requested_ami_version: PropertyRef = PropertyRef(
        "RequestedAmiVersion", description="The AMI version requested for this cluster."
    )
    running_ami_version: PropertyRef = PropertyRef(
        "RunningAmiVersion", description="The AMI version running on this cluster."
    )
    scale_down_behavior: PropertyRef = PropertyRef(
        "ScaleDownBehavior",
        description="The way that individual Amazon EC2 instances terminate when an automatic scale-in activity occurs or an instance group is resized.",
    )
    security_configuration: PropertyRef = PropertyRef(
        "SecurityConfiguration",
        description="The name of the security configuration applied to the cluster.",
    )
    servicerole: PropertyRef = PropertyRef(
        "ServiceRole", description="Service Role of the EMR Cluster"
    )
    termination_protected: PropertyRef = PropertyRef(
        "TerminationProtected",
        description="Indicates whether Amazon EMR will lock the cluster to prevent the EC2 instances from being terminated by an API call or user intervention, or in the event of a cluster error.",
    )
    visible_to_all_users: PropertyRef = PropertyRef(
        "VisibleToAllUsers",
        description="Indicates whether the cluster is visible to IAM principals in the Amazon Web Services account associated with the cluster.",
    )


@dataclass(frozen=True)
class EMRClusterToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSEMRCluster)<-[:RESOURCE]-(:AWSAccount)
class EMRClusterToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEMRCluster`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EMRClusterToAWSAccountRelRelProperties = (
        EMRClusterToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class EMRClusterSchema(CartographyNodeSchema):
    "Represents an `AWSEMRCluster` node in the AWS graph."

    label: str = "AWSEMRCluster"
    # DEPRECATED: legacy EMRCluster node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["EMRCluster", "ComputeCluster"]
    )
    properties: EMRClusterNodeProperties = EMRClusterNodeProperties()
    sub_resource_relationship: EMRClusterToAWSAccountRel = EMRClusterToAWSAccountRel()
