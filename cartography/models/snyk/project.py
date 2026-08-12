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
class SnykProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Snyk project.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Project name."
    )
    type: PropertyRef = PropertyRef(
        "type", extra_index=True, description="Snyk project type or package manager."
    )
    origin: PropertyRef = PropertyRef("origin", description="Project origin.")
    target_reference: PropertyRef = PropertyRef(
        "target_reference",
        description="Branch, tag, or image reference monitored by Snyk.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Project creation time."
    )
    target_id: PropertyRef = PropertyRef(
        "target_id",
        extra_index=True,
        description="ID of the Snyk target for this project.",
    )
    org_id: PropertyRef = PropertyRef(
        "org_id", description="ID of the owning Snyk org."
    )


@dataclass(frozen=True)
class SnykProjectToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SnykProjectToOrgRel(CartographyRelSchema):
    """Connects a Snyk organization to one of its projects."""

    target_node_label: str = "SnykOrg"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnykProjectToOrgRelProperties = SnykProjectToOrgRelProperties()


@dataclass(frozen=True)
class SnykProjectToTargetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SnykProjectToTargetRel(CartographyRelSchema):
    """Links a Snyk project to the target that Snyk monitors for it."""

    target_node_label: str = "SnykTarget"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: SnykProjectToTargetRelProperties = SnykProjectToTargetRelProperties()


@dataclass(frozen=True)
class SnykProjectSchema(CartographyNodeSchema):
    """A Snyk project, usually one scanned repository manifest or container image."""

    label: str = "SnykProject"
    properties: SnykProjectNodeProperties = SnykProjectNodeProperties()
    sub_resource_relationship: SnykProjectToOrgRel = SnykProjectToOrgRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [SnykProjectToTargetRel()],
    )
