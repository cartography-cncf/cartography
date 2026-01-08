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
class WorkOSDirectoryUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    idp_id: PropertyRef = PropertyRef("idp_id", extra_index=True)
    directory_id: PropertyRef = PropertyRef("directory_id", extra_index=True)
    organization_id: PropertyRef = PropertyRef("organization_id", extra_index=True)
    first_name: PropertyRef = PropertyRef("first_name")
    last_name: PropertyRef = PropertyRef("last_name")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    state: PropertyRef = PropertyRef("state")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    custom_attributes: PropertyRef = PropertyRef("custom_attributes")
    raw_attributes: PropertyRef = PropertyRef("raw_attributes")
    role: PropertyRef = PropertyRef("role")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkOSDirectoryUserToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSDirectoryUser)
class WorkOSDirectoryUserToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "WorkOSEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKOS_CLIENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WorkOSDirectoryUserToEnvironmentRelProperties = (
        WorkOSDirectoryUserToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class WorkOSDirectoryUserToDirectoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSDirectory)-[:HAS]->(:WorkOSDirectoryUser)
class WorkOSDirectoryUserToDirectoryRel(CartographyRelSchema):
    target_node_label: str = "WorkOSDirectory"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("directory_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: WorkOSDirectoryUserToDirectoryRelProperties = (
        WorkOSDirectoryUserToDirectoryRelProperties()
    )


@dataclass(frozen=True)
class WorkOSDirectoryUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSDirectoryUser)-[:BELONGS_TO]->(:WorkOSOrganization)
class WorkOSDirectoryUserToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "WorkOSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BELONGS_TO"
    properties: WorkOSDirectoryUserToOrganizationRelProperties = (
        WorkOSDirectoryUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class WorkOSDirectoryUserToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSDirectoryUser)-[:MEMBER_OF]->(:WorkOSDirectoryGroup)
class WorkOSDirectoryUserToGroupRel(CartographyRelSchema):
    target_node_label: str = "WorkOSDirectoryGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: WorkOSDirectoryUserToGroupRelProperties = (
        WorkOSDirectoryUserToGroupRelProperties()
    )


@dataclass(frozen=True)
class WorkOSDirectoryUserSchema(CartographyNodeSchema):
    label: str = "WorkOSDirectoryUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: WorkOSDirectoryUserNodeProperties = WorkOSDirectoryUserNodeProperties()
    sub_resource_relationship: WorkOSDirectoryUserToEnvironmentRel = (
        WorkOSDirectoryUserToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            WorkOSDirectoryUserToDirectoryRel(),
            WorkOSDirectoryUserToOrganizationRel(),
            WorkOSDirectoryUserToGroupRel(),
        ],
    )
