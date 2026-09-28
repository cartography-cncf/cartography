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
class MiradoreConfigProfileDeploymentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Tenant-scoped identifier for the configuration profile deployment, as `<site name>/<Miradore ID>`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    miradore_id: PropertyRef = PropertyRef(
        "miradore_id",
        extra_index=True,
        description="Raw Miradore ID of the configuration profile deployment, which is only unique within the tenant.",
    )
    deployment_time: PropertyRef = PropertyRef(
        "deployment_time",
        description="Timestamp when the profile was deployed to the device.",
    )
    deployment_trigger: PropertyRef = PropertyRef(
        "deployment_trigger",
        description="What triggered the deployment: Administrator or BusinessEnforcement.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Deployment status: Unknown, Installed or Removed.",
    )


@dataclass(frozen=True)
class MiradoreConfigProfileDeploymentToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:MiradoreTenant)-[:RESOURCE]->(:MiradoreConfigProfileDeployment)
@dataclass(frozen=True)
class MiradoreConfigProfileDeploymentToTenantRel(CartographyRelSchema):
    """Links a Miradore tenant to one of its configuration profile deployments."""

    target_node_label: str = "MiradoreTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: MiradoreConfigProfileDeploymentToTenantRelProperties = (
        MiradoreConfigProfileDeploymentToTenantRelProperties()
    )


@dataclass(frozen=True)
class MiradoreConfigProfileDeploymentToDeviceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:MiradoreDevice)-[:HAS_DEPLOYMENT]->(:MiradoreConfigProfileDeployment)
@dataclass(frozen=True)
class MiradoreConfigProfileDeploymentToDeviceRel(CartographyRelSchema):
    """Links a Miradore device to a configuration profile deployment targeting it."""

    target_node_label: str = "MiradoreDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("device_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DEPLOYMENT"
    properties: MiradoreConfigProfileDeploymentToDeviceRelProperties = (
        MiradoreConfigProfileDeploymentToDeviceRelProperties()
    )


@dataclass(frozen=True)
class MiradoreConfigProfileDeploymentToConfigProfileRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:MiradoreConfigProfileDeployment)-[:DEPLOYS]->(:MiradoreConfigProfile)
@dataclass(frozen=True)
class MiradoreConfigProfileDeploymentToConfigProfileRel(CartographyRelSchema):
    """Links a deployment to the configuration profile it installs."""

    target_node_label: str = "MiradoreConfigProfile"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("config_profile_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYS"
    properties: MiradoreConfigProfileDeploymentToConfigProfileRelProperties = (
        MiradoreConfigProfileDeploymentToConfigProfileRelProperties()
    )


@dataclass(frozen=True)
class MiradoreConfigProfileDeploymentSchema(CartographyNodeSchema):
    """The deployment of a Miradore configuration profile onto a single device."""

    label: str = "MiradoreConfigProfileDeployment"
    properties: MiradoreConfigProfileDeploymentNodeProperties = (
        MiradoreConfigProfileDeploymentNodeProperties()
    )
    sub_resource_relationship: MiradoreConfigProfileDeploymentToTenantRel = (
        MiradoreConfigProfileDeploymentToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            MiradoreConfigProfileDeploymentToDeviceRel(),
            MiradoreConfigProfileDeploymentToConfigProfileRel(),
        ],
    )
