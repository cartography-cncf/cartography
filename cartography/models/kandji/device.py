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
class KandjiDeviceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Kandji device ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    device_id: PropertyRef = PropertyRef(
        "device_id",
        description="Kandji device ID.",
    )
    device_name: PropertyRef = PropertyRef(
        "device_name",
        extra_index=True,
        description="Friendly device name.",
    )
    last_check_in: PropertyRef = PropertyRef(
        "last_check_in",
        description="Timestamp of the device's last Kandji check-in.",
    )
    model: PropertyRef = PropertyRef("model", description="Device model.")
    os_version: PropertyRef = PropertyRef(
        "os_version",
        description="Operating system version.",
    )
    platform: PropertyRef = PropertyRef(
        "platform",
        description="Device platform.",
    )
    serial_number: PropertyRef = PropertyRef(
        "serial_number",
        extra_index=True,
        description="Device serial number.",
    )


@dataclass(frozen=True)
class KandjiTenantToKandjiDeviceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KandjiDevice)<-[:RESOURCE]-(:KandjiTenant)
class KandjiTenantToKandjiDeviceRel(CartographyRelSchema):
    """The tenant contains the enrolled device."""

    target_node_label: str = "KandjiTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KandjiTenantToKandjiDeviceRelProperties = (
        KandjiTenantToKandjiDeviceRelProperties()
    )


@dataclass(frozen=True)
# (:KandjiDevice)-[:ENROLLED_TO]->(:KandjiTenant) - Backwards compatibility
class KandjiDeviceToTenantDeprecatedRel(CartographyRelSchema):
    """Deprecated compatibility edge linking a device to its tenant."""

    target_node_label: str = "KandjiTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENROLLED_TO"
    properties: KandjiTenantToKandjiDeviceRelProperties = (
        KandjiTenantToKandjiDeviceRelProperties()
    )


@dataclass(frozen=True)
class KandjiDeviceSchema(CartographyNodeSchema):
    """A device managed by Kandji."""

    label: str = "KandjiDevice"  # The label of the node
    properties: KandjiDeviceNodeProperties = (
        KandjiDeviceNodeProperties()
    )  # An object representing all properties
    sub_resource_relationship: KandjiTenantToKandjiDeviceRel = (
        KandjiTenantToKandjiDeviceRel()
    )
    # DEPRECATED: for backward compatibility, will be removed in v1.0.0
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[KandjiDeviceToTenantDeprecatedRel()],
    )
