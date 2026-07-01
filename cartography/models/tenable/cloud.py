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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    ec2_instance_ami_id: PropertyRef = PropertyRef("ec2_instance_ami_id")
    owner_id: PropertyRef = PropertyRef("owner_id")
    availability_zone: PropertyRef = PropertyRef("availability_zone")
    region: PropertyRef = PropertyRef("region")
    vpc_id: PropertyRef = PropertyRef("vpc_id")
    subnet_id: PropertyRef = PropertyRef("subnet_id")
    ec2_instance_type: PropertyRef = PropertyRef("ec2_instance_type")
    ec2_instance_state_name: PropertyRef = PropertyRef("ec2_instance_state_name")
    ec2_instance_group_name: PropertyRef = PropertyRef("ec2_instance_group_name")
    ec2_name: PropertyRef = PropertyRef("ec2_name")


@dataclass(frozen=True)
class TenableAssetAWSToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableAssetAWS)
@dataclass(frozen=True)
class TenableAssetAWSToTenantRel(CartographyRelSchema):
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
    label: str = "TenableAssetAWS"
    properties: TenableAssetAWSNodeProperties = TenableAssetAWSNodeProperties()
    sub_resource_relationship: TenableAssetAWSToTenantRel = TenableAssetAWSToTenantRel()


# ---------------------------------------------------------------------------
# TenableAssetAzure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TenableAssetAzureNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    resource_id: PropertyRef = PropertyRef("resource_id", extra_index=True)


@dataclass(frozen=True)
class TenableAssetAzureToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableAssetAzure)
@dataclass(frozen=True)
class TenableAssetAzureToTenantRel(CartographyRelSchema):
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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    project_id: PropertyRef = PropertyRef("project_id")
    zone: PropertyRef = PropertyRef("zone")


@dataclass(frozen=True)
class TenableAssetGCPToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableAssetGCP)
@dataclass(frozen=True)
class TenableAssetGCPToTenantRel(CartographyRelSchema):
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
    label: str = "TenableAssetGCP"
    properties: TenableAssetGCPNodeProperties = TenableAssetGCPNodeProperties()
    sub_resource_relationship: TenableAssetGCPToTenantRel = TenableAssetGCPToTenantRel()
