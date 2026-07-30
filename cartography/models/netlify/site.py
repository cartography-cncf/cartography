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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    state: PropertyRef = PropertyRef("state")
    lifecycle_state: PropertyRef = PropertyRef("lifecycle_state")
    plan: PropertyRef = PropertyRef("plan")
    # Public entry points. `url`/`ssl_url` are the primary ones, `default_domain` is the
    # always-present *.netlify.app hostname and `custom_domain` the customer's own.
    url: PropertyRef = PropertyRef("url", extra_index=True)
    ssl_url: PropertyRef = PropertyRef("ssl_url")
    admin_url: PropertyRef = PropertyRef("admin_url")
    default_domain: PropertyRef = PropertyRef("default_domain", extra_index=True)
    custom_domain: PropertyRef = PropertyRef("custom_domain", extra_index=True)
    domain_aliases: PropertyRef = PropertyRef("domain_aliases")
    branch_deploy_custom_domain: PropertyRef = PropertyRef(
        "branch_deploy_custom_domain",
    )
    deploy_preview_custom_domain: PropertyRef = PropertyRef(
        "deploy_preview_custom_domain",
    )
    # TLS posture. `ssl` reports whether a certificate is in place, `force_ssl` whether plain
    # HTTP is redirected.
    ssl: PropertyRef = PropertyRef("ssl")
    force_ssl: PropertyRef = PropertyRef("force_ssl")
    ssl_status: PropertyRef = PropertyRef("ssl_status")
    automatic_tls_provisioning: PropertyRef = PropertyRef(
        "automatic_tls_provisioning",
    )
    managed_dns: PropertyRef = PropertyRef("managed_dns")
    dns_zone_id: PropertyRef = PropertyRef("dns_zone_id")
    # Access controls on the deployed site. The password itself is never ingested; Netlify
    # already exposes only the `has_password` boolean.
    has_password: PropertyRef = PropertyRef("has_password")
    password_context: PropertyRef = PropertyRef("password_context")
    sso_login: PropertyRef = PropertyRef("sso_login")
    sso_login_context: PropertyRef = PropertyRef("sso_login_context")
    account_sso_login: PropertyRef = PropertyRef("account_sso_login")
    # JWT-based role gating for Netlify Identity. `jwt_secret` is a secret and is dropped;
    # `has_jwt_secret` records only whether one is configured.
    has_jwt_secret: PropertyRef = PropertyRef("has_jwt_secret")
    jwt_roles_path: PropertyRef = PropertyRef("jwt_roles_path")
    identity_instance_id: PropertyRef = PropertyRef("identity_instance_id")
    # Deploy guardrails.
    prevent_non_git_prod_deploys: PropertyRef = PropertyRef(
        "prevent_non_git_prod_deploys",
    )
    deploy_retention_in_days: PropertyRef = PropertyRef("deploy_retention_in_days")
    disabled: PropertyRef = PropertyRef("disabled")
    disabled_reason: PropertyRef = PropertyRef("disabled_reason")
    # Build and runtime configuration.
    build_image: PropertyRef = PropertyRef("build_image")
    functions_region: PropertyRef = PropertyRef("functions_region")
    functions_timeout: PropertyRef = PropertyRef("functions_timeout")
    prerender: PropertyRef = PropertyRef("prerender")
    use_functions: PropertyRef = PropertyRef("use_functions")
    use_forms: PropertyRef = PropertyRef("use_forms")
    use_edge_handlers: PropertyRef = PropertyRef("use_edge_handlers")
    has_database: PropertyRef = PropertyRef("has_database")
    # Source repository, flattened from `build_settings` by transform(). `repo_path` is the
    # `owner/name` form used to join against GitHubRepository.fullname.
    git_provider: PropertyRef = PropertyRef("git_provider")
    repo_path: PropertyRef = PropertyRef("repo_path", extra_index=True)
    repo_url: PropertyRef = PropertyRef("repo_url")
    repo_branch: PropertyRef = PropertyRef("repo_branch")
    repo_allowed_branches: PropertyRef = PropertyRef("repo_allowed_branches")
    repo_public: PropertyRef = PropertyRef("repo_public")
    repo_private_logs: PropertyRef = PropertyRef("repo_private_logs")
    repo_stop_builds: PropertyRef = PropertyRef("repo_stop_builds")
    build_command: PropertyRef = PropertyRef("build_command")
    publish_dir: PropertyRef = PropertyRef("publish_dir")
    functions_dir: PropertyRef = PropertyRef("functions_dir")
    deploy_key_id: PropertyRef = PropertyRef("deploy_key_id")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


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
