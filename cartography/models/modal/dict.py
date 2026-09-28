from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ModalDictNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Dict ID, e.g. `di-F91whmwZVRH92mOiJgNOCT`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Dict name.")
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the Dict was created."
    )
    environment_name: PropertyRef = PropertyRef(
        "environment_name",
        extra_index=True,
        description="Name of the owning environment.",
    )


@dataclass(frozen=True)
class ModalDictToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalDict)
class ModalDictToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalDictToEnvironmentRelProperties = (
        ModalDictToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
# A Modal Dict: a distributed key-value store scoped to an environment.
#
# It carries no ontology label. `Database` would be a stretch (this is not a queryable
# datastore with its own engine, encryption or backup posture) and the ontology has no
# key-value-store label, so tagging it would surface it wrongly to cross-provider datastore
# rules. Contents are not enumerated: only the container is inventoried.
class ModalDictSchema(CartographyNodeSchema):
    """Represents a Modal Dict: a distributed key-value store scoped to an environment. Only the container is inventoried; its contents are not enumerated. It carries no ontology label. `Database` would be a stretch, since this is not a queryable datastore with its own engine, encryption or backup posture, and the ontology has no key-value-store label, so tagging it would surface it wrongly to cross-provider datastore rules."""

    label: str = "ModalDict"
    properties: ModalDictNodeProperties = ModalDictNodeProperties()
    sub_resource_relationship: ModalDictToEnvironmentRel = ModalDictToEnvironmentRel()
