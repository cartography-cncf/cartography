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
class DopplerSecretNodeProperties(CartographyNodeProperties):
    # id is the composite "{project}/{config}/{NAME}" built in transform.
    # Only the secret NAME is stored, never the raw or computed value.
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    project: PropertyRef = PropertyRef("project")
    config: PropertyRef = PropertyRef("config")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerSecretToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerSecret)
class DopplerSecretToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerSecretToWorkplaceRelProperties = (
        DopplerSecretToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerSecretToConfigRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerConfig)-[:CONTAINS]->(:DopplerSecret)
class DopplerSecretToConfigRel(CartographyRelSchema):
    target_node_label: str = "DopplerConfig"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("config_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: DopplerSecretToConfigRelProperties = (
        DopplerSecretToConfigRelProperties()
    )


@dataclass(frozen=True)
class DopplerSecretSchema(CartographyNodeSchema):
    label: str = "DopplerSecret"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["Secret"]
    )  # Secret label is used for ontology mapping
    properties: DopplerSecretNodeProperties = DopplerSecretNodeProperties()
    sub_resource_relationship: DopplerSecretToWorkplaceRel = (
        DopplerSecretToWorkplaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DopplerSecretToConfigRel()],
    )
