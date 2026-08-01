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
    id: PropertyRef = PropertyRef(
        "id",
        description="Composite `<site_id>|<branch>|<name>`. Netlify's own function ids are content hashes that change on every build, so keying on them would create a new node per deploy.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef(
        "site_id", description="Id of the site the function is deployed on."
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Function name, which is also its route segment.",
    )
    branch: PropertyRef = PropertyRef(
        "branch", description="Branch the function bundle was built from."
    )
    # Netlify's per-build function id and content digest, kept as attributes rather than
    # identity so a rebuild updates the node instead of replacing it.
    provider_function_id: PropertyRef = PropertyRef(
        "provider_function_id", description="Netlify's per-build function id."
    )
    content_digest: PropertyRef = PropertyRef(
        "content_digest", description="Digest of the function's built artifact."
    )
    runtime: PropertyRef = PropertyRef(
        "runtime", description="Runtime the function executes on, e.g. `nodejs24.x`."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the function runs in."
    )
    memory_mb: PropertyRef = PropertyRef(
        "memory_mb", description="Memory allocated to the function, in MB."
    )
    size_bytes: PropertyRef = PropertyRef(
        "size_bytes", description="Size of the built artifact."
    )
    invocation_mode: PropertyRef = PropertyRef(
        "invocation_mode",
        description="How the function is invoked, e.g. `stream`, `buffer`.",
    )
    # Publicly reachable invocation URL, so this is attack surface.
    endpoint: PropertyRef = PropertyRef(
        "endpoint", description="Publicly reachable invocation URL."
    )
    # Cron expression when the function runs on a schedule rather than on request.
    schedule: PropertyRef = PropertyRef(
        "schedule",
        description="Cron expression, when the function runs on a schedule rather than on request.",
    )
    # The underlying provider ("aws_lambda") and the account it runs in, both reported by
    # Netlify on the parent object.
    provider: PropertyRef = PropertyRef(
        "provider", description="Underlying compute provider, e.g. `aws_lambda`."
    )
    provider_account_id: PropertyRef = PropertyRef(
        "provider_account_id", description="Provider account the function runs in."
    )
    log_type: PropertyRef = PropertyRef(
        "log_type", description="Logging pipeline the function reports to."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the function bundle was built."
    )


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
