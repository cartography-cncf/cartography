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
from cartography.models.ontology.labels import COMPUTE_INSTANCE


@dataclass(frozen=True)
class UnikraftInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uuid", description="Unikraft instance UUID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Instance name."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    state: PropertyRef = PropertyRef("state", description="Instance lifecycle state.")
    private_fqdn: PropertyRef = PropertyRef(
        "private_fqdn", description="Private FQDN of the instance."
    )
    image: PropertyRef = PropertyRef(
        "image", description="Image identifier used to boot this instance."
    )
    memory_mb: PropertyRef = PropertyRef(
        "memory_mb", description="Allocated memory in MB."
    )
    vcpus: PropertyRef = PropertyRef("vcpus", description="Allocated vCPUs.")
    args: PropertyRef = PropertyRef("args", description="Boot arguments.")
    restart_policy: PropertyRef = PropertyRef(
        "restart_policy", description="Restart policy."
    )
    start_count: PropertyRef = PropertyRef(
        "start_count", description="Number of times the instance was started."
    )
    restart_count: PropertyRef = PropertyRef(
        "restart_count", description="Number of times the instance was restarted."
    )
    started_at: PropertyRef = PropertyRef(
        "started_at", description="Last start timestamp."
    )
    stopped_at: PropertyRef = PropertyRef(
        "stopped_at", description="Last stop timestamp."
    )
    uptime_ms: PropertyRef = PropertyRef(
        "uptime_ms", description="Instance uptime in milliseconds."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags associated with the instance."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Operation status of the instance."
    )
    message: PropertyRef = PropertyRef(
        "message", description="Additional status information."
    )
    private_ip: PropertyRef = PropertyRef(
        "private_ip", description="Private IP address."
    )
    gateway: PropertyRef = PropertyRef("gateway", description="Network gateway.")
    nameserver: PropertyRef = PropertyRef(
        "nameserver", description="Network nameserver."
    )
    metro: PropertyRef = PropertyRef(
        "METRO",
        set_in_kwargs=True,
        description="Unikraft metro this instance runs in.",
    )
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID", set_in_kwargs=True, description="Unikraft account UUID."
    )


@dataclass(frozen=True)
class UnikraftInstanceToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnikraftAccount)-[:RESOURCE]->(:UnikraftInstance)
class UnikraftInstanceToAccountRel(CartographyRelSchema):
    """Connects `UnikraftAccount` to `UnikraftInstance` through `RESOURCE`."""

    target_node_label: str = "UnikraftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnikraftInstanceToAccountRelProperties = (
        UnikraftInstanceToAccountRelProperties()
    )


@dataclass(frozen=True)
class UnikraftInstanceSchema(CartographyNodeSchema):
    """Represents a Unikraft Cloud instance (microVM)."""

    label: str = "UnikraftInstance"
    properties: UnikraftInstanceNodeProperties = UnikraftInstanceNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_INSTANCE])
    sub_resource_relationship: UnikraftInstanceToAccountRel = (
        UnikraftInstanceToAccountRel()
    )
