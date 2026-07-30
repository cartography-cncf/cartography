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
class NetlifyDeployNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef("site_id")
    name: PropertyRef = PropertyRef("name")
    state: PropertyRef = PropertyRef("state")
    context: PropertyRef = PropertyRef("context")
    # How the deploy was produced. `deploy_source` is "cli", "git", "api", ...;
    # `manual_deploy` is true when a build artifact was uploaded rather than built from git.
    deploy_source: PropertyRef = PropertyRef("deploy_source")
    manual_deploy: PropertyRef = PropertyRef("manual_deploy")
    build_id: PropertyRef = PropertyRef("build_id")
    # Provenance of the deployed code.
    branch: PropertyRef = PropertyRef("branch")
    commit_ref: PropertyRef = PropertyRef("commit_ref", extra_index=True)
    commit_url: PropertyRef = PropertyRef("commit_url")
    commit_message: PropertyRef = PropertyRef("commit_message")
    committer: PropertyRef = PropertyRef("committer")
    public_repo: PropertyRef = PropertyRef("public_repo")
    # Netlify verifies that the committer is a known team member before deploying. A failure
    # here means unattributed code reached the site.
    strict_contributor_verification_failure: PropertyRef = PropertyRef(
        "strict_contributor_verification_failure",
    )
    # Set when the deploy was produced by a Netlify AI agent runner rather than a human.
    agent_runner_id: PropertyRef = PropertyRef("agent_runner_id")
    # Netlify's own secrets scanner. `secrets_scan_matches_count` counts findings; the matched
    # values themselves are never ingested.
    secrets_scan_files_scanned: PropertyRef = PropertyRef(
        "secrets_scan_files_scanned",
    )
    secrets_scan_matches_count: PropertyRef = PropertyRef(
        "secrets_scan_matches_count",
    )
    url: PropertyRef = PropertyRef("url")
    ssl_url: PropertyRef = PropertyRef("ssl_url")
    deploy_url: PropertyRef = PropertyRef("deploy_url")
    deploy_ssl_url: PropertyRef = PropertyRef("deploy_ssl_url")
    admin_url: PropertyRef = PropertyRef("admin_url")
    framework: PropertyRef = PropertyRef("framework")
    functions_region: PropertyRef = PropertyRef("functions_region")
    blobs_region: PropertyRef = PropertyRef("blobs_region")
    edge_functions_present: PropertyRef = PropertyRef("edge_functions_present")
    required_functions: PropertyRef = PropertyRef("required_functions")
    required_edge_functions: PropertyRef = PropertyRef("required_edge_functions")
    database_branch_id: PropertyRef = PropertyRef("database_branch_id")
    draft: PropertyRef = PropertyRef("draft")
    locked: PropertyRef = PropertyRef("locked")
    skipped: PropertyRef = PropertyRef("skipped")
    error_message: PropertyRef = PropertyRef("error_message")
    review_id: PropertyRef = PropertyRef("review_id")
    review_url: PropertyRef = PropertyRef("review_url")
    pending_review_reason: PropertyRef = PropertyRef("pending_review_reason")
    deploy_time: PropertyRef = PropertyRef("deploy_time")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    published_at: PropertyRef = PropertyRef("published_at")


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyDeployToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyDeploy)
class NetlifyDeployToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyDeployToNetlifyAccountRelProperties = (
        NetlifyDeployToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyDeployToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifySite)-[:HAS_DEPLOY]->(:NetlifyDeploy)
class NetlifyDeployToSiteRel(CartographyRelSchema):
    target_node_label: str = "NetlifySite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DEPLOY"
    properties: NetlifyDeployToSiteRelProperties = NetlifyDeployToSiteRelProperties()


@dataclass(frozen=True)
class NetlifyDeployToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyDeploy)-[:DEPLOYED_BY]->(:NetlifyUser)
class NetlifyDeployToUserRel(CartographyRelSchema):
    target_node_label: str = "NetlifyUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED_BY"
    properties: NetlifyDeployToUserRelProperties = NetlifyDeployToUserRelProperties()


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyDeploySchema(CartographyNodeSchema):
    """
    The deploy currently published on a Netlify site.

    Only the published deploy is ingested. Netlify keeps the full deploy history behind a
    paginated endpoint that can hold thousands of entries per site, and the published deploy is
    embedded in the site payload, so this costs no extra API request and yields a bounded,
    deterministic set that cleanup can safely treat as exhaustive.
    """

    label: str = "NetlifyDeploy"
    properties: NetlifyDeployNodeProperties = NetlifyDeployNodeProperties()
    sub_resource_relationship: NetlifyDeployToNetlifyAccountRel = (
        NetlifyDeployToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NetlifyDeployToSiteRel(),
            NetlifyDeployToUserRel(),
        ],
    )
