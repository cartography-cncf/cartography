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
from cartography.models.ontology.labels import CONTAINER


@dataclass(frozen=True)
class ModalSandboxNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Sandbox ID, e.g. `sb-iSd0kw3efjqPw0yPVelPit`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Sandbox name, if one was given."
    )
    app_id: PropertyRef = PropertyRef("app_id", description="ID of the owning app.")
    exposed_internet: PropertyRef = PropertyRef(
        "exposed_internet",
        extra_index=True,
        description="`True` when the sandbox has at least one tunnel, meaning a forwarded port is reachable from the public internet.",
    )
    exposed_internet_type: PropertyRef = PropertyRef(
        "exposed_internet_type",
        extra_index=True,
        description="How it is exposed. Always `direct`. Whether a given tunnel terminates TLS is on `ModalSandboxTunnel.has_unencrypted_endpoint`.",
    )
    # Derived in transform: Modal's SandboxInfo has no state field, so it is inferred from
    # the task result status plus readiness. PENDING / RUNNING are synthetic; the rest are
    # raw GENERIC_STATUS_* values.
    state: PropertyRef = PropertyRef(
        "state",
        extra_index=True,
        description="`PENDING`, `RUNNING`, or a raw `GENERIC_STATUS_*` value.",
    )
    # "v1" or "v2", derived from the id shape since Modal reports no version field. The two
    # generations are returned by different RPCs and support different operations, so which one
    # a sandbox is matters operationally.
    sandbox_version: PropertyRef = PropertyRef(
        "sandbox_version",
        extra_index=True,
        description="`v1` or `v2`, derived from the id shape. The two are listed by different API calls and support different operations.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the sandbox was created."
    )
    ready_at: PropertyRef = PropertyRef(
        "ready_at",
        description="When the sandbox became ready. Null while still starting.",
    )
    image_id: PropertyRef = PropertyRef(
        "image_id", extra_index=True, description="ID of the image it runs."
    )
    # Unlike functions, sandboxes DO expose their resource allocation.
    memory_mb: PropertyRef = PropertyRef(
        "memory_mb", description="Requested memory in MB."
    )
    memory_mb_max: PropertyRef = PropertyRef(
        "memory_mb_max", description="Memory limit in MB, if set."
    )
    milli_cpu: PropertyRef = PropertyRef(
        "milli_cpu", description="Requested CPU in millicores."
    )
    milli_cpu_max: PropertyRef = PropertyRef(
        "milli_cpu_max", description="CPU limit in millicores, if set."
    )
    gpu_type: PropertyRef = PropertyRef(
        "gpu_type",
        extra_index=True,
        description="Raw `GPU_TYPE_*` value, null for a CPU-only sandbox.",
    )
    ephemeral_disk_mb: PropertyRef = PropertyRef(
        "ephemeral_disk_mb", description="Ephemeral disk in MB, if set."
    )
    regions: PropertyRef = PropertyRef(
        "regions", description="Regions the sandbox may run in."
    )
    # Set only when the sandbox pins exactly one region, so it can join the ontology's
    # scalar region field. Left null for a multi-region sandbox.
    region: PropertyRef = PropertyRef(
        "region",
        extra_index=True,
        description="Set only when exactly one region is pinned, so it can join the ontology's scalar region. Null for a multi-region sandbox.",
    )
    # A long timeout on a sandbox with an open tunnel is the sharpest exposure signal here.
    timeout_secs: PropertyRef = PropertyRef(
        "timeout_secs", description="Hard lifetime in seconds."
    )
    idle_timeout_secs: PropertyRef = PropertyRef(
        "idle_timeout_secs", description="Idle timeout in seconds, if set."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Sandbox tags, flattened to `key=value` strings."
    )
    environment_name: PropertyRef = PropertyRef(
        "environment_name",
        extra_index=True,
        description="Name of the owning environment.",
    )


@dataclass(frozen=True)
class ModalSandboxToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalSandbox)
class ModalSandboxToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalSandboxToEnvironmentRelProperties = (
        ModalSandboxToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class ModalSandboxToAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalSandbox)-[:WORKLOAD_PARENT]->(:ModalApp)
# WORKLOAD_PARENT is required here: ONTOLOGY_REL_CONSTRAINTS pins Container -> ComputeService
# to this label.
class ModalSandboxToAppRel(CartographyRelSchema):
    target_node_label: str = "ModalApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("app_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: ModalSandboxToAppRelProperties = ModalSandboxToAppRelProperties()


@dataclass(frozen=True)
class ModalSandboxToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalSandbox)-[:HAS_IMAGE]->(:ModalImage)
# Best-effort: only resolves when the sandbox runs a *named* image, since anonymous build
# images are not enumerable. Unconstrained by the ontology because ModalImage deliberately
# carries no :Image label.
class ModalSandboxToImageRel(CartographyRelSchema):
    target_node_label: str = "ModalImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("image_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: ModalSandboxToImageRelProperties = ModalSandboxToImageRelProperties()


@dataclass(frozen=True)
# A Modal sandbox is an ad-hoc container, typically used to run untrusted or agent-generated
# code. Only live sandboxes are ingested: finished ones are ephemeral by nature and would
# otherwise accumulate in the graph forever.
class ModalSandboxSchema(CartographyNodeSchema):
    """Represents a running Modal sandbox: an ad-hoc container, commonly used to run untrusted or agent-generated code. Only **live** sandboxes are ingested; finished ones are ephemeral and would otherwise accumulate forever. Unlike functions, sandboxes **do** expose their resource allocation, regions and tunnels. Modal reports no state field, so `state` is derived from the task result plus readiness: `PENDING` and `RUNNING` are synthetic values, the rest are raw `GENERIC_STATUS_*` values. Modal has two sandbox generations and **the ordinary listing returns only v1**: its docs state that \"V2 sandboxes created with this method are not currently returned by `client.sandboxes.list()`\". Cartography therefore also calls the v2 listing, which is per app rather than per environment, so both generations appear. Modal reports no version field either, so `sandbox_version` is derived from the shape of the id. v2 is still opt-in at the time of writing, so most workspaces have none. A long `timeout_secs` combined with an exposed tunnel is the sharpest exposure signal on this node. its forwarded ports. `HAS_IMAGE` only resolves when the sandbox runs a *named* image, since anonymous build images are not enumerable."""

    label: str = "ModalSandbox"
    properties: ModalSandboxNodeProperties = ModalSandboxNodeProperties()
    sub_resource_relationship: ModalSandboxToEnvironmentRel = (
        ModalSandboxToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ModalSandboxToAppRel(), ModalSandboxToImageRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CONTAINER])
