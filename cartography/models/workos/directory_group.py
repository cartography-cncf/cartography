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
class WorkOSDirectoryGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    idp_id: PropertyRef = PropertyRef("idp_id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    raw_attributes: PropertyRef = PropertyRef("raw_attributes")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkOSDirectoryGroupToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSDirectoryGroup)
class WorkOSDirectoryGroupToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "WorkOSEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKOS_CLIENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WorkOSDirectoryGroupToEnvironmentRelProperties = (
        WorkOSDirectoryGroupToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class WorkOSDirectoryGroupToDirectoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSDirectory)-[:HAS]->(:WorkOSDirectoryGroup)
class WorkOSDirectoryGroupToDirectoryRel(CartographyRelSchema):
    target_node_label: str = "WorkOSDirectory"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("directory_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: WorkOSDirectoryGroupToDirectoryRelProperties = (
        WorkOSDirectoryGroupToDirectoryRelProperties()
    )


@dataclass(frozen=True)
class WorkOSDirectoryGroupToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSDirectoryGroup)-[:BELONGS_TO]->(:WorkOSOrganization)
class WorkOSDirectoryGroupToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "WorkOSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BELONGS_TO"
    properties: WorkOSDirectoryGroupToOrganizationRelProperties = (
        WorkOSDirectoryGroupToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class WorkOSDirectoryGroupSchema(CartographyNodeSchema):
    label: str = "WorkOSDirectoryGroup"
    properties: WorkOSDirectoryGroupNodeProperties = (
        WorkOSDirectoryGroupNodeProperties()
    )
    sub_resource_relationship: WorkOSDirectoryGroupToEnvironmentRel = (
        WorkOSDirectoryGroupToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            WorkOSDirectoryGroupToDirectoryRel(),
            WorkOSDirectoryGroupToOrganizationRel(),
        ],
    )
