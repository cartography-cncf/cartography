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
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class ModalEnvironmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Environment ID, e.g. `en-C3umado26sLFrhYfZjoWjL`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Environment name."
    )
    # Suffix appended to the generated URL of every web endpoint in this environment.
    webhook_suffix: PropertyRef = PropertyRef(
        "webhook_suffix",
        extra_index=True,
        description="Suffix appended to generated web endpoint URLs in this environment.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the environment was created."
    )
    is_default: PropertyRef = PropertyRef(
        "is_default", description="Whether this is the workspace's default environment."
    )
    is_managed: PropertyRef = PropertyRef(
        "is_managed", description="Whether the environment is managed by Modal."
    )
    environment_type: PropertyRef = PropertyRef(
        "environment_type", description="Raw `ENVIRONMENT_TYPE_*` value."
    )
    max_concurrent_tasks: PropertyRef = PropertyRef(
        "max_concurrent_tasks", description="Concurrency limit on tasks."
    )
    max_concurrent_gpus: PropertyRef = PropertyRef(
        "max_concurrent_gpus", description="Concurrency limit on GPUs."
    )
    current_concurrent_tasks: PropertyRef = PropertyRef(
        "current_concurrent_tasks", description="Tasks currently running."
    )
    current_concurrent_gpus: PropertyRef = PropertyRef(
        "current_concurrent_gpus", description="GPUs currently in use."
    )
    # Availability signal: workloads in this environment are refused once the spend
    # limit is hit. The cost figures themselves are out of scope for this module.
    spend_limit_reached: PropertyRef = PropertyRef(
        "spend_limit_reached",
        description="Whether the spend limit has been hit. Workloads are refused when true. Cost figures themselves are out of scope.",
    )


@dataclass(frozen=True)
class ModalEnvironmentToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalWorkspace)-[:RESOURCE]->(:ModalEnvironment)
class ModalEnvironmentToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "ModalWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalEnvironmentToWorkspaceRelProperties = (
        ModalEnvironmentToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
# A Modal environment is a namespace within a workspace: every named object (secret,
# volume, app, ...) is scoped to exactly one environment, and every Modal listing RPC
# is keyed by environment name. It is therefore the sub-resource (cleanup) scope for
# all environment-scoped Modal nodes.
#
# It carries Tenant rather than ComputeNamespace on purpose. ComputeNamespace would be
# the closer semantic fit, but ONTOLOGY_REL_CONSTRAINTS constrains
# ComputeService/ComputePod -> ComputeNamespace to WORKLOAD_PARENT in both directions,
# and the (:ModalEnvironment)-[:RESOURCE]->(:ModalApp) sub-resource edge would violate
# it and require a LEGACY_REL_WHITELIST entry. The environment name is still exposed to
# the ontology as _ont_namespace on ModalTask and ModalSandbox, so no signal is lost.
class ModalEnvironmentSchema(CartographyNodeSchema):
    """Represents a Modal environment: a namespace within a workspace. Every named object (app, secret, volume, ...) belongs to exactly one environment, and every Modal listing call is keyed by environment, which makes the environment the cleanup scope for all environment-scoped Modal nodes. `ComputeNamespace` would be the closer semantic fit, but the ontology constrains `ComputeService`/`ComputePod` to `ComputeNamespace` edges to `WORKLOAD_PARENT` in both directions, which the `RESOURCE` sub-resource edge would violate. The environment name is instead exposed to the ontology as `_ont_namespace` on the workload nodes."""

    label: str = "ModalEnvironment"
    properties: ModalEnvironmentNodeProperties = ModalEnvironmentNodeProperties()
    sub_resource_relationship: ModalEnvironmentToWorkspaceRel = (
        ModalEnvironmentToWorkspaceRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
