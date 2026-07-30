from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyDeployKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # The public half of the SSH keypair Netlify uses to clone a private repository. Safe to
    # store, and useful for matching against the deploy keys registered on the git provider.
    public_key: PropertyRef = PropertyRef("public_key")
    created_at: PropertyRef = PropertyRef("created_at")


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyDeployKeyToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyDeployKey)
class NetlifyDeployKeyToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyDeployKeyToNetlifyAccountRelProperties = (
        NetlifyDeployKeyToNetlifyAccountRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyDeployKeySchema(CartographyNodeSchema):
    """
    An SSH deploy key Netlify uses to clone a site's source repository.

    The edge to the sites using it is declared on NetlifySite, which is the side that carries
    the `deploy_key_id`.
    """

    label: str = "NetlifyDeployKey"
    properties: NetlifyDeployKeyNodeProperties = NetlifyDeployKeyNodeProperties()
    sub_resource_relationship: NetlifyDeployKeyToNetlifyAccountRel = (
        NetlifyDeployKeyToNetlifyAccountRel()
    )
