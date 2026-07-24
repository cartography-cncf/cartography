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
class DopplerServiceTokenNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("slug")
    name: PropertyRef = PropertyRef("name")
    project: PropertyRef = PropertyRef("project")
    environment: PropertyRef = PropertyRef("environment")
    config: PropertyRef = PropertyRef("config")
    created_at: PropertyRef = PropertyRef("created_at")
    expires_at: PropertyRef = PropertyRef("expires_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerServiceTokenToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerServiceToken)
class DopplerServiceTokenToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerServiceTokenToWorkplaceRelProperties = (
        DopplerServiceTokenToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerServiceTokenToConfigRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerConfig)-[:HAS_TOKEN]->(:DopplerServiceToken)
class DopplerServiceTokenToConfigRel(CartographyRelSchema):
    target_node_label: str = "DopplerConfig"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("config_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TOKEN"
    properties: DopplerServiceTokenToConfigRelProperties = (
        DopplerServiceTokenToConfigRelProperties()
    )


@dataclass(frozen=True)
class DopplerServiceTokenSchema(CartographyNodeSchema):
    label: str = "DopplerServiceToken"
    properties: DopplerServiceTokenNodeProperties = DopplerServiceTokenNodeProperties()
    sub_resource_relationship: DopplerServiceTokenToWorkplaceRel = (
        DopplerServiceTokenToWorkplaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DopplerServiceTokenToConfigRel()],
    )
