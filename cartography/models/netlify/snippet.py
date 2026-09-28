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
class NetlifySnippetNodeProperties(CartographyNodeProperties):
    # Composite `<site_id>|<snippet_id>`, built in transform(). Netlify's snippet id is the
    # snippet's index in the site's list, so it is unique per site but not stable across
    # deletions: removing the first snippet renumbers the rest.
    id: PropertyRef = PropertyRef(
        "id",
        description="Composite `<site_id>|<snippet_index>`. Netlify's snippet id is the snippet's position in the site's list, so it collides across sites and is renumbered when an earlier snippet is deleted.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef(
        "site_id", description="Id of the site the snippet is injected into."
    )
    snippet_index: PropertyRef = PropertyRef(
        "snippet_index", description="Netlify's positional snippet id."
    )
    title: PropertyRef = PropertyRef("title", description="Display title.")
    # Where in the served HTML the markup is injected: head or footer.
    general_position: PropertyRef = PropertyRef(
        "general_position",
        description="Where the general markup is injected: `head` or `footer`.",
    )
    goal_position: PropertyRef = PropertyRef(
        "goal_position", description="Where the goal markup is injected."
    )
    # The injected markup is stored so that a rule can flag third-party script origins. It is
    # site configuration authored by the team, not a credential.
    general: PropertyRef = PropertyRef("general", description="The injected markup.")
    goal: PropertyRef = PropertyRef("goal", description="The goal-tracking markup.")


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifySnippetToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifySnippet)
class NetlifySnippetToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifySnippetToNetlifyAccountRelProperties = (
        NetlifySnippetToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifySnippetToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifySite)-[:HAS_SNIPPET]->(:NetlifySnippet)
class NetlifySnippetToSiteRel(CartographyRelSchema):
    target_node_label: str = "NetlifySite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SNIPPET"
    properties: NetlifySnippetToSiteRelProperties = NetlifySnippetToSiteRelProperties()


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifySnippetSchema(CartographyNodeSchema):
    """
    A snippet: arbitrary markup Netlify injects into every page a site serves.

    Snippets execute in every visitor's browser with the site's origin, so a third-party script
    added here has the same reach as first-party code.
    """

    label: str = "NetlifySnippet"
    properties: NetlifySnippetNodeProperties = NetlifySnippetNodeProperties()
    sub_resource_relationship: NetlifySnippetToNetlifyAccountRel = (
        NetlifySnippetToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [NetlifySnippetToSiteRel()],
    )
