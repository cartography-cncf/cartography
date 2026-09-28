"""ModalClass lives in klass.py: `class` is a reserved word, so class.py is not importable."""

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
class ModalClassNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Class ID, e.g. `cs-35B2OoyjwFlvFPNjBMCrPK`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Class name.")
    app_id: PropertyRef = PropertyRef("app_id", description="ID of the owning app.")
    environment_name: PropertyRef = PropertyRef(
        "environment_name",
        extra_index=True,
        description="Name of the owning environment.",
    )


@dataclass(frozen=True)
class ModalClassToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalClass)
class ModalClassToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalClassToEnvironmentRelProperties = (
        ModalClassToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class ModalClassToAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalClass)-[:WORKLOAD_PARENT]->(:ModalApp)
class ModalClassToAppRel(CartographyRelSchema):
    target_node_label: str = "ModalApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("app_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: ModalClassToAppRelProperties = ModalClassToAppRelProperties()


@dataclass(frozen=True)
# A Modal class groups methods that share a container lifecycle. It carries no ontology
# label of its own: the runnable units are its methods, which are ModalFunction nodes.
class ModalClassSchema(CartographyNodeSchema):
    """Represents a Modal class, which groups methods sharing a container lifecycle. It carries no ontology label of its own: the runnable units are its methods, which are `ModalFunction` nodes. `HAS_METHOD` is best-effort: it is resolved from the `<Class>.` prefix of the function name, so a function whose prefix matches no known class simply has no edge."""

    label: str = "ModalClass"
    properties: ModalClassNodeProperties = ModalClassNodeProperties()
    sub_resource_relationship: ModalClassToEnvironmentRel = ModalClassToEnvironmentRel()
    other_relationships: OtherRelationships = OtherRelationships([ModalClassToAppRel()])
