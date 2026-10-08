"""
This schema does not handle the org's relationships.  Those are handled by other schemas, for example:
* GitHubTeamSchema defines (GitHubOrganization)-[RESOURCE]->(GitHubTeam)
* GitHubUserSchema defines (GitHubUser)-[MEMBER_OF|ADMIN_OF|UNAFFILIATED]->(GitHubOrganization)
(There may be others, these are just two examples.)
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class GitHubOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("url", description="GitHub organization URL.")
    username: PropertyRef = PropertyRef(
        "login", extra_index=True, description="GitHub organization login."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Organization settings. These are only populated by the organization settings
    # sync, and are null when GitHub does not expose them to the credential. Most
    # are only returned to organization owners.
    name: PropertyRef = PropertyRef("name", description="Organization display name.")
    is_verified: PropertyRef = PropertyRef(
        "is_verified",
        description="Whether GitHub shows the organization as verified through a verified domain.",
    )
    two_factor_requirement_enabled: PropertyRef = PropertyRef(
        "two_factor_requirement_enabled",
        description="Whether members, outside collaborators and billing managers must use two-factor authentication. Visible to organization owners only.",
    )
    default_repository_permission: PropertyRef = PropertyRef(
        "default_repository_permission",
        description="Base permission members get on every repository: `read`, `write`, `admin` or `none`.",
    )
    members_can_create_repositories: PropertyRef = PropertyRef(
        "members_can_create_repositories",
        description="Whether members can create repositories of any visibility.",
    )
    members_can_create_public_repositories: PropertyRef = PropertyRef(
        "members_can_create_public_repositories",
        description="Whether members can create public repositories.",
    )
    members_can_create_private_repositories: PropertyRef = PropertyRef(
        "members_can_create_private_repositories",
        description="Whether members can create private repositories.",
    )
    members_can_create_internal_repositories: PropertyRef = PropertyRef(
        "members_can_create_internal_repositories",
        description="Whether members can create internal repositories. GitHub Enterprise only.",
    )
    members_can_fork_private_repositories: PropertyRef = PropertyRef(
        "members_can_fork_private_repositories",
        description="Whether members can fork private and internal repositories.",
    )
    members_can_create_public_pages: PropertyRef = PropertyRef(
        "members_can_create_public_pages",
        description="Whether members can publish public GitHub Pages sites.",
    )
    web_commit_signoff_required: PropertyRef = PropertyRef(
        "web_commit_signoff_required",
        description="Whether commits made in the web interface require a sign-off.",
    )
    deploy_keys_enabled_for_repositories: PropertyRef = PropertyRef(
        "deploy_keys_enabled_for_repositories",
        description="Whether repositories can use deploy keys.",
    )
    advanced_security_enabled_for_new_repositories: PropertyRef = PropertyRef(
        "advanced_security_enabled_for_new_repositories",
        description="Deprecated by GitHub in favor of code security configurations. Whether GitHub Advanced Security is enabled on new repositories.",
    )
    dependabot_alerts_enabled_for_new_repositories: PropertyRef = PropertyRef(
        "dependabot_alerts_enabled_for_new_repositories",
        description="Deprecated by GitHub in favor of code security configurations. Whether Dependabot alerts are enabled on new repositories.",
    )
    dependabot_security_updates_enabled_for_new_repositories: PropertyRef = PropertyRef(
        "dependabot_security_updates_enabled_for_new_repositories",
        description="Deprecated by GitHub in favor of code security configurations. Whether Dependabot security updates are enabled on new repositories.",
    )
    dependency_graph_enabled_for_new_repositories: PropertyRef = PropertyRef(
        "dependency_graph_enabled_for_new_repositories",
        description="Deprecated by GitHub in favor of code security configurations. Whether the dependency graph is enabled on new repositories.",
    )
    secret_scanning_enabled_for_new_repositories: PropertyRef = PropertyRef(
        "secret_scanning_enabled_for_new_repositories",
        description="Deprecated by GitHub in favor of code security configurations. Whether secret scanning is enabled on new repositories.",
    )
    secret_scanning_push_protection_enabled_for_new_repositories: PropertyRef = (
        PropertyRef(
            "secret_scanning_push_protection_enabled_for_new_repositories",
            description="Deprecated by GitHub in favor of code security configurations. Whether secret scanning push protection is enabled on new repositories.",
        )
    )
    secret_scanning_push_protection_custom_link_enabled: PropertyRef = PropertyRef(
        "secret_scanning_push_protection_custom_link_enabled",
        description="Whether push protection blocks show a custom organization link.",
    )
    ip_allow_list_enabled: PropertyRef = PropertyRef(
        "ip_allow_list_enabled",
        description="Whether the organization IP allow list is enabled.",
    )
    notification_delivery_restricted: PropertyRef = PropertyRef(
        "notification_delivery_restricted",
        description="Whether email notifications may only be delivered to verified or approved domains.",
    )
    domain_count: PropertyRef = PropertyRef(
        "domain_count",
        description="Number of domains configured on the organization. Null when the domain list was unavailable.",
    )
    verified_domain_count: PropertyRef = PropertyRef(
        "verified_domain_count",
        description="Number of verified domains on the organization. Null when the domain list was unavailable.",
    )
    actions_enabled_repositories: PropertyRef = PropertyRef(
        "actions_enabled_repositories",
        description="Repositories where GitHub Actions may run: `all`, `none` or `selected`.",
    )
    actions_allowed_actions: PropertyRef = PropertyRef(
        "actions_allowed_actions",
        description="Actions and reusable workflows that may run: `all`, `local_only` or `selected`.",
    )
    actions_sha_pinning_required: PropertyRef = PropertyRef(
        "actions_sha_pinning_required",
        description="Whether workflows must pin actions to a full-length commit SHA.",
    )
    actions_github_owned_allowed: PropertyRef = PropertyRef(
        "actions_github_owned_allowed",
        description="Whether GitHub-owned actions are allowed when `actions_allowed_actions` is `selected`.",
    )
    actions_verified_allowed: PropertyRef = PropertyRef(
        "actions_verified_allowed",
        description="Whether Marketplace actions from verified creators are allowed when `actions_allowed_actions` is `selected`.",
    )
    actions_patterns_allowed: PropertyRef = PropertyRef(
        "actions_patterns_allowed",
        description="Action and reusable workflow patterns allowed when `actions_allowed_actions` is `selected`.",
    )
    actions_default_workflow_permissions: PropertyRef = PropertyRef(
        "actions_default_workflow_permissions",
        description="Default `GITHUB_TOKEN` permissions for workflows: `read` or `write`.",
    )
    actions_can_approve_pull_request_reviews: PropertyRef = PropertyRef(
        "actions_can_approve_pull_request_reviews",
        description="Whether workflows can create or approve pull requests.",
    )
    copilot_plan_type: PropertyRef = PropertyRef(
        "copilot_plan_type",
        description="Copilot plan for the organization, such as `business` or `enterprise`.",
    )
    copilot_seat_management_setting: PropertyRef = PropertyRef(
        "copilot_seat_management_setting",
        description="Copilot seat assignment mode: `assign_all`, `assign_selected`, `disabled` or `unconfigured`.",
    )
    copilot_seat_count: PropertyRef = PropertyRef(
        "copilot_seat_count", description="Total number of assigned Copilot seats."
    )
    copilot_public_code_suggestions: PropertyRef = PropertyRef(
        "copilot_public_code_suggestions",
        description="Whether Copilot may suggest code matching public code: `allow`, `block` or `unconfigured`.",
    )
    copilot_ide_chat: PropertyRef = PropertyRef(
        "copilot_ide_chat",
        description="Copilot Chat in the IDE policy: `enabled`, `disabled` or `unconfigured`.",
    )
    copilot_platform_chat: PropertyRef = PropertyRef(
        "copilot_platform_chat",
        description="Copilot Chat on GitHub.com policy: `enabled`, `disabled` or `unconfigured`.",
    )
    copilot_cli: PropertyRef = PropertyRef(
        "copilot_cli",
        description="Copilot in the CLI policy: `enabled`, `disabled` or `unconfigured`.",
    )


@dataclass(frozen=True)
class GitHubOrganizationSchema(CartographyNodeSchema):
    """An organization in GitHub."""

    label: str = "GitHubOrganization"
    properties: GitHubOrganizationNodeProperties = GitHubOrganizationNodeProperties()
    other_relationships = None
    sub_resource_relationship = None
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
