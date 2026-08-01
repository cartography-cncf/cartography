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
from cartography.models.ontology.labels import COMPUTE_SERVICE


@dataclass(frozen=True)
class ModalAppNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Ephemeral apps (a bare `modal run`) have no name; only deployed apps do. The
    # description is then the sole human label, which is why the ontology mapping coalesces
    # the two.
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    # Raw APP_STATE_* value. Normalised into the ontology's canonical set separately.
    state: PropertyRef = PropertyRef("state", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    stopped_at: PropertyRef = PropertyRef("stopped_at")
    n_running_tasks: PropertyRef = PropertyRef("n_running_tasks")
    environment_name: PropertyRef = PropertyRef("environment_name", extra_index=True)


@dataclass(frozen=True)
class ModalAppToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalApp)
class ModalAppToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalAppToEnvironmentRelProperties = (
        ModalAppToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
# A Modal app is the deployment unit that owns functions, classes, sandboxes and tasks. It
# is the ComputeService of the Modal workload chain, so every child workload points at it
# with the canonical WORKLOAD_PARENT edge.
class ModalAppSchema(CartographyNodeSchema):
    label: str = "ModalApp"
    properties: ModalAppNodeProperties = ModalAppNodeProperties()
    sub_resource_relationship: ModalAppToEnvironmentRel = ModalAppToEnvironmentRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_SERVICE])
