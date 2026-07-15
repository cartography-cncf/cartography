from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher

# ---------------------------------------------------------------------------
# TenableAssetAWS
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TenableAssetAWSNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="AWS EC2 instance ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    ec2_instance_ami_id: PropertyRef = PropertyRef(
        "ec2_instance_ami_id", description="AMI ID used to launch the instance."
    )
    owner_id: PropertyRef = PropertyRef("owner_id", description="AWS account ID.")
    availability_zone: PropertyRef = PropertyRef(
        "availability_zone", description="AWS availability zone."
    )
    region: PropertyRef = PropertyRef("region", description="AWS region.")
    vpc_id: PropertyRef = PropertyRef("vpc_id", description="AWS VPC ID.")
    subnet_id: PropertyRef = PropertyRef("subnet_id", description="AWS subnet ID.")
    ec2_instance_type: PropertyRef = PropertyRef(
        "ec2_instance_type", description="EC2 instance type."
    )
    ec2_instance_state_name: PropertyRef = PropertyRef(
        "ec2_instance_state_name", description="EC2 instance state."
    )
    ec2_instance_group_name: PropertyRef = PropertyRef(
        "ec2_instance_group_name", description="EC2 security group name."
    )
    ec2_name: PropertyRef = PropertyRef(
        "ec2_name", description="Value of the EC2 Name tag."
    )


@dataclass(frozen=True)
class TenableAssetAWSToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableAssetAWS)
@dataclass(frozen=True)
class TenableAssetAWSToTenantRel(CartographyRelSchema):
    """Links a Tenable tenant to AWS details for an asset."""

    target_node_label: str = "TenableTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENABLE_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TenableAssetAWSToTenantRelProperties = (
        TenableAssetAWSToTenantRelProperties()
    )


@dataclass(frozen=True)
class TenableAssetAWSSchema(CartographyNodeSchema):
    """AWS cloud details associated with a Tenable asset."""

    label: str = "TenableAssetAWS"
    properties: TenableAssetAWSNodeProperties = TenableAssetAWSNodeProperties()
    sub_resource_relationship: TenableAssetAWSToTenantRel = TenableAssetAWSToTenantRel()


# ---------------------------------------------------------------------------
# TenableAssetAzure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TenableAssetAzureNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Azure virtual machine ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    resource_id: PropertyRef = PropertyRef(
        "resource_id",
        extra_index=True,
        description="Azure Resource Manager resource ID.",
    )


@dataclass(frozen=True)
class TenableAssetAzureToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableAssetAzure)
@dataclass(frozen=True)
class TenableAssetAzureToTenantRel(CartographyRelSchema):
    """Links a Tenable tenant to Azure details for an asset."""

    target_node_label: str = "TenableTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENABLE_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TenableAssetAzureToTenantRelProperties = (
        TenableAssetAzureToTenantRelProperties()
    )


@dataclass(frozen=True)
class TenableAssetAzureSchema(CartographyNodeSchema):
    """Azure cloud details associated with a Tenable asset."""

    label: str = "TenableAssetAzure"
    properties: TenableAssetAzureNodeProperties = TenableAssetAzureNodeProperties()
    sub_resource_relationship: TenableAssetAzureToTenantRel = (
        TenableAssetAzureToTenantRel()
    )


# ---------------------------------------------------------------------------
# TenableAssetGCP
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TenableAssetGCPNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="GCP instance ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    project_id: PropertyRef = PropertyRef("project_id", description="GCP project ID.")
    zone: PropertyRef = PropertyRef("zone", description="GCP zone.")


@dataclass(frozen=True)
class TenableAssetGCPToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableAssetGCP)
@dataclass(frozen=True)
class TenableAssetGCPToTenantRel(CartographyRelSchema):
    """Links a Tenable tenant to GCP details for an asset."""

    target_node_label: str = "TenableTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENABLE_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TenableAssetGCPToTenantRelProperties = (
        TenableAssetGCPToTenantRelProperties()
    )


@dataclass(frozen=True)
class TenableAssetGCPSchema(CartographyNodeSchema):
    """GCP cloud details associated with a Tenable asset."""

    label: str = "TenableAssetGCP"
    properties: TenableAssetGCPNodeProperties = TenableAssetGCPNodeProperties()
    sub_resource_relationship: TenableAssetGCPToTenantRel = TenableAssetGCPToTenantRel()
