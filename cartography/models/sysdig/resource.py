from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.sysdig.common import SysdigNodeToTenantRel


@dataclass(frozen=True)
class SysdigResourceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("type")
    cloud_provider: PropertyRef = PropertyRef("cloud_provider")
    cloud_account_id: PropertyRef = PropertyRef("cloud_account_id")
    cloud_region: PropertyRef = PropertyRef("cloud_region")
    cloud_resource_id: PropertyRef = PropertyRef("cloud_resource_id", extra_index=True)
    cloud_resource_arn: PropertyRef = PropertyRef(
        "cloud_resource_arn", extra_index=True
    )
    kubernetes_cluster: PropertyRef = PropertyRef("kubernetes_cluster")
    kubernetes_namespace: PropertyRef = PropertyRef("kubernetes_namespace")
    kubernetes_workload: PropertyRef = PropertyRef("kubernetes_workload")
    kubernetes_kind: PropertyRef = PropertyRef("kubernetes_kind")
    container_name: PropertyRef = PropertyRef("container_name")
    image_digest: PropertyRef = PropertyRef("image_digest", extra_index=True)
    image_uri: PropertyRef = PropertyRef("image_uri")


@dataclass(frozen=True)
class SysdigResourceSchema(CartographyNodeSchema):
    label: str = "SysdigResource"
    properties: SysdigResourceNodeProperties = SysdigResourceNodeProperties()
    sub_resource_relationship: CartographyRelSchema = SysdigNodeToTenantRel()
