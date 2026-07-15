from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "partial_uri",
        description="The partial resource URI representing this instance. Has the form `projects/{project_name}/zones/{zone_name}/instances/{instance_name}`.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    self_link: PropertyRef = PropertyRef(
        "selfLink",
        description="The full resource URI representing this instance. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}`.",
    )
    instancename: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description='The name of the instance, e.g. "my-instance".',
    )
    hostname: PropertyRef = PropertyRef(
        "hostname", description="If present, the hostname of the instance."
    )
    zone_name: PropertyRef = PropertyRef(
        "zone_name", description="The zone that the instance is installed on."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="Google Cloud project that owns this resource."
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="The [GCP Instance Lifecycle](https://cloud.google.com/compute/docs/instances/instance-life-cycle) state of the instance.",
    )
    machine_type: PropertyRef = PropertyRef(
        "machine_type",
        description="The instance machine type short name, e.g. `n2d-standard-4`.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="RFC 3339 timestamp of when the instance was created.",
    )
    private_ip: PropertyRef = PropertyRef(
        "private_ip",
        description="Primary internal IP address (first NIC's `networkIP`).",
    )
    public_ip: PropertyRef = PropertyRef(
        "public_ip",
        description="Primary external IP address (first access config's `natIP`), if any.",
    )
    service_account_email: PropertyRef = PropertyRef(
        "service_account_email",
        description="Primary attached service account email when the instance has one.",
    )
    service_account_scopes: PropertyRef = PropertyRef(
        "service_account_scopes",
        description="OAuth scopes configured on the primary attached service account.",
    )
    can_ip_forward: PropertyRef = PropertyRef(
        "can_ip_forward",
        description="Whether the instance is configured with IP forwarding enabled.",
    )
    enable_vtpm: PropertyRef = PropertyRef(
        "enable_vtpm",
        description="Shielded VM vTPM state from `shieldedInstanceConfig.enableVtpm`.",
    )
    enable_integrity_monitoring: PropertyRef = PropertyRef(
        "enable_integrity_monitoring",
        description="Shielded VM Integrity Monitoring state from `shieldedInstanceConfig.enableIntegrityMonitoring`.",
    )
    enable_confidential_compute: PropertyRef = PropertyRef(
        "enable_confidential_compute",
        description="Confidential Computing state from `confidentialInstanceConfig.enableConfidentialCompute`.",
    )
    enable_oslogin_metadata: PropertyRef = PropertyRef(
        "enable_oslogin_metadata",
        description="Instance metadata value for `enable-oslogin` when explicitly set.",
    )
    block_project_ssh_keys: PropertyRef = PropertyRef(
        "block_project_ssh_keys",
        description="Instance metadata value for `block-project-ssh-keys` when explicitly set.",
    )
    serial_port_enable: PropertyRef = PropertyRef(
        "serial_port_enable",
        description="Instance metadata value for `serial-port-enable` when explicitly set.",
    )


@dataclass(frozen=True)
class GCPInstanceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
class GCPInstanceToServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPInstance)-[:RUNS_AS]->(:GCPServiceAccount)
class GCPInstanceToServiceAccountRel(CartographyRelSchema):
    target_node_label: str = "GCPServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("service_account_email")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_AS"
    properties: GCPInstanceToServiceAccountRelProperties = (
        GCPInstanceToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class GCPInstanceSchema(CartographyNodeSchema):
    """Representation of a GCP [Instance](https://cloud.google.com/compute/docs/reference/rest/v1/instances).  Additional references can be found in the [official documentation]( https://cloud.google.com/compute/docs/concepts)."""

    label: str = "GCPInstance"
    properties: GCPInstanceNodeProperties = GCPInstanceNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["Instance", "ComputeInstance"]
    )
    sub_resource_relationship: GCPInstanceToProjectRel = GCPInstanceToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPInstanceToServiceAccountRel(),
        ],
    )
