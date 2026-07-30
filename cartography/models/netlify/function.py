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
from cartography.models.ontology.labels import FUNCTION


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyFunctionNodeProperties(CartographyNodeProperties):
    # Composite `<site_id>|<branch>|<name>`, built in transform(). Netlify's own function ids
    # are content hashes that change on every build, so keying on them would create a new node
    # per deploy.
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef("site_id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    branch: PropertyRef = PropertyRef("branch")
    # Netlify's per-build function id and content digest, kept as attributes rather than
    # identity so a rebuild updates the node instead of replacing it.
    provider_function_id: PropertyRef = PropertyRef("provider_function_id")
    content_digest: PropertyRef = PropertyRef("content_digest")
    runtime: PropertyRef = PropertyRef("runtime")
    region: PropertyRef = PropertyRef("region")
    memory_mb: PropertyRef = PropertyRef("memory_mb")
    size_bytes: PropertyRef = PropertyRef("size_bytes")
    invocation_mode: PropertyRef = PropertyRef("invocation_mode")
    # Publicly reachable invocation URL, so this is attack surface.
    endpoint: PropertyRef = PropertyRef("endpoint")
    # Cron expression when the function runs on a schedule rather than on request.
    schedule: PropertyRef = PropertyRef("schedule")
    # The underlying provider ("aws_lambda") and the account it runs in, both reported by
    # Netlify on the parent object.
    provider: PropertyRef = PropertyRef("provider")
    provider_account_id: PropertyRef = PropertyRef("provider_account_id")
    log_type: PropertyRef = PropertyRef("log_type")
    created_at: PropertyRef = PropertyRef("created_at")


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyFunctionToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyFunction)
class NetlifyFunctionToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyFunctionToNetlifyAccountRelProperties = (
        NetlifyFunctionToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyFunctionToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifySite)-[:HAS_FUNCTION]->(:NetlifyFunction)
class NetlifyFunctionToSiteRel(CartographyRelSchema):
    target_node_label: str = "NetlifySite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_FUNCTION"
    properties: NetlifyFunctionToSiteRelProperties = (
        NetlifyFunctionToSiteRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyFunctionSchema(CartographyNodeSchema):
    """
    A serverless function deployed on a Netlify site.
    """

    label: str = "NetlifyFunction"
    properties: NetlifyFunctionNodeProperties = NetlifyFunctionNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([FUNCTION])
    sub_resource_relationship: NetlifyFunctionToNetlifyAccountRel = (
        NetlifyFunctionToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [NetlifyFunctionToSiteRel()],
    )
