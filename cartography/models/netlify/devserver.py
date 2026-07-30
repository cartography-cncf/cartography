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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef("site_id")
    title: PropertyRef = PropertyRef("title")
    state: PropertyRef = PropertyRef("state")
    branch: PropertyRef = PropertyRef("branch")
    environment: PropertyRef = PropertyRef("environment")
    # A running dev server is reachable at a public *.netlify.app hostname, so it is live attack
    # surface exposing an unbuilt working copy of the site.
    url: PropertyRef = PropertyRef("url", extra_index=True)
    stop_reason: PropertyRef = PropertyRef("stop_reason")
    last_activity_at: PropertyRef = PropertyRef("last_activity_at")
    enqueued_at: PropertyRef = PropertyRef("enqueued_at")
    starting_at: PropertyRef = PropertyRef("starting_at")
    live_at: PropertyRef = PropertyRef("live_at")
    error_at: PropertyRef = PropertyRef("error_at")
    done_at: PropertyRef = PropertyRef("done_at")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


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
