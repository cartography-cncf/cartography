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
    id: PropertyRef = PropertyRef("partial_uri")
    partial_uri: PropertyRef = PropertyRef("partial_uri")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    self_link: PropertyRef = PropertyRef("self_link")
    project_id: PropertyRef = PropertyRef("project_id")
    region: PropertyRef = PropertyRef("region")
    description: PropertyRef = PropertyRef("description")
    load_balancing_scheme: PropertyRef = PropertyRef("load_balancing_scheme")
    protocol: PropertyRef = PropertyRef("protocol")
    port: PropertyRef = PropertyRef("port")
    port_name: PropertyRef = PropertyRef("port_name")
    timeout_sec: PropertyRef = PropertyRef("timeout_sec")
    security_policy: PropertyRef = PropertyRef("security_policy")
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")


@dataclass(frozen=True)
class GCPBackendServiceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
