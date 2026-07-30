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
class NetlifyHookNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef("site_id")
    # Destination kind: url, slack, email, github_commit_status, gitlab_review_comment, ...
    type: PropertyRef = PropertyRef("type")
    # The deploy lifecycle event that fires it, e.g. deploy_created, deploy_failed.
    event: PropertyRef = PropertyRef("event")
    disabled: PropertyRef = PropertyRef("disabled")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyHookToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyHook)
class NetlifyHookToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyHookToNetlifyAccountRelProperties = (
        NetlifyHookToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyHookToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifySite)-[:HAS_NOTIFICATION_HOOK]->(:NetlifyHook)
class NetlifyHookToSiteRel(CartographyRelSchema):
    target_node_label: str = "NetlifySite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_NOTIFICATION_HOOK"
    properties: NetlifyHookToSiteRelProperties = NetlifyHookToSiteRelProperties()


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyHookSchema(CartographyNodeSchema):
    """
    An outgoing notification hook: where Netlify reports a site's deploy events.

    The hook's `data` object is not ingested. Depending on the hook type it holds the Slack
    incoming-webhook URL, the target webhook URL, or a git provider access token, all of which
    are credentials.
    """

    label: str = "NetlifyHook"
    properties: NetlifyHookNodeProperties = NetlifyHookNodeProperties()
    sub_resource_relationship: NetlifyHookToNetlifyAccountRel = (
        NetlifyHookToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [NetlifyHookToSiteRel()],
    )
