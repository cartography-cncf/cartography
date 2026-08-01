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
    id: PropertyRef = PropertyRef("id", description="The Netlify deploy id.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef(
        "site_id", description="Id of the site this deploy belongs to."
    )
    name: PropertyRef = PropertyRef("name", description="Site name at deploy time.")
    state: PropertyRef = PropertyRef(
        "state", description="Deploy state, e.g. `ready`, `error`, `building`."
    )
    context: PropertyRef = PropertyRef(
        "context",
        description="Deploy context, e.g. `production`, `deploy-preview`, `branch-deploy`.",
    )
    # How the deploy was produced. `deploy_source` is "cli", "git", "api", ...;
    # `manual_deploy` is true when a build artifact was uploaded rather than built from git.
    deploy_source: PropertyRef = PropertyRef(
        "deploy_source",
        description="How the deploy was submitted, e.g. `cli`, `git`, `api`.",
    )
    manual_deploy: PropertyRef = PropertyRef(
        "manual_deploy",
        description="Whether a prebuilt artifact was uploaded rather than built from git.",
    )
    build_id: PropertyRef = PropertyRef(
        "build_id",
        description="Id of the build that produced the deploy, when there was one.",
    )
    # Provenance of the deployed code.
    branch: PropertyRef = PropertyRef(
        "branch", description="Branch the deploy was built from."
    )
    commit_ref: PropertyRef = PropertyRef(
        "commit_ref",
        extra_index=True,
        description="Commit SHA the deploy was built from.",
    )
    commit_url: PropertyRef = PropertyRef(
        "commit_url", description="Link to the commit on the git provider."
    )
    commit_message: PropertyRef = PropertyRef(
        "commit_message", description="Commit message."
    )
    committer: PropertyRef = PropertyRef("committer", description="Committer handle.")
    public_repo: PropertyRef = PropertyRef(
        "public_repo",
        description="Whether the source repository was public at deploy time.",
    )
    # Netlify verifies that the committer is a known team member before deploying. A failure
    # here means unattributed code reached the site.
    strict_contributor_verification_failure: PropertyRef = PropertyRef(
        "strict_contributor_verification_failure",
        description="True when Netlify could not verify the committer against the team. Unattributed code reached the site.",
    )
    # Set when the deploy was produced by a Netlify AI agent runner rather than a human.
    agent_runner_id: PropertyRef = PropertyRef(
        "agent_runner_id",
        description="Set when a Netlify AI agent runner produced the deploy rather than a human.",
    )
    # Netlify's own secrets scanner. `secrets_scan_matches_count` counts findings; the matched
    # values themselves are never ingested.
    secrets_scan_files_scanned: PropertyRef = PropertyRef(
        "secrets_scan_files_scanned",
        description="Number of files Netlify's secrets scanner checked.",
    )
    secrets_scan_matches_count: PropertyRef = PropertyRef(
        "secrets_scan_matches_count",
        description="Number of secrets the scanner matched. The matched values themselves are never ingested.",
    )
    url: PropertyRef = PropertyRef(
        "url", description="Primary URL served by this deploy."
    )
    ssl_url: PropertyRef = PropertyRef(
        "ssl_url", description="HTTPS URL served by this deploy."
    )
    deploy_url: PropertyRef = PropertyRef(
        "deploy_url", description="Permalink URL of this specific deploy."
    )
    deploy_ssl_url: PropertyRef = PropertyRef(
        "deploy_ssl_url", description="HTTPS permalink of this specific deploy."
    )
    admin_url: PropertyRef = PropertyRef(
        "admin_url", description="Netlify admin URL for the deploy."
    )
    framework: PropertyRef = PropertyRef(
        "framework", description="Framework Netlify detected."
    )
    functions_region: PropertyRef = PropertyRef(
        "functions_region", description="Region the deploy's functions run in."
    )
    blobs_region: PropertyRef = PropertyRef(
        "blobs_region", description="Region the deploy's blob store lives in."
    )
    edge_functions_present: PropertyRef = PropertyRef(
        "edge_functions_present", description="Whether the deploy ships edge functions."
    )
    required_functions: PropertyRef = PropertyRef(
        "required_functions", description="Function ids the deploy requires."
    )
    required_edge_functions: PropertyRef = PropertyRef(
        "required_edge_functions", description="Edge function ids the deploy requires."
    )
    database_branch_id: PropertyRef = PropertyRef(
        "database_branch_id", description="Netlify DB branch this deploy is wired to."
    )
    draft: PropertyRef = PropertyRef(
        "draft", description="Whether the deploy is a draft."
    )
    locked: PropertyRef = PropertyRef(
        "locked", description="Whether the deploy is pinned as published."
    )
    skipped: PropertyRef = PropertyRef(
        "skipped", description="Whether the build was skipped."
    )
    error_message: PropertyRef = PropertyRef(
        "error_message", description="Failure reason, when the deploy failed."
    )
    review_id: PropertyRef = PropertyRef(
        "review_id", description="Pull request number the deploy previews."
    )
    review_url: PropertyRef = PropertyRef(
        "review_url", description="Pull request URL the deploy previews."
    )
    pending_review_reason: PropertyRef = PropertyRef(
        "pending_review_reason", description="Why the deploy is awaiting review."
    )
    deploy_time: PropertyRef = PropertyRef(
        "deploy_time", description="How long the deploy took, in seconds."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the deploy was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the deploy was last modified."
    )
    published_at: PropertyRef = PropertyRef(
        "published_at", description="When the deploy became the published one."
    )


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
    """
    The deploy currently published on the site. Cartography ingests only the published
    deploy, not the site's deploy history, so a site has at most one of these.
    """

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
    """The team member who triggered the deploy, when Netlify attributes it to one."""

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
