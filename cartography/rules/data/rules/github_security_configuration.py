from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference


class GitHubSecurityConfigurationOutput(Finding):
    asset_name: str | None = None
    asset_id: str | None = None
    organization: str | None = None
    issue: str | None = None
    current_value: str | None = None
    repository_selection: str | None = None


def _organization_setting_fact(
    issue: str,
    name: str,
    description: str,
    condition: str,
    evaluated: str,
    current_value: str,
) -> Fact:
    """
    Build a fact over a GitHubOrganization setting. `condition` selects failing
    organizations and `evaluated` selects organizations whose setting is known.
    """
    return Fact(
        id=f"github_org_{issue}",
        name=name,
        description=description,
        cypher_query=f"""
        MATCH (n:GitHubOrganization)
        WHERE {condition}
        RETURN n.username AS asset_name, n.id AS asset_id,
            n.username AS organization, '{issue}' AS issue,
            {current_value} AS current_value
        """,
        cypher_visual_query=f"""
        MATCH (n:GitHubOrganization)
        WHERE {condition}
        RETURN n
        """,
        cypher_count_query=f"""
        MATCH (n:GitHubOrganization)
        WHERE {evaluated}
        RETURN count(n) AS count
        """,
        asset_label="GitHubOrganization",
        asset_id_field="asset_id",
        identity_fields=("asset_id", "issue"),
        module=Module.GITHUB,
        maturity=Maturity.EXPERIMENTAL,
    )


# Repository secret protection

_repository_secret_scanning_disabled = Fact(
    id="github_repository_secret_scanning_disabled",
    name="Repositories without secret scanning",
    description=(
        "Unarchived repositories where GitHub reports secret scanning as disabled. "
        "Repositories whose settings are not visible to the credential are not "
        "evaluated."
    ),
    cypher_query="""
    MATCH (n:GitHubRepository)
    WHERE n.secret_scanning_enabled = false AND coalesce(n.archived, false) = false
    RETURN n.fullname AS asset_name, n.id AS asset_id,
        split(n.fullname, '/')[0] AS organization,
        'repository_secret_scanning_disabled' AS issue,
        n.visibility AS current_value
    """,
    cypher_visual_query="""
    MATCH (n:GitHubRepository)
    WHERE n.secret_scanning_enabled = false AND coalesce(n.archived, false) = false
    RETURN n
    """,
    cypher_count_query="""
    MATCH (n:GitHubRepository)
    WHERE n.secret_scanning_enabled IS NOT NULL AND coalesce(n.archived, false) = false
    RETURN count(n) AS count
    """,
    asset_label="GitHubRepository",
    asset_id_field="asset_id",
    identity_fields=("asset_id", "issue"),
    module=Module.GITHUB,
    maturity=Maturity.EXPERIMENTAL,
)

_repository_push_protection_disabled = Fact(
    id="github_repository_push_protection_disabled",
    name="Repositories without secret scanning push protection",
    description=(
        "Unarchived repositories where GitHub reports push protection as disabled, "
        "so pushes containing supported secrets are not blocked. Repositories whose "
        "settings are not visible to the credential are not evaluated."
    ),
    cypher_query="""
    MATCH (n:GitHubRepository)
    WHERE n.secret_scanning_push_protection_enabled = false
        AND coalesce(n.archived, false) = false
    RETURN n.fullname AS asset_name, n.id AS asset_id,
        split(n.fullname, '/')[0] AS organization,
        'repository_push_protection_disabled' AS issue,
        n.visibility AS current_value
    """,
    cypher_visual_query="""
    MATCH (n:GitHubRepository)
    WHERE n.secret_scanning_push_protection_enabled = false
        AND coalesce(n.archived, false) = false
    RETURN n
    """,
    cypher_count_query="""
    MATCH (n:GitHubRepository)
    WHERE n.secret_scanning_push_protection_enabled IS NOT NULL
        AND coalesce(n.archived, false) = false
    RETURN count(n) AS count
    """,
    asset_label="GitHubRepository",
    asset_id_field="asset_id",
    identity_fields=("asset_id", "issue"),
    module=Module.GITHUB,
    maturity=Maturity.EXPERIMENTAL,
)

github_secret_scanning_disabled = Rule(
    id="github_secret_scanning_disabled",
    name="GitHub Repositories Without Secret Protection",
    description=(
        "Finds unarchived GitHub repositories where secret scanning or push "
        "protection is disabled. GitHub only reports these settings to repository "
        "administrators, organization owners and security managers, so a check whose "
        "evaluated count is zero had no data to test."
    ),
    output_model=GitHubSecurityConfigurationOutput,
    facts=(
        _repository_secret_scanning_disabled,
        _repository_push_protection_disabled,
    ),
    tags=("github", "secrets", "supply_chain", "stride:information_disclosure"),
    version="0.1.0",
    references=[
        RuleReference(
            text="About secret scanning",
            url="https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning",
        ),
        RuleReference(
            text="About push protection",
            url="https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection",
        ),
    ],
)


# Organization security settings

_two_factor_not_required = _organization_setting_fact(
    issue="two_factor_not_required",
    name="Organizations that do not require two-factor authentication",
    description=(
        "Organizations that let members, outside collaborators and billing managers "
        "use the organization without two-factor authentication."
    ),
    condition="n.two_factor_requirement_enabled = false",
    evaluated="n.two_factor_requirement_enabled IS NOT NULL",
    current_value="'Two-factor authentication not required'",
)

_base_permission_write = _organization_setting_fact(
    issue="base_permission_write",
    name="Organizations granting members write access to every repository",
    description=(
        "Organizations whose base repository permission is `write` or `admin`, so "
        "every member can push to, or administer, every repository."
    ),
    condition="n.default_repository_permission IN ['write', 'admin']",
    evaluated="n.default_repository_permission IS NOT NULL",
    current_value="n.default_repository_permission",
)

_members_can_create_public_repositories = _organization_setting_fact(
    issue="members_can_create_public_repositories",
    name="Organizations where members can create public repositories",
    description=(
        "Organizations that let members create public repositories, which can expose "
        "internal code without an owner's review."
    ),
    condition="n.members_can_create_public_repositories = true",
    evaluated="n.members_can_create_public_repositories IS NOT NULL",
    current_value="'Members can create public repositories'",
)

_members_can_fork_private_repositories = _organization_setting_fact(
    issue="members_can_fork_private_repositories",
    name="Organizations where members can fork private repositories",
    description=(
        "Organizations that let members fork private and internal repositories, "
        "which copies code into forks the organization does not manage."
    ),
    condition="n.members_can_fork_private_repositories = true",
    evaluated="n.members_can_fork_private_repositories IS NOT NULL",
    current_value="'Members can fork private repositories'",
)

_no_verified_domain = _organization_setting_fact(
    issue="no_verified_domain",
    name="Organizations without a verified domain",
    description=(
        "Organizations with no verified domain. A verified domain proves ownership "
        "on the organization profile and is needed to restrict email notifications "
        "to company addresses."
    ),
    condition="n.verified_domain_count = 0",
    evaluated="n.verified_domain_count IS NOT NULL",
    current_value="'No verified domains'",
)

_notifications_not_restricted = _organization_setting_fact(
    issue="notifications_not_restricted",
    name="Organizations that send notifications to unverified email domains",
    description=(
        "Organizations that do not restrict email notifications to verified or "
        "approved domains, so repository content can be emailed to personal "
        "addresses."
    ),
    condition="n.notification_delivery_restricted = false",
    evaluated="n.notification_delivery_restricted IS NOT NULL",
    current_value="'Notifications not restricted to verified domains'",
)

_copilot_public_code_suggestions = _organization_setting_fact(
    issue="copilot_public_code_suggestions",
    name="Organizations allowing Copilot suggestions that match public code",
    description=(
        "Organizations whose Copilot policy allows suggestions that match public "
        "code, which can bring code with incompatible licenses into repositories."
    ),
    condition="n.copilot_public_code_suggestions = 'allow'",
    evaluated="n.copilot_public_code_suggestions IS NOT NULL",
    current_value="n.copilot_public_code_suggestions",
)

github_organization_security_settings = Rule(
    id="github_organization_security_settings",
    name="GitHub Organization Security Settings",
    description=(
        "Reviews GitHub organization settings: two-factor enforcement, base "
        "repository permission, public repository creation, private forking, "
        "verified domains, notification restriction and the Copilot public code "
        "policy. Most settings are only visible to organization owners; a check "
        "whose evaluated count is zero had no data to test."
    ),
    output_model=GitHubSecurityConfigurationOutput,
    facts=(
        _two_factor_not_required,
        _base_permission_write,
        _members_can_create_public_repositories,
        _members_can_fork_private_repositories,
        _no_verified_domain,
        _notifications_not_restricted,
        _copilot_public_code_suggestions,
    ),
    tags=(
        "github",
        "identity",
        "access_control",
        "configuration",
        "stride:spoofing",
        "stride:elevation_of_privilege",
    ),
    version="0.1.0",
    references=[
        RuleReference(
            text="Requiring two-factor authentication in your organization",
            url="https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-two-factor-authentication-for-your-organization/requiring-two-factor-authentication-in-your-organization",
        ),
        RuleReference(
            text="Setting base permissions for an organization",
            url="https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/setting-base-permissions-for-an-organization",
        ),
        RuleReference(
            text="Restricting repository creation in your organization",
            url="https://docs.github.com/en/organizations/managing-organization-settings/restricting-repository-creation-in-your-organization",
        ),
        RuleReference(
            text="Verifying or approving a domain for your organization",
            url="https://docs.github.com/en/organizations/managing-organization-settings/verifying-or-approving-a-domain-for-your-organization",
        ),
        RuleReference(
            text="Managing policies for Copilot in your organization",
            url="https://docs.github.com/en/copilot/managing-copilot/managing-github-copilot-in-your-organization/managing-policies-for-copilot-in-your-organization",
        ),
    ],
)


# Actions policy

_actions_all_actions_allowed = _organization_setting_fact(
    issue="actions_all_actions_allowed",
    name="Organizations allowing any GitHub Action",
    description=(
        "Organizations with Actions enabled that allow workflows to use any action "
        "or reusable workflow, instead of an allowlist."
    ),
    condition=(
        "n.actions_allowed_actions = 'all' "
        "AND coalesce(n.actions_enabled_repositories, '') <> 'none'"
    ),
    evaluated="n.actions_allowed_actions IS NOT NULL",
    current_value="n.actions_allowed_actions",
)

_actions_default_token_write = _organization_setting_fact(
    issue="actions_default_token_write",
    name="Organizations granting workflows a write GITHUB_TOKEN by default",
    description=(
        "Organizations whose default `GITHUB_TOKEN` permission is read and write, so "
        "any workflow that does not declare permissions can modify repository "
        "contents."
    ),
    condition="n.actions_default_workflow_permissions = 'write'",
    evaluated="n.actions_default_workflow_permissions IS NOT NULL",
    current_value="n.actions_default_workflow_permissions",
)

_actions_can_approve_pull_requests = _organization_setting_fact(
    issue="actions_can_approve_pull_requests",
    name="Organizations letting workflows approve pull requests",
    description=(
        "Organizations that let GitHub Actions create or approve pull requests, "
        "which lets a workflow satisfy required reviews."
    ),
    condition="n.actions_can_approve_pull_request_reviews = true",
    evaluated="n.actions_can_approve_pull_request_reviews IS NOT NULL",
    current_value="'Workflows can approve pull requests'",
)

github_actions_permissive_policy = Rule(
    id="github_actions_permissive_policy",
    name="GitHub Actions Permissive Organization Policy",
    description=(
        "Reviews the GitHub Actions organization policy: unrestricted third-party "
        "actions, a write `GITHUB_TOKEN` by default, and workflows that can approve "
        "pull requests. These settings are only visible with organization "
        "Administration read access."
    ),
    output_model=GitHubSecurityConfigurationOutput,
    facts=(
        _actions_all_actions_allowed,
        _actions_default_token_write,
        _actions_can_approve_pull_requests,
    ),
    tags=(
        "github",
        "supply_chain",
        "configuration",
        "stride:tampering",
        "stride:elevation_of_privilege",
    ),
    version="0.1.0",
    references=[
        RuleReference(
            text="Disabling or limiting GitHub Actions for your organization",
            url="https://docs.github.com/en/organizations/managing-organization-settings/disabling-or-limiting-github-actions-for-your-organization",
        ),
        RuleReference(
            text="Security hardening for GitHub Actions",
            url="https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions",
        ),
    ],
)


# GitHub Apps

# Write access to any of these lets an App change code, CI, credentials, access or
# event delivery for the repositories or organization it is installed on.
_SENSITIVE_APP_PERMISSIONS = (
    "administration",
    "contents",
    "members",
    "organization_administration",
    "organization_custom_roles",
    "organization_hooks",
    "organization_personal_access_tokens",
    "organization_secrets",
    "organization_self_hosted_runners",
    "repository_hooks",
    "secrets",
    "workflows",
)
_SENSITIVE_APP_PERMISSIONS_CYPHER = (
    "[" + ", ".join(f"'{name}'" for name in _SENSITIVE_APP_PERMISSIONS) + "]"
)

_app_sensitive_write_permissions = Fact(
    id="github_app_installation_sensitive_write_permissions",
    name="GitHub Apps with write access to code, CI, secrets or administration",
    description=(
        "Active GitHub App installations granted write or admin access to "
        "repository contents, workflows, secrets, webhooks, self-hosted runners, "
        "members or administration. `current_value` lists the matching permissions; "
        "`repository_selection` of `all` means every repository is in scope."
    ),
    cypher_query=f"""
    MATCH (o:GitHubOrganization)-[:RESOURCE]->(n:GitHubAppInstallation)
    WHERE n.enabled = true
    WITH o, n, [p IN n.write_permissions WHERE p IN {_SENSITIVE_APP_PERMISSIONS_CYPHER}] AS sensitive
    WHERE size(sensitive) > 0
    RETURN n.app_slug AS asset_name, n.id AS asset_id, o.username AS organization,
        'app_sensitive_write_permissions' AS issue,
        reduce(joined = head(sensitive), p IN tail(sensitive) | joined + ', ' + p) AS current_value,
        n.repository_selection AS repository_selection
    """,
    cypher_visual_query=f"""
    MATCH (o:GitHubOrganization)-[:RESOURCE]->(n:GitHubAppInstallation)
    WHERE n.enabled = true
        AND any(p IN n.write_permissions WHERE p IN {_SENSITIVE_APP_PERMISSIONS_CYPHER})
    RETURN o, n
    """,
    cypher_count_query="""
    MATCH (n:GitHubAppInstallation)
    WHERE n.enabled = true AND n.write_permissions IS NOT NULL
    RETURN count(n) AS count
    """,
    asset_label="GitHubAppInstallation",
    asset_id_field="asset_id",
    identity_fields=("asset_id", "issue"),
    module=Module.GITHUB,
    maturity=Maturity.EXPERIMENTAL,
)

github_app_sensitive_permissions = Rule(
    id="github_app_sensitive_permissions",
    name="GitHub Apps With Sensitive Write Permissions",
    description=(
        "Finds active GitHub App installations that can change code, CI workflows, "
        "secrets, webhooks, runners, membership or organization administration. "
        "Review each App's need for that access and limit it to selected "
        "repositories where possible. Requires organization owner access to list "
        "installations."
    ),
    output_model=GitHubSecurityConfigurationOutput,
    facts=(_app_sensitive_write_permissions,),
    tags=(
        "github",
        "supply_chain",
        "privileged_access",
        "stride:elevation_of_privilege",
    ),
    version="0.1.0",
    references=[
        RuleReference(
            text="Reviewing GitHub Apps installed in your organization",
            url="https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/reviewing-github-apps-installed-in-your-organization",
        ),
        RuleReference(
            text="Choosing permissions for a GitHub App",
            url="https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app",
        ),
    ],
)


# Webhooks

_WEBHOOK_RETURN = """
    RETURN coalesce(n.target_host, toString(n.hook_id)) AS asset_name, n.id AS asset_id,
        o.username AS organization, '{issue}' AS issue,
        n.scope + ' webhook to ' + coalesce(n.target_scheme + '://' + n.target_host, 'unknown target') AS current_value
"""


def _webhook_fact(
    issue: str,
    name: str,
    description: str,
    condition: str,
    evaluated: str,
) -> Fact:
    return Fact(
        id=f"github_webhook_{issue}",
        name=name,
        description=description,
        cypher_query=f"""
        MATCH (o:GitHubOrganization)-[:RESOURCE]->(n:GitHubWebhook)
        WHERE n.active = true AND {condition}
        {_WEBHOOK_RETURN.format(issue=issue)}
        """,
        cypher_visual_query=f"""
        MATCH (o:GitHubOrganization)-[:RESOURCE]->(n:GitHubWebhook)
        WHERE n.active = true AND {condition}
        OPTIONAL MATCH (owner)-[:HAS_WEBHOOK]->(n)
        RETURN n, owner
        """,
        cypher_count_query=f"""
        MATCH (n:GitHubWebhook)
        WHERE n.active = true AND {evaluated}
        RETURN count(n) AS count
        """,
        asset_label="GitHubWebhook",
        asset_id_field="asset_id",
        identity_fields=("asset_id", "issue"),
        module=Module.GITHUB,
        maturity=Maturity.EXPERIMENTAL,
    )


_webhook_without_secret = _webhook_fact(
    issue="without_secret",
    name="Webhooks without a signing secret",
    description=(
        "Active webhooks without a secret, so the receiver cannot verify that "
        "payloads came from GitHub."
    ),
    condition="n.has_secret = false",
    evaluated="n.has_secret IS NOT NULL",
)

_webhook_insecure_ssl = _webhook_fact(
    issue="insecure_ssl",
    name="Webhooks with TLS certificate verification disabled",
    description=(
        "Active webhooks that skip TLS certificate verification, so payloads can be "
        "intercepted by anyone able to present a certificate for the target."
    ),
    condition="n.insecure_ssl = true",
    evaluated="n.insecure_ssl IS NOT NULL",
)

_webhook_not_https = _webhook_fact(
    issue="not_https",
    name="Webhooks delivering over plain HTTP",
    description="Active webhooks that send payloads to a non-HTTPS URL.",
    condition="n.uses_https = false",
    evaluated="n.uses_https IS NOT NULL",
)

github_webhook_insecure_delivery = Rule(
    id="github_webhook_insecure_delivery",
    name="GitHub Webhooks With Insecure Delivery",
    description=(
        "Finds active organization and repository webhooks that deliver without a "
        "signing secret, without TLS certificate verification or over plain HTTP. "
        "Webhook payloads can include repository content and metadata."
    ),
    output_model=GitHubSecurityConfigurationOutput,
    facts=(_webhook_without_secret, _webhook_insecure_ssl, _webhook_not_https),
    tags=(
        "github",
        "transport_security",
        "stride:information_disclosure",
        "stride:tampering",
    ),
    version="0.1.0",
    references=[
        RuleReference(
            text="Best practices for using webhooks",
            url="https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks",
        ),
        RuleReference(
            text="Validating webhook deliveries",
            url="https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries",
        ),
    ],
)
