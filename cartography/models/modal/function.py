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
from cartography.models.ontology.labels import FUNCTION


@dataclass(frozen=True)
class ModalFunctionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    app_id: PropertyRef = PropertyRef("app_id")
    # Public URL of a web endpoint, null for a plain function. Every non-null value is
    # internet-reachable.
    #
    # IMPORTANT: this says nothing about whether the endpoint is protected. Modal's
    # `requires_proxy_auth` is write-only and cannot be read back, so protection status is
    # unknowable from the API. Treat any non-null web_url as potentially unauthenticated.
    web_url: PropertyRef = PropertyRef("web_url", extra_index=True)
    is_web_endpoint: PropertyRef = PropertyRef("is_web_endpoint", extra_index=True)
    # Raw FUNCTION_TYPE_* value.
    function_type: PropertyRef = PropertyRef("function_type")
    is_method: PropertyRef = PropertyRef("is_method")
    definition_id: PropertyRef = PropertyRef("definition_id")
    input_plane_url: PropertyRef = PropertyRef("input_plane_url")
    input_plane_region: PropertyRef = PropertyRef("input_plane_region")
    environment_name: PropertyRef = PropertyRef("environment_name", extra_index=True)
    # NOTE: GPU, CPU, memory, timeout, region, cloud, mounted secrets and volumes,
    # block_network, untrusted, proxy and schedule are deliberately absent. Modal only ever
    # *accepts* them at deploy time (FunctionCreate); no read RPC returns them for a
    # deployed function, so there is nothing to ingest.


@dataclass(frozen=True)
class ModalFunctionToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalFunction)
class ModalFunctionToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalFunctionToEnvironmentRelProperties = (
        ModalFunctionToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class ModalFunctionToAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalFunction)-[:WORKLOAD_PARENT]->(:ModalApp)
class ModalFunctionToAppRel(CartographyRelSchema):
    target_node_label: str = "ModalApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("app_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: ModalFunctionToAppRelProperties = ModalFunctionToAppRelProperties()


@dataclass(frozen=True)
class ModalClassToFunctionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalClass)-[:HAS_METHOD]->(:ModalFunction)
# Modal names a class method "<Class>.<method>" (or "<Class>.*" for the class service
# function), so class_id is resolved in transform from that prefix. Best-effort: a function
# whose prefix matches no class simply gets no edge.
class ModalClassToFunctionRel(CartographyRelSchema):
    target_node_label: str = "ModalClass"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("class_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_METHOD"
    properties: ModalClassToFunctionRelProperties = ModalClassToFunctionRelProperties()


@dataclass(frozen=True)
class ModalFunctionSchema(CartographyNodeSchema):
    label: str = "ModalFunction"
    properties: ModalFunctionNodeProperties = ModalFunctionNodeProperties()
    sub_resource_relationship: ModalFunctionToEnvironmentRel = (
        ModalFunctionToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ModalFunctionToAppRel(), ModalClassToFunctionRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([FUNCTION])
