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
    id: PropertyRef = PropertyRef(
        "id", description="Function ID, e.g. `fu-Z8U7DHNMEog5ogYErpRIW8`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Function name. A class method is named `<Class>.<method>`, and a class service function `<Class>.*`.",
    )
    app_id: PropertyRef = PropertyRef("app_id", description="ID of the owning app.")
    # Public URL of a web endpoint, null for a plain function. Every non-null value is
    # internet-reachable.
    #
    # IMPORTANT: this says nothing about whether the endpoint is protected. Modal's
    # `requires_proxy_auth` is write-only and cannot be read back, so protection status is
    # unknowable from the API. Treat any non-null web_url as potentially unauthenticated.
    web_url: PropertyRef = PropertyRef(
        "web_url",
        extra_index=True,
        description="Public URL if this is a web endpoint, else null. Protection status is unknowable, see above.",
    )
    is_web_endpoint: PropertyRef = PropertyRef(
        "is_web_endpoint",
        extra_index=True,
        description="Whether the function is exposed over HTTP.",
    )
    # Raw FUNCTION_TYPE_* value.
    function_type: PropertyRef = PropertyRef(
        "function_type", description="Raw `FUNCTION_TYPE_*` value."
    )
    is_method: PropertyRef = PropertyRef(
        "is_method",
        description="Whether Modal reports this function as a class method.",
    )
    definition_id: PropertyRef = PropertyRef(
        "definition_id", description="Function definition ID, when Modal returns one."
    )
    input_plane_url: PropertyRef = PropertyRef(
        "input_plane_url", description="Input plane endpoint serving this function."
    )
    input_plane_region: PropertyRef = PropertyRef(
        "input_plane_region", description="Region of that input plane."
    )
    environment_name: PropertyRef = PropertyRef(
        "environment_name",
        extra_index=True,
        description="Name of the owning environment.",
    )
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
    """Represents a deployed Modal function, including web endpoints. Enumerated per app from the private `AppGetLayout` RPC. **Every non-null `web_url` is reachable from the public internet.** Cartography cannot tell you whether it is protected: Modal's `requires_proxy_auth` is write-only and is not returned by any read API. Treat such endpoints as potentially unauthenticated and confirm out of band. For the same reason, a deployed function's GPU, CPU, memory, timeout, region, cloud, mounted secrets and volumes, `block_network`, `untrusted`, proxy and schedule are **absent from this node**: Modal only accepts them at deploy time and never returns them. In particular this means `(:ModalFunction)-[:USES_SECRET]->(:ModalSecret)` cannot be built."""

    label: str = "ModalFunction"
    properties: ModalFunctionNodeProperties = ModalFunctionNodeProperties()
    sub_resource_relationship: ModalFunctionToEnvironmentRel = (
        ModalFunctionToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ModalFunctionToAppRel(), ModalClassToFunctionRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([FUNCTION])
