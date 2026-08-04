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
from cartography.models.ontology.labels import COMPUTE_INSTANCE


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyDevServerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The Netlify dev server id.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef(
        "site_id", description="Id of the site the dev server runs a copy of."
    )
    title: PropertyRef = PropertyRef("title", description="Display title.")
    state: PropertyRef = PropertyRef(
        "state",
        description="Dev server state, e.g. `enqueued`, `starting`, `live`, `done`.",
    )
    branch: PropertyRef = PropertyRef(
        "branch", description="Branch the dev server serves."
    )
    environment: PropertyRef = PropertyRef(
        "environment", description="Environment name the dev server runs as."
    )
    # A running dev server is reachable at a public *.netlify.app hostname, so it is live attack
    # surface exposing an unbuilt working copy of the site.
    url: PropertyRef = PropertyRef(
        "url", extra_index=True, description="Public hostname serving the dev server."
    )
    stop_reason: PropertyRef = PropertyRef(
        "stop_reason", description="Why the dev server stopped."
    )
    last_activity_at: PropertyRef = PropertyRef(
        "last_activity_at", description="Last request the dev server served."
    )
    enqueued_at: PropertyRef = PropertyRef(
        "enqueued_at", description="When the dev server was requested."
    )
    starting_at: PropertyRef = PropertyRef(
        "starting_at", description="When the dev server began starting."
    )
    live_at: PropertyRef = PropertyRef(
        "live_at", description="When the dev server became reachable."
    )
    error_at: PropertyRef = PropertyRef(
        "error_at", description="When the dev server failed."
    )
    done_at: PropertyRef = PropertyRef(
        "done_at", description="When the dev server shut down."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the dev server was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the dev server was last modified."
    )


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyDevServerToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyDevServer)
class NetlifyDevServerToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyDevServerToNetlifyAccountRelProperties = (
        NetlifyDevServerToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyDevServerToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifySite)-[:HAS_DEV_SERVER]->(:NetlifyDevServer)
class NetlifyDevServerToSiteRel(CartographyRelSchema):
    target_node_label: str = "NetlifySite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DEV_SERVER"
    properties: NetlifyDevServerToSiteRelProperties = (
        NetlifyDevServerToSiteRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyDevServerSchema(CartographyNodeSchema):
    """
    A Netlify cloud dev server: an ephemeral container running a site's working copy.
    """

    label: str = "NetlifyDevServer"
    properties: NetlifyDevServerNodeProperties = NetlifyDevServerNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_INSTANCE])
    sub_resource_relationship: NetlifyDevServerToNetlifyAccountRel = (
        NetlifyDevServerToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [NetlifyDevServerToSiteRel()],
    )
