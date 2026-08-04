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


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyBuildHookNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The Netlify build hook id.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef(
        "site_id", description="Id of the site the hook deploys."
    )
    title: PropertyRef = PropertyRef("title", description="Display title.")
    # The branch this hook builds when triggered.
    branch: PropertyRef = PropertyRef(
        "branch", description="Branch the hook builds when triggered."
    )
    draft: PropertyRef = PropertyRef(
        "draft", description="Whether the hook produces a draft deploy."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the hook was created."
    )


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyBuildHookToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyBuildHook)
class NetlifyBuildHookToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyBuildHookToNetlifyAccountRelProperties = (
        NetlifyBuildHookToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyBuildHookToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifySite)-[:HAS_BUILD_HOOK]->(:NetlifyBuildHook)
class NetlifyBuildHookToSiteRel(CartographyRelSchema):
    target_node_label: str = "NetlifySite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_BUILD_HOOK"
    properties: NetlifyBuildHookToSiteRelProperties = (
        NetlifyBuildHookToSiteRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyBuildHookSchema(CartographyNodeSchema):
    """
    An incoming build hook: an unauthenticated URL that triggers a production deploy.

    The URL is not ingested. Anyone holding it can deploy the site, so it is bearer-equivalent
    and belongs in a secret store, not in the graph.
    """

    label: str = "NetlifyBuildHook"
    properties: NetlifyBuildHookNodeProperties = NetlifyBuildHookNodeProperties()
    sub_resource_relationship: NetlifyBuildHookToNetlifyAccountRel = (
        NetlifyBuildHookToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [NetlifyBuildHookToSiteRel()],
    )
