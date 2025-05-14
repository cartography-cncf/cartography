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
class EMRClusterNodeProperties(CartographyNodeProperties):
    arn: PropertyRef = PropertyRef("ClusterArn", extra_index=True)
    auto_terminate: PropertyRef = PropertyRef("AutoTerminate")
    autoscaling_role: PropertyRef = PropertyRef("AutoScalingRole")
    custom_ami_id: PropertyRef = PropertyRef("CustomAmiId")
    id: PropertyRef = PropertyRef("Id")
    instance_collection_type: PropertyRef = PropertyRef("InstanceCollectionType")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    log_encryption_kms_key_id: PropertyRef = PropertyRef("LogEncryptionKmsKeyId")
    log_uri: PropertyRef = PropertyRef("LogUri")
    master_public_dns_name: PropertyRef = PropertyRef("MasterPublicDnsName")
    name: PropertyRef = PropertyRef("Name")
    outpost_arn: PropertyRef = PropertyRef("OutpostArn")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    release_label: PropertyRef = PropertyRef("ReleaseLabel")
    repo_upgrade_on_boot: PropertyRef = PropertyRef("RepoUpgradeOnBoot")
    requested_ami_version: PropertyRef = PropertyRef("RequestedAmiVersion")
    running_ami_version: PropertyRef = PropertyRef("RunningAmiVersion")
    scale_down_behavior: PropertyRef = PropertyRef("ScaleDownBehavior")
    security_configuration: PropertyRef = PropertyRef("SecurityConfiguration")
    servicerole: PropertyRef = PropertyRef("ServiceRole")
    termination_protected: PropertyRef = PropertyRef("TerminationProtected")
    visible_to_all_users: PropertyRef = PropertyRef("VisibleToAllUsers")


@dataclass(frozen=True)
class EMRClusterToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EMRCluster)<-[:RESOURCE]-(:AWSAccount)
class EMRClusterToAWSAccountRel(CartographyRelSchema):
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
    label: str = "EMRCluster"
    properties: EMRClusterNodeProperties = EMRClusterNodeProperties()
    sub_resource_relationship: EMRClusterToAWSAccountRel = EMRClusterToAWSAccountRel()
