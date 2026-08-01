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
class WizResourceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    external_id: PropertyRef = PropertyRef("external_id", extra_index=True)
    resource_type: PropertyRef = PropertyRef("resource_type", extra_index=True)
    cloud_platform: PropertyRef = PropertyRef("cloud_platform", extra_index=True)
    cloud_provider_url: PropertyRef = PropertyRef("cloud_provider_url")
    status: PropertyRef = PropertyRef("status")
    region: PropertyRef = PropertyRef("region", extra_index=True)
    cloud_account_id: PropertyRef = PropertyRef("cloud_account_id", extra_index=True)
    cloud_account_name: PropertyRef = PropertyRef("cloud_account_name")
    cloud_account_provider: PropertyRef = PropertyRef("cloud_account_provider")
    cloud_account_external_id: PropertyRef = PropertyRef(
        "cloud_account_external_id",
        extra_index=True,
    )
    project_ids: PropertyRef = PropertyRef("project_ids", extra_index=True)
    project_names: PropertyRef = PropertyRef("project_names", extra_index=True)
    tags: PropertyRef = PropertyRef("tags")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    is_open_to_all_internet: PropertyRef = PropertyRef("is_open_to_all_internet")
    is_accessible_from_internet: PropertyRef = PropertyRef(
        "is_accessible_from_internet",
    )
    has_access_to_sensitive_data: PropertyRef = PropertyRef(
        "has_access_to_sensitive_data",
    )
    has_admin_privileges: PropertyRef = PropertyRef("has_admin_privileges")
    has_high_privileges: PropertyRef = PropertyRef("has_high_privileges")
    has_sensitive_data: PropertyRef = PropertyRef("has_sensitive_data")


@dataclass(frozen=True)
class WizResourceToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:WizTenant)-[:RESOURCE]->(:WizResource)
@dataclass(frozen=True)
class WizResourceToTenantRel(CartographyRelSchema):
    target_node_label: str = "WizTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WIZ_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WizResourceToTenantRelProperties = WizResourceToTenantRelProperties()


@dataclass(frozen=True)
class WizResourceSchema(CartographyNodeSchema):
    label: str = "WizResource"
    properties: WizResourceNodeProperties = WizResourceNodeProperties()
    sub_resource_relationship: WizResourceToTenantRel = WizResourceToTenantRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Asset"])
