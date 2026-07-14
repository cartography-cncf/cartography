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
    id: PropertyRef = PropertyRef("id", description="WorkOS directory group ID.")
    idp_id: PropertyRef = PropertyRef(
        "idp_id",
        extra_index=True,
        description="Group ID assigned by the identity provider.",
    )
    name: PropertyRef = PropertyRef("name", description="Directory group name.")
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="RFC 3339 timestamp when the directory group was created.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="RFC 3339 timestamp when the directory group was updated.",
    )
    raw_attributes: PropertyRef = PropertyRef(
        "raw_attributes", description="Raw group attributes from the identity provider."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )


@dataclass(frozen=True)
class WorkOSDirectoryGroupToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSDirectoryGroup)
class WorkOSDirectoryGroupToEnvironmentRel(CartographyRelSchema):
    """The WorkOS environment contains this directory group as a resource."""

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
    """The WorkOS directory contains this directory group."""

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
    """The WorkOS directory group belongs to its organization."""

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
    """A group synchronized from an external identity provider through WorkOS."""

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
