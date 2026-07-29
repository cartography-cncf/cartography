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
class DopplerConfigNodeProperties(CartographyNodeProperties):
    # id is the composite "{project}/{name}" built in transform.
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    project: PropertyRef = PropertyRef("project")
    environment: PropertyRef = PropertyRef("environment")
    root: PropertyRef = PropertyRef("root")
    locked: PropertyRef = PropertyRef("locked")
    created_at: PropertyRef = PropertyRef("created_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerConfigToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerConfig)
class DopplerConfigToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerConfigToWorkplaceRelProperties = (
        DopplerConfigToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerConfigToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerProject)-[:HAS_CONFIG]->(:DopplerConfig)
class DopplerConfigToProjectRel(CartographyRelSchema):
    target_node_label: str = "DopplerProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"slug": PropertyRef("project")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CONFIG"
    properties: DopplerConfigToProjectRelProperties = (
        DopplerConfigToProjectRelProperties()
    )


@dataclass(frozen=True)
class DopplerConfigToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerConfig)-[:IN_ENVIRONMENT]->(:DopplerEnvironment)
class DopplerConfigToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "DopplerEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("environment_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_ENVIRONMENT"
    properties: DopplerConfigToEnvironmentRelProperties = (
        DopplerConfigToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class DopplerConfigSchema(CartographyNodeSchema):
    label: str = "DopplerConfig"
    properties: DopplerConfigNodeProperties = DopplerConfigNodeProperties()
    sub_resource_relationship: DopplerConfigToWorkplaceRel = (
        DopplerConfigToWorkplaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DopplerConfigToProjectRel(), DopplerConfigToEnvironmentRel()],
    )
