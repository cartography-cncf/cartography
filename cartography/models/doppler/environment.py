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
class DopplerEnvironmentNodeProperties(CartographyNodeProperties):
    # id is the composite "{project}/{env_id}" built in transform; env_id is the
    # per-project environment slug (e.g. "dev").
    id: PropertyRef = PropertyRef("id")
    env_id: PropertyRef = PropertyRef("env_id")
    name: PropertyRef = PropertyRef("name")
    project: PropertyRef = PropertyRef("project")
    created_at: PropertyRef = PropertyRef("created_at")
    initial_fetch_at: PropertyRef = PropertyRef("initial_fetch_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerEnvironmentToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerEnvironment)
class DopplerEnvironmentToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerEnvironmentToWorkplaceRelProperties = (
        DopplerEnvironmentToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerEnvironmentToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerProject)-[:HAS_ENVIRONMENT]->(:DopplerEnvironment)
class DopplerEnvironmentToProjectRel(CartographyRelSchema):
    target_node_label: str = "DopplerProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"slug": PropertyRef("project")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ENVIRONMENT"
    properties: DopplerEnvironmentToProjectRelProperties = (
        DopplerEnvironmentToProjectRelProperties()
    )


@dataclass(frozen=True)
class DopplerEnvironmentSchema(CartographyNodeSchema):
    label: str = "DopplerEnvironment"
    properties: DopplerEnvironmentNodeProperties = DopplerEnvironmentNodeProperties()
    sub_resource_relationship: DopplerEnvironmentToWorkplaceRel = (
        DopplerEnvironmentToWorkplaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DopplerEnvironmentToProjectRel()],
    )
