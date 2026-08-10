"""
RE: why NetlifyDeployKey carries no relationships on its node schema

``GET /deploy_keys`` takes no team parameter: it returns every key the token can see. So with a
token that reaches several teams, each team's sync sees the same keys and stamps them with its own
update tag. A node-schema ``sub_resource_relationship`` would then make the generated cleanup
``MATCH (n:NetlifyDeployKey)<-[:RESOURCE]-(:NetlifyAccount{id: $NETLIFY_ACCOUNT_ID})
WHERE n.lastupdated <> $UPDATE_TAG ... DETACH DELETE n`` delete every key another team's sync last
touched, on every run.

The team edge is therefore a MatchLink, scoped by ``_sub_resource_id`` to the team being synced,
and it means only "this team's sync saw this key". The precise attribution is the
``(:NetlifySite)-[:USES_DEPLOY_KEY]->`` edge, which comes from the site's own build settings and is
safe as a node-schema relationship because a site is genuinely team-scoped.

Same reasoning as NetlifyUser; see the docstring in models/netlify/user.py for the two cleanup
statements involved.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyDeployKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The Netlify deploy key id.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # The public half of the SSH keypair Netlify uses to clone a private repository. Safe to
    # store, and useful for matching against the deploy keys registered on the git provider.
    public_key: PropertyRef = PropertyRef(
        "public_key", description="Public half of the SSH keypair."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the key was created."
    )


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyDeployKeyToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyDeployKey)
class NetlifyDeployKeyToAccountMatchLink(CartographyRelSchema):
    source_node_label: str = "NetlifyDeployKey"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("id")},
    )
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyDeployKeyToAccountRelProperties = (
        NetlifyDeployKeyToAccountRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyDeployKeySchema(CartographyNodeSchema):
    """
    An SSH deploy key Netlify uses to clone a site's source repository.

    The team edge is a MatchLink and the sites-using-it edge is declared on NetlifySite; see the
    module docstring.
    """

    label: str = "NetlifyDeployKey"
    properties: NetlifyDeployKeyNodeProperties = NetlifyDeployKeyNodeProperties()
    sub_resource_relationship = None
