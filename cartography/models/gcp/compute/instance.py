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
class GCPInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("partial_uri")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    self_link: PropertyRef = PropertyRef("selfLink")
    instancename: PropertyRef = PropertyRef("name", extra_index=True)
    hostname: PropertyRef = PropertyRef("hostname")
    zone_name: PropertyRef = PropertyRef("zone_name")
    project_id: PropertyRef = PropertyRef("project_id")
    status: PropertyRef = PropertyRef("status")
    machine_type: PropertyRef = PropertyRef("machine_type")
    service_account_email: PropertyRef = PropertyRef("service_account_email")
    service_account_scopes: PropertyRef = PropertyRef("service_account_scopes")
    can_ip_forward: PropertyRef = PropertyRef("can_ip_forward")
    enable_vtpm: PropertyRef = PropertyRef("enable_vtpm")
    enable_integrity_monitoring: PropertyRef = PropertyRef(
        "enable_integrity_monitoring"
    )
    enable_confidential_compute: PropertyRef = PropertyRef(
        "enable_confidential_compute"
    )
    enable_oslogin_metadata: PropertyRef = PropertyRef("enable_oslogin_metadata")
    block_project_ssh_keys: PropertyRef = PropertyRef("block_project_ssh_keys")
    serial_port_enable: PropertyRef = PropertyRef("serial_port_enable")


@dataclass(frozen=True)
class GCPInstanceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPInstanceToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPInstanceToProjectRelProperties = GCPInstanceToProjectRelProperties()


@dataclass(frozen=True)
class GCPInstanceSchema(CartographyNodeSchema):
    label: str = "GCPInstance"
    properties: GCPInstanceNodeProperties = GCPInstanceNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["Instance", "ComputeInstance"]
    )
    sub_resource_relationship: GCPInstanceToProjectRel = GCPInstanceToProjectRel()
