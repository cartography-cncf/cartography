from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class TencentCloudAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="UIN of the Tencent Cloud root account (the `OwnerUin`).",
    )
    app_id: PropertyRef = PropertyRef(
        "app_id",
        extra_index=True,
        description="APPID of the account. COS bucket names end with this value.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TencentCloudAccountSchema(CartographyNodeSchema):
    """A Tencent Cloud root account. Every other Tencent Cloud node belongs to one."""

    label: str = "TencentCloudAccount"
    properties: TencentCloudAccountNodeProperties = TencentCloudAccountNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
