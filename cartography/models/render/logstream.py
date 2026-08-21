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
class RenderLogStreamNodeProperties(CartographyNodeProperties):
    # Render exposes at most one log stream per workspace, with no id of its own; the
    # owning workspace's id is unique per workspace and stable across syncs.
    id: PropertyRef = PropertyRef(
        "ownerId",
        description="ID of the owning Render workspace (used as this node's id).",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    endpoint: PropertyRef = PropertyRef(
        "endpoint", description="Destination endpoint logs are streamed to."
    )
    preview: PropertyRef = PropertyRef(
        "preview",
        description="Whether preview environment logs are included: `send` or `drop`.",
    )


@dataclass(frozen=True)
class RenderLogStreamToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderLogStream)
class RenderLogStreamToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to its log stream configuration."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderLogStreamToTenantRelProperties = (
        RenderLogStreamToTenantRelProperties()
    )


@dataclass(frozen=True)
class RenderLogStreamSchema(CartographyNodeSchema):
    """
    A Render workspace's log stream configuration: where logs are shipped externally.

    The API never returns the stream's auth token in this response (confirmed in the
    API docs), so there is nothing sensitive to discard here the way secretfiles.py
    discards secret file content.
    """

    label: str = "RenderLogStream"
    properties: RenderLogStreamNodeProperties = RenderLogStreamNodeProperties()
    sub_resource_relationship: RenderLogStreamToTenantRel = RenderLogStreamToTenantRel()
