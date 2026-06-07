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
class WorkOSDirectoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    domain: PropertyRef = PropertyRef("domain")
    state: PropertyRef = PropertyRef("state")
    type: PropertyRef = PropertyRef("type")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkOSDirectoryToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSDirectory)
class WorkOSDirectoryToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "WorkOSEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKOS_CLIENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WorkOSDirectoryToEnvironmentRelProperties = (
        WorkOSDirectoryToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class WorkOSDirectoryToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSDirectory)-[:BELONGS_TO]->(:WorkOSOrganization)
class WorkOSDirectoryToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "WorkOSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BELONGS_TO"
    properties: WorkOSDirectoryToOrganizationRelProperties = (
        WorkOSDirectoryToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class WorkOSDirectorySchema(CartographyNodeSchema):
    label: str = "WorkOSDirectory"
    properties: WorkOSDirectoryNodeProperties = WorkOSDirectoryNodeProperties()
    sub_resource_relationship: WorkOSDirectoryToEnvironmentRel = (
        WorkOSDirectoryToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[WorkOSDirectoryToOrganizationRel()],
    )
