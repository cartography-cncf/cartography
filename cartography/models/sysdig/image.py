from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.sysdig.common import SysdigNodeToTenantRel


@dataclass(frozen=True)
class SysdigImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    digest: PropertyRef = PropertyRef("digest", extra_index=True)
    uri: PropertyRef = PropertyRef("uri")
    architecture: PropertyRef = PropertyRef("architecture")
    os: PropertyRef = PropertyRef("os")


@dataclass(frozen=True)
class SysdigImageSchema(CartographyNodeSchema):
    label: str = "SysdigImage"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Image"])
    properties: SysdigImageNodeProperties = SysdigImageNodeProperties()
    sub_resource_relationship: CartographyRelSchema = SysdigNodeToTenantRel()
