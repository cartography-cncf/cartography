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
from cartography.models.ontology.labels import COMPUTE_SERVICE


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifySiteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The Netlify site id.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Site name, which is also its `*.netlify.app` subdomain.",
    )
    state: PropertyRef = PropertyRef(
        "state", description="Site state, e.g. `current`, `building`, `error`."
    )
    lifecycle_state: PropertyRef = PropertyRef(
        "lifecycle_state", description="Site lifecycle state, e.g. `active`."
    )
    plan: PropertyRef = PropertyRef(
        "plan", description="Plan the site is billed on, e.g. `nf_team_dev`."
    )
    # Public entry points. `url`/`ssl_url` are the primary ones, `default_domain` is the
    # always-present *.netlify.app hostname and `custom_domain` the customer's own.
    url: PropertyRef = PropertyRef(
        "url", extra_index=True, description="Primary URL of the site."
    )
    ssl_url: PropertyRef = PropertyRef("ssl_url", description="HTTPS URL of the site.")
    admin_url: PropertyRef = PropertyRef(
        "admin_url", description="Netlify admin URL for the site."
    )
    default_domain: PropertyRef = PropertyRef(
        "default_domain",
        extra_index=True,
        description="Always-present `*.netlify.app` hostname.",
    )
    custom_domain: PropertyRef = PropertyRef(
        "custom_domain",
        extra_index=True,
        description="Customer's own primary domain, if set.",
    )
    domain_aliases: PropertyRef = PropertyRef(
        "domain_aliases", description="Additional domains serving the same site."
    )
    branch_deploy_custom_domain: PropertyRef = PropertyRef(
        "branch_deploy_custom_domain",
        description="Custom domain pattern for branch deploys.",
    )
    deploy_preview_custom_domain: PropertyRef = PropertyRef(
        "deploy_preview_custom_domain",
        description="Custom domain pattern for deploy previews.",
    )
    # TLS posture. `ssl` reports whether a certificate is in place, `force_ssl` whether plain
    # HTTP is redirected.
    ssl: PropertyRef = PropertyRef(
        "ssl", description="Whether a TLS certificate is in place."
    )
    force_ssl: PropertyRef = PropertyRef(
        "force_ssl", description="Whether plain HTTP is redirected to HTTPS."
    )
    ssl_status: PropertyRef = PropertyRef(
        "ssl_status", description="Provisioning status of the certificate."
    )
    automatic_tls_provisioning: PropertyRef = PropertyRef(
        "automatic_tls_provisioning",
        description="Whether Netlify provisions certificates automatically.",
    )
    managed_dns: PropertyRef = PropertyRef(
        "managed_dns", description="Whether the site's DNS is hosted on Netlify DNS."
    )
    dns_zone_id: PropertyRef = PropertyRef(
        "dns_zone_id",
        description="Id of the Netlify DNS zone serving the site, if any.",
    )
    # Access controls on the deployed site. The password itself is never ingested; Netlify
    # already exposes only the `has_password` boolean.
    has_password: PropertyRef = PropertyRef(
        "has_password",
        description="Whether the site is behind a password. The password itself is never returned by the API.",
    )
    password_context: PropertyRef = PropertyRef(
        "password_context", description="Which deploy contexts the password applies to."
    )
    sso_login: PropertyRef = PropertyRef(
        "sso_login", description="Whether Netlify SSO is required to view the site."
    )
    sso_login_context: PropertyRef = PropertyRef(
        "sso_login_context",
        description="Which deploy contexts the SSO requirement applies to.",
    )
    account_sso_login: PropertyRef = PropertyRef(
        "account_sso_login",
        description="Whether the team-level SSO requirement applies to this site.",
    )
    # JWT-based role gating for Netlify Identity. `jwt_secret` is a secret and is dropped;
    # `has_jwt_secret` records only whether one is configured.
    has_jwt_secret: PropertyRef = PropertyRef(
        "has_jwt_secret",
        description="Whether a Netlify Identity JWT signing secret is configured. The secret itself is dropped.",
    )
    jwt_roles_path: PropertyRef = PropertyRef(
        "jwt_roles_path",
        description="JSON path in the JWT where Netlify reads role claims.",
    )
    identity_instance_id: PropertyRef = PropertyRef(
        "identity_instance_id",
        description="Netlify Identity instance backing the site, if any.",
    )
    # Deploy guardrails.
    prevent_non_git_prod_deploys: PropertyRef = PropertyRef(
        "prevent_non_git_prod_deploys",
        description="Whether production deploys must come from git rather than an upload.",
    )
    deploy_retention_in_days: PropertyRef = PropertyRef(
        "deploy_retention_in_days", description="How long deploys are kept."
    )
    disabled: PropertyRef = PropertyRef(
        "disabled", description="Whether the site has been taken offline."
    )
    disabled_reason: PropertyRef = PropertyRef(
        "disabled_reason", description="Why the site was taken offline."
    )
    # Build and runtime configuration.
    build_image: PropertyRef = PropertyRef(
        "build_image", description="Build image the site builds on, e.g. `noble`."
    )
    functions_region: PropertyRef = PropertyRef(
        "functions_region", description="Region the site's serverless functions run in."
    )
    functions_timeout: PropertyRef = PropertyRef(
        "functions_timeout", description="Function timeout in seconds."
    )
    prerender: PropertyRef = PropertyRef(
        "prerender", description="Prerendering setting."
    )
    use_functions: PropertyRef = PropertyRef(
        "use_functions", description="Whether serverless functions are enabled."
    )
    use_forms: PropertyRef = PropertyRef(
        "use_forms", description="Whether form detection is enabled."
    )
    use_edge_handlers: PropertyRef = PropertyRef(
        "use_edge_handlers", description="Whether edge handlers are enabled."
    )
    has_database: PropertyRef = PropertyRef(
        "has_database", description="Whether a Netlify DB is attached."
    )
    # Source repository, flattened from `build_settings` by transform(). `repo_path` is the
    # `owner/name` form used to join against GitHubRepository.fullname.
    git_provider: PropertyRef = PropertyRef(
        "git_provider", description="Git provider backing the site, e.g. `github`."
    )
    repo_path: PropertyRef = PropertyRef(
        "repo_path",
        extra_index=True,
        description="Source repository in `owner/name` form, used to join to `GitHubRepository`.",
    )
    repo_url: PropertyRef = PropertyRef(
        "repo_url", description="Source repository URL."
    )
    repo_branch: PropertyRef = PropertyRef(
        "repo_branch", description="Production branch."
    )
    repo_allowed_branches: PropertyRef = PropertyRef(
        "repo_allowed_branches", description="Branches Netlify is allowed to build."
    )
    repo_public: PropertyRef = PropertyRef(
        "repo_public", description="Whether the source repository is public."
    )
    repo_private_logs: PropertyRef = PropertyRef(
        "repo_private_logs", description="Whether build logs are kept private."
    )
    repo_stop_builds: PropertyRef = PropertyRef(
        "repo_stop_builds", description="Whether automatic builds are paused."
    )
    build_command: PropertyRef = PropertyRef(
        "build_command", description="Build command."
    )
    publish_dir: PropertyRef = PropertyRef(
        "publish_dir", description="Directory published as the site root."
    )
    functions_dir: PropertyRef = PropertyRef(
        "functions_dir", description="Directory holding the serverless functions."
    )
    deploy_key_id: PropertyRef = PropertyRef(
        "deploy_key_id",
        description="Id of the deploy key used to clone the repository.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the site was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the site was last modified."
    )


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifySiteToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifySite)
class NetlifySiteToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifySiteToNetlifyAccountRelProperties = (
        NetlifySiteToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifySiteToGitHubRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifySite)-[:DEPLOYED_FROM]->(:GitHubRepository), joined on owner/name.
# Best-effort: only created if the GitHub repo has also been ingested (OPTIONAL MATCH).
class NetlifySiteToGitHubRepositoryRel(CartographyRelSchema):
    """
    The GitHub repository the site builds from, joined on the repository's full name.
    Best effort: the edge only exists if that repository has also been ingested.
    """

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"fullname": PropertyRef("repo_path")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED_FROM"
    properties: NetlifySiteToGitHubRepositoryRelProperties = (
        NetlifySiteToGitHubRepositoryRelProperties()
    )


@dataclass(frozen=True)
class NetlifySiteToDeployKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifySite)-[:USES_DEPLOY_KEY]->(:NetlifyDeployKey)
class NetlifySiteToDeployKeyRel(CartographyRelSchema):
    """
    The SSH key the site uses to clone its private repository. This edge is also what
    determines which keys are ingested at all: Netlify lists deploy keys per token rather
    than per team, so only keys a team's own sites reference are attached to that team.
    """

    target_node_label: str = "NetlifyDeployKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("deploy_key_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_DEPLOY_KEY"
    properties: NetlifySiteToDeployKeyRelProperties = (
        NetlifySiteToDeployKeyRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifySiteSchema(CartographyNodeSchema):
    """
    A Netlify site: the deployed web application, its entry points and its build settings.
    """

    label: str = "NetlifySite"
    properties: NetlifySiteNodeProperties = NetlifySiteNodeProperties()
    # The site is the workload that serves traffic, so this is where ComputeService belongs.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_SERVICE])
    sub_resource_relationship: NetlifySiteToNetlifyAccountRel = (
        NetlifySiteToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NetlifySiteToGitHubRepositoryRel(),
            NetlifySiteToDeployKeyRel(),
        ],
    )
