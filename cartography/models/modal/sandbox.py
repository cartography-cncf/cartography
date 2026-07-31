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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    app_id: PropertyRef = PropertyRef("app_id")
    # Derived in transform: Modal's SandboxInfo has no state field, so it is inferred from
    # the task result status plus readiness. PENDING / RUNNING are synthetic; the rest are
    # raw GENERIC_STATUS_* values.
    state: PropertyRef = PropertyRef("state", extra_index=True)
    # "v1" or "v2", derived from the id shape since Modal reports no version field. The two
    # generations are returned by different RPCs and support different operations, so which one
    # a sandbox is matters operationally.
    sandbox_version: PropertyRef = PropertyRef("sandbox_version", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    ready_at: PropertyRef = PropertyRef("ready_at")
    image_id: PropertyRef = PropertyRef("image_id", extra_index=True)
    # Unlike functions, sandboxes DO expose their resource allocation.
    memory_mb: PropertyRef = PropertyRef("memory_mb")
    memory_mb_max: PropertyRef = PropertyRef("memory_mb_max")
    milli_cpu: PropertyRef = PropertyRef("milli_cpu")
    milli_cpu_max: PropertyRef = PropertyRef("milli_cpu_max")
    gpu_type: PropertyRef = PropertyRef("gpu_type", extra_index=True)
    ephemeral_disk_mb: PropertyRef = PropertyRef("ephemeral_disk_mb")
    regions: PropertyRef = PropertyRef("regions")
    # Set only when the sandbox pins exactly one region, so it can join the ontology's
    # scalar region field. Left null for a multi-region sandbox.
    region: PropertyRef = PropertyRef("region", extra_index=True)
    # A long timeout on a sandbox with an open tunnel is the sharpest exposure signal here.
    timeout_secs: PropertyRef = PropertyRef("timeout_secs")
    idle_timeout_secs: PropertyRef = PropertyRef("idle_timeout_secs")
    tags: PropertyRef = PropertyRef("tags")
    environment_name: PropertyRef = PropertyRef("environment_name", extra_index=True)


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
    label: str = "ModalSandbox"
    properties: ModalSandboxNodeProperties = ModalSandboxNodeProperties()
    sub_resource_relationship: ModalSandboxToEnvironmentRel = (
        ModalSandboxToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ModalSandboxToAppRel(), ModalSandboxToImageRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CONTAINER])
