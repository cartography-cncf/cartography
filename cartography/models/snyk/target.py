from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SnykTargetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Snyk target.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    display_name: PropertyRef = PropertyRef(
        "display_name", extra_index=True, description="Human-readable target name."
    )
    url: PropertyRef = PropertyRef(
        "url", extra_index=True, description="Repository, registry, or integration URL."
    )
    origin: PropertyRef = PropertyRef(
        "origin", description="Snyk target origin, such as github or docker-hub."
    )
    org_id: PropertyRef = PropertyRef(
        "org_id", description="ID of the owning Snyk org."
    )


@dataclass(frozen=True)
class SnykTargetToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SnykTargetToOrgRel(CartographyRelSchema):
    """Connects a Snyk organization to a monitored target."""

    target_node_label: str = "SnykOrg"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnykTargetToOrgRelProperties = SnykTargetToOrgRelProperties()


@dataclass(frozen=True)
class SnykTargetSchema(CartographyNodeSchema):
    """A repository, registry, or package source monitored by Snyk."""

    label: str = "SnykTarget"
    properties: SnykTargetNodeProperties = SnykTargetNodeProperties()
    sub_resource_relationship: SnykTargetToOrgRel = SnykTargetToOrgRel()
