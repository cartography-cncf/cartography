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
class SocketDevRepositoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    slug: PropertyRef = PropertyRef("slug", extra_index=True)
    fullname: PropertyRef = PropertyRef("fullname", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    visibility: PropertyRef = PropertyRef("visibility")
    archived: PropertyRef = PropertyRef("archived")
    default_branch: PropertyRef = PropertyRef("default_branch")
    homepage: PropertyRef = PropertyRef("homepage")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


@dataclass(frozen=True)
class SocketDevOrgToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SocketDevOrganization)-[:RESOURCE]->(:SocketDevRepository)
class SocketDevOrgToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "SocketDevOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SocketDevOrgToRepositoryRelProperties = (
        SocketDevOrgToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class SocketDevRepoToCodeRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SocketDevRepository)-[:MONITORS]->(:CodeRepository)
class SocketDevRepoToCodeRepoRel(CartographyRelSchema):
    target_node_label: str = "CodeRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_fullname": PropertyRef("fullname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: SocketDevRepoToCodeRepoRelProperties = (
        SocketDevRepoToCodeRepoRelProperties()
    )


@dataclass(frozen=True)
class SocketDevRepositorySchema(CartographyNodeSchema):
    label: str = "SocketDevRepository"
    properties: SocketDevRepositoryNodeProperties = SocketDevRepositoryNodeProperties()
    sub_resource_relationship: SocketDevOrgToRepositoryRel = (
        SocketDevOrgToRepositoryRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            SocketDevRepoToCodeRepoRel(),
        ],
    )
