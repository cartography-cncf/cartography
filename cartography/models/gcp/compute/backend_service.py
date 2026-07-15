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
class GCPBackendServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "partial_uri", description="Stable identifier for this resource."
    )
    partial_uri: PropertyRef = PropertyRef("partial_uri", description="Same as `id`.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The name of the backend service."
    )
    self_link: PropertyRef = PropertyRef(
        "self_link", description="Server-defined URL for the resource."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="The project ID that this backend service belongs to."
    )
    region: PropertyRef = PropertyRef(
        "region",
        description="The region of this backend service, or `null` for global backend services.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="An optional description of this backend service."
    )
    load_balancing_scheme: PropertyRef = PropertyRef(
        "load_balancing_scheme",
        description="The load balancing scheme (e.g., `EXTERNAL`, `EXTERNAL_MANAGED`, `INTERNAL`, `INTERNAL_MANAGED`).",
    )
    protocol: PropertyRef = PropertyRef(
        "protocol",
        description="The protocol this backend service uses (e.g., `HTTP`, `HTTPS`, `TCP`, `SSL`).",
    )
    port: PropertyRef = PropertyRef(
        "port", description="The port for the backend service."
    )
    port_name: PropertyRef = PropertyRef(
        "port_name", description="A named port on a backend instance group."
    )
    timeout_sec: PropertyRef = PropertyRef(
        "timeout_sec", description="Backend service timeout in seconds."
    )
    security_policy: PropertyRef = PropertyRef(
        "security_policy",
        description="The full URL of the Cloud Armor security policy attached to this backend service.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp", description="Creation timestamp of the resource."
    )


@dataclass(frozen=True)
class GCPBackendServiceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPBackendServiceToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPBackendServiceToProjectRelProperties = (
        GCPBackendServiceToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPBackendServiceToInstanceGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPBackendServiceToInstanceGroupRel(CartographyRelSchema):
    target_node_label: str = "GCPInstanceGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("backend_group_partial_uris", one_to_many=True),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO"
    properties: GCPBackendServiceToInstanceGroupRelProperties = (
        GCPBackendServiceToInstanceGroupRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudArmorPolicyToBackendServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPCloudArmorPolicyToBackendServiceRel(CartographyRelSchema):
    target_node_label: str = "GCPCloudArmorPolicy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("security_policy_partial_uri"),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PROTECTS"
    properties: GCPCloudArmorPolicyToBackendServiceRelProperties = (
        GCPCloudArmorPolicyToBackendServiceRelProperties()
    )


@dataclass(frozen=True)
class GCPBackendServiceSchema(CartographyNodeSchema):
    """A Google Cloud Backend Service resource."""

    label: str = "GCPBackendService"
    properties: GCPBackendServiceNodeProperties = GCPBackendServiceNodeProperties()
    sub_resource_relationship: GCPBackendServiceToProjectRel = (
        GCPBackendServiceToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPBackendServiceToInstanceGroupRel(),
            GCPCloudArmorPolicyToBackendServiceRel(),
        ],
    )
