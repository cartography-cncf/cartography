"""LangSmith security detection rules.

LangSmith holds an organization's LLM traces, which carry prompts, tool inputs and
outputs, and often personal data, and it runs agent code that can act for users. These
rules cover the credentials that reach it, who it lets in, and the paths by which its data
leaves. Each maps onto the provider-neutral ISO 27001 Annex A and SOC 2 frameworks.
"""

from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.soc2 import soc2_tsc
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# ---------------------------------------------------------------------------
# API keys that never expire
# ---------------------------------------------------------------------------
_api_key_never_expires = Fact(
    id="langsmith_api_key_never_expires",
    name="LangSmith API Keys Without Expiry",
    description=(
        "Unrevoked LangSmith personal access tokens, service keys, tracing keys and "
        "workspace keys with no expiry. A leaked key grants access until someone "
        "notices and revokes it."
    ),
    cypher_query="""
    MATCH (k:LangSmithApiKey)
    WHERE k.expires_at IS NULL
      AND k.revoked_at IS NULL
      AND NOT k.key_type IN ['scim_token', 'legacy_key']
    OPTIONAL MATCH (k)-[:OWNED_BY]->(u:LangSmithUser)
    WITH k, collect(u.email)[0] AS owner_email
    RETURN
        k.id AS id,
        coalesce(k.name, k.short_key) AS name,
        k.key_type AS key_type,
        k.access_scope AS access_scope,
        k.last_used_at AS last_used_at,
        owner_email
    """,
    cypher_visual_query="""
    MATCH (k:LangSmithApiKey)
    WHERE k.expires_at IS NULL
      AND k.revoked_at IS NULL
      AND NOT k.key_type IN ['scim_token', 'legacy_key']
    OPTIONAL MATCH p=(k)-[:OWNED_BY]->(:LangSmithUser)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (k:LangSmithApiKey)
    WHERE k.revoked_at IS NULL AND NOT k.key_type IN ['scim_token', 'legacy_key']
    RETURN COUNT(k) AS count
    """,
    asset_label="LangSmithApiKey",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.LANGSMITH,
    maturity=Maturity.EXPERIMENTAL,
)


class LangSmithApiKeyOutput(Finding):
    id: str | None = None
    name: str | None = None
    key_type: str | None = None
    access_scope: str | None = None
    last_used_at: str | None = None
    owner_email: str | None = None


langsmith_api_key_never_expires = Rule(
    id="langsmith_api_key_never_expires",
    name="LangSmith API Keys Without Expiry",
    description="Detects LangSmith API keys that never expire.",
    output_model=LangSmithApiKeyOutput,
    facts=(_api_key_never_expires,),
    tags=("identity", "credentials", "ai", "stride:elevation_of_privilege"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("5.17"),
        soc2_tsc("CC6.1"),
    ),
)


# ---------------------------------------------------------------------------
# Unused API keys and SCIM tokens
# ---------------------------------------------------------------------------
_api_key_unused = Fact(
    id="langsmith_api_key_unused",
    name="Unused LangSmith API Keys",
    description=(
        "Live LangSmith keys and SCIM tokens unused for 90 days, or never used 30 days "
        "after creation. A SCIM token can provision organization administrators."
    ),
    cypher_query="""
    MATCH (k:LangSmithApiKey)
    WHERE k.revoked_at IS NULL
      AND k.key_type <> 'legacy_key'
      AND (k.expires_at IS NULL OR datetime(k.expires_at) > datetime())
      AND (
        (k.last_used_at IS NULL
         AND datetime(k.created_at) < datetime() - duration('P30D'))
        OR datetime(k.last_used_at) < datetime() - duration('P90D')
      )
    OPTIONAL MATCH (k)-[:OWNED_BY]->(u:LangSmithUser)
    WITH k, collect(u.email)[0] AS owner_email
    RETURN
        k.id AS id,
        coalesce(k.name, k.short_key) AS name,
        k.key_type AS key_type,
        k.access_scope AS access_scope,
        k.last_used_at AS last_used_at,
        owner_email
    """,
    cypher_visual_query="""
    MATCH (k:LangSmithApiKey)
    WHERE k.revoked_at IS NULL
      AND k.key_type <> 'legacy_key'
      AND (k.expires_at IS NULL OR datetime(k.expires_at) > datetime())
      AND (
        (k.last_used_at IS NULL
         AND datetime(k.created_at) < datetime() - duration('P30D'))
        OR datetime(k.last_used_at) < datetime() - duration('P90D')
      )
    OPTIONAL MATCH p=(k)-[:OWNED_BY]->(:LangSmithUser)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (k:LangSmithApiKey)
    WHERE k.revoked_at IS NULL
      AND k.key_type <> 'legacy_key'
      AND (k.expires_at IS NULL OR datetime(k.expires_at) > datetime())
    RETURN COUNT(k) AS count
    """,
    asset_label="LangSmithApiKey",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.LANGSMITH,
    maturity=Maturity.EXPERIMENTAL,
)

langsmith_api_key_unused = Rule(
    id="langsmith_api_key_unused",
    name="Unused LangSmith API Keys",
    description="Detects live LangSmith keys and SCIM tokens nobody uses.",
    output_model=LangSmithApiKeyOutput,
    facts=(_api_key_unused,),
    tags=("identity", "credentials", "ai", "stride:spoofing"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("5.18"),
        soc2_tsc("CC6.2"),
    ),
)


# ---------------------------------------------------------------------------
# Organizations that don't cap key lifetimes
# ---------------------------------------------------------------------------
_key_lifetime_uncapped = Fact(
    id="langsmith_key_lifetime_uncapped",
    name="LangSmith Organizations Without a Key Lifetime Cap",
    description=(
        "LangSmith organizations that set no maximum lifetime for personal access "
        "tokens, service keys or API keys, so members can create keys that never "
        "expire. Plans without the setting also report no cap."
    ),
    cypher_query="""
    MATCH (o:LangSmithOrganization)
    WHERE NOT coalesce(o.is_personal, false)
    WITH o, [kind IN [
        CASE WHEN o.max_pat_expiry_days IS NULL
              AND NOT coalesce(o.pat_creation_disabled, false)
             THEN 'personal_access_token' END,
        CASE WHEN o.max_service_key_expiry_days IS NULL THEN 'service_key' END,
        CASE WHEN o.max_api_key_expiry_days IS NULL THEN 'api_key' END
    ] WHERE kind IS NOT NULL] AS uncapped
    WHERE size(uncapped) > 0
    RETURN o.id AS id, o.name AS name, uncapped AS uncapped_key_types
    """,
    cypher_visual_query="""
    MATCH (o:LangSmithOrganization)
    WHERE NOT coalesce(o.is_personal, false)
      AND (
        (o.max_pat_expiry_days IS NULL AND NOT coalesce(o.pat_creation_disabled, false))
        OR o.max_service_key_expiry_days IS NULL
        OR o.max_api_key_expiry_days IS NULL
      )
    RETURN o
    """,
    cypher_count_query="""
    MATCH (o:LangSmithOrganization)
    WHERE NOT coalesce(o.is_personal, false)
    RETURN COUNT(o) AS count
    """,
    asset_label="LangSmithOrganization",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.LANGSMITH,
    maturity=Maturity.EXPERIMENTAL,
)


class LangSmithKeyLifetimeOutput(Finding):
    id: str | None = None
    name: str | None = None
    uncapped_key_types: list[str] | None = None


langsmith_key_lifetime_uncapped = Rule(
    id="langsmith_key_lifetime_uncapped",
    name="LangSmith Organizations Without a Key Lifetime Cap",
    description="Detects LangSmith organizations that let keys live forever.",
    output_model=LangSmithKeyLifetimeOutput,
    facts=(_key_lifetime_uncapped,),
    tags=("identity", "credentials", "ai", "stride:elevation_of_privilege"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("5.17"),
        soc2_tsc("CC6.1"),
    ),
)


# ---------------------------------------------------------------------------
# SSO configured but not enforced
# ---------------------------------------------------------------------------
_sso_not_enforced = Fact(
    id="langsmith_sso_not_enforced",
    name="LangSmith Organizations Not Enforcing SSO",
    description=(
        "LangSmith organizations with SAML SSO configured that still accept password "
        "and social logins, which bypass the identity provider's MFA and offboarding."
    ),
    cypher_query="""
    MATCH (o:LangSmithOrganization)-[:RESOURCE]->(s:LangSmithSSOProvider)
    WHERE NOT coalesce(o.sso_only, false)
    RETURN o.id AS id, o.name AS name, collect(s.name) AS sso_providers
    """,
    cypher_visual_query="""
    MATCH p=(o:LangSmithOrganization)-[:RESOURCE]->(:LangSmithSSOProvider)
    WHERE NOT coalesce(o.sso_only, false)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (o:LangSmithOrganization)-[:RESOURCE]->(:LangSmithSSOProvider)
    RETURN COUNT(DISTINCT o) AS count
    """,
    asset_label="LangSmithOrganization",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.LANGSMITH,
    maturity=Maturity.EXPERIMENTAL,
)


class LangSmithSsoNotEnforcedOutput(Finding):
    id: str | None = None
    name: str | None = None
    sso_providers: list[str] | None = None


langsmith_sso_not_enforced = Rule(
    id="langsmith_sso_not_enforced",
    name="LangSmith Organizations Not Enforcing SSO",
    description="Detects LangSmith organizations where SSO is optional.",
    output_model=LangSmithSsoNotEnforcedOutput,
    facts=(_sso_not_enforced,),
    tags=("identity", "authentication", "ai", "stride:spoofing"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.5"),
        soc2_tsc("CC6.1"),
    ),
)


# ---------------------------------------------------------------------------
# Just-in-time provisioning grants write access by default
# ---------------------------------------------------------------------------
_SSO_DEFAULT_ROLE_RISKY_PERMISSIONS = (
    "['deployments:create', 'deployments:update', 'workspaces:manage-members', "
    "'workspaces:manage-keys', 'workspaces:manage-secrets', 'rules:create', "
    "'bulk-exports:manage']"
)

_sso_default_role_can_deploy = Fact(
    id="langsmith_sso_default_role_can_deploy",
    name="LangSmith SSO Default Role With Deploy or Admin Permissions",
    description=(
        "LangSmith SSO settings whose just-in-time provisioning gives every new user a "
        "role that can deploy code, manage members, keys or secrets, or send data out "
        "through automations and bulk exports. Deployed code runs with the workspace's "
        "secrets."
    ),
    cypher_query=f"""
    MATCH (o:LangSmithOrganization)-[:RESOURCE]->(s:LangSmithSSOProvider)
          -[:DEFAULT_ROLE]->(r:LangSmithRole)-[:GRANTS]->(p:LangSmithPermission)
    WHERE o.jit_provisioning_enabled = true
      AND p.name IN {_SSO_DEFAULT_ROLE_RISKY_PERMISSIONS}
    WITH s, collect(DISTINCT r.name) AS default_roles,
         collect(DISTINCT p.name) AS permissions
    OPTIONAL MATCH (s)-[:PROVISIONS_INTO]->(w:LangSmithWorkspace)
    RETURN
        s.id AS id,
        s.name AS name,
        default_roles,
        permissions,
        collect(DISTINCT w.name) AS workspaces
    """,
    cypher_visual_query=f"""
    MATCH p=(o:LangSmithOrganization)-[:RESOURCE]->(s:LangSmithSSOProvider)
          -[:DEFAULT_ROLE]->(:LangSmithRole)-[:GRANTS]->(perm:LangSmithPermission)
    WHERE o.jit_provisioning_enabled = true
      AND perm.name IN {_SSO_DEFAULT_ROLE_RISKY_PERMISSIONS}
    OPTIONAL MATCH w=(s)-[:PROVISIONS_INTO]->(:LangSmithWorkspace)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (:LangSmithOrganization)-[:RESOURCE]->(s:LangSmithSSOProvider)
    RETURN COUNT(s) AS count
    """,
    asset_label="LangSmithSSOProvider",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.LANGSMITH,
    maturity=Maturity.EXPERIMENTAL,
)


class LangSmithSsoDefaultRoleOutput(Finding):
    id: str | None = None
    name: str | None = None
    default_roles: list[str] | None = None
    permissions: list[str] | None = None
    workspaces: list[str] | None = None


langsmith_sso_default_role_can_deploy = Rule(
    id="langsmith_sso_default_role_can_deploy",
    name="LangSmith SSO Default Role With Deploy or Admin Permissions",
    description=(
        "Detects LangSmith just-in-time provisioning that hands every new user "
        "deploy or admin permissions."
    ),
    output_model=LangSmithSsoDefaultRoleOutput,
    facts=(_sso_default_role_can_deploy,),
    tags=("identity", "least_privilege", "ai", "stride:elevation_of_privilege"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("5.15"),
        soc2_tsc("CC6.3"),
    ),
)


# ---------------------------------------------------------------------------
# Public share links and public repos
# ---------------------------------------------------------------------------
_public_share = Fact(
    id="langsmith_public_share",
    name="LangSmith Data Readable Without an Account",
    description=(
        "Runs, datasets, threads, and prompt or agent repos that anyone with the link "
        "can read without a LangSmith account, in organizations that allow public "
        "sharing. Traces hold prompts, tool inputs and outputs, and often personal data; "
        "a shared dataset also exposes its experiments."
    ),
    cypher_query="""
    MATCH (o:LangSmithOrganization)-[:RESOURCE]->(w:LangSmithWorkspace)
          -[:RESOURCE]->(s:LangSmithPublicShare)
    WHERE NOT coalesce(o.public_sharing_disabled, false)
    RETURN
        s.id AS id,
        coalesce(s.entity_name, s.entity_id) AS name,
        s.share_type AS share_type,
        w.name AS workspace,
        s.project_name AS project,
        s.created_at AS shared_at
    """,
    cypher_visual_query="""
    MATCH p=(o:LangSmithOrganization)-[:RESOURCE]->(:LangSmithWorkspace)
          -[:RESOURCE]->(:LangSmithPublicShare)
    WHERE NOT coalesce(o.public_sharing_disabled, false)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (s:LangSmithPublicShare)
    RETURN COUNT(s) AS count
    """,
    asset_label="LangSmithPublicShare",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.LANGSMITH,
    maturity=Maturity.EXPERIMENTAL,
)


class LangSmithPublicShareOutput(Finding):
    id: str | None = None
    name: str | None = None
    share_type: str | None = None
    workspace: str | None = None
    project: str | None = None
    shared_at: str | None = None


langsmith_public_share = Rule(
    id="langsmith_public_share",
    name="LangSmith Data Readable Without an Account",
    description="Detects LangSmith traces, datasets and repos shared publicly.",
    output_model=LangSmithPublicShareOutput,
    facts=(_public_share,),
    tags=("data_exposure", "attack_surface", "ai", "stride:information_disclosure"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.12"),
        soc2_tsc("CC6.7"),
    ),
)


# ---------------------------------------------------------------------------
# Deployments any LangSmith user can open
# ---------------------------------------------------------------------------
_shareable_deployment = Fact(
    id="langsmith_shareable_deployment",
    name="LangSmith Deployments Shared Outside the Organization",
    description=(
        "LangSmith deployments marked shareable, which any LangSmith user in any "
        "organization can open and run in Studio."
    ),
    cypher_query="""
    MATCH (w:LangSmithWorkspace)-[:RESOURCE]->(d:LangSmithDeployment)
    WHERE d.shareable = true
    RETURN
        d.id AS id,
        coalesce(d.display_name, d.name) AS name,
        d.url AS url,
        d.status AS status,
        w.name AS workspace
    """,
    cypher_visual_query="""
    MATCH p=(:LangSmithWorkspace)-[:RESOURCE]->(d:LangSmithDeployment)
    WHERE d.shareable = true
    OPTIONAL MATCH a=(d)-[:RUNS]->(:LangSmithAgent)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (d:LangSmithDeployment)
    RETURN COUNT(d) AS count
    """,
    asset_label="LangSmithDeployment",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.LANGSMITH,
    maturity=Maturity.EXPERIMENTAL,
)


class LangSmithDeploymentOutput(Finding):
    id: str | None = None
    name: str | None = None
    url: str | None = None
    status: str | None = None
    workspace: str | None = None


langsmith_shareable_deployment = Rule(
    id="langsmith_shareable_deployment",
    name="LangSmith Deployments Shared Outside the Organization",
    description="Detects LangSmith deployments any LangSmith user can run.",
    output_model=LangSmithDeploymentOutput,
    facts=(_shareable_deployment,),
    tags=("attack_surface", "ai", "stride:elevation_of_privilege"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("5.15"),
        soc2_tsc("CC6.6"),
    ),
)


# ---------------------------------------------------------------------------
# Static cloud credentials in deployment environments
# ---------------------------------------------------------------------------
_STATIC_CREDENTIAL_PATTERN = (
    "(?i).*(AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID|PRIVATE_KEY|"
    "GOOGLE_APPLICATION_CREDENTIALS|SERVICE_ACCOUNT_KEY|AZURE_CLIENT_SECRET).*"
)

_deployment_static_cloud_credentials = Fact(
    id="langsmith_deployment_static_cloud_credentials",
    name="LangSmith Deployments Holding Static Cloud Credentials",
    description=(
        "LangSmith deployments whose environment holds long-lived cloud credentials, "
        "such as AWS access keys or service account private keys, judged by secret "
        "name. Anyone who can update the deployment's code can read them, and they "
        "outlive the deployment unless rotated."
    ),
    cypher_query=f"""
    MATCH (w:LangSmithWorkspace)-[:RESOURCE]->(d:LangSmithDeployment)
    WITH w, d, [name IN coalesce(d.secret_names, [])
                WHERE name =~ '{_STATIC_CREDENTIAL_PATTERN}'] AS credentials
    WHERE size(credentials) > 0
    RETURN
        d.id AS id,
        coalesce(d.display_name, d.name) AS name,
        credentials AS secret_names,
        w.name AS workspace
    """,
    cypher_visual_query=f"""
    MATCH p=(:LangSmithWorkspace)-[:RESOURCE]->(d:LangSmithDeployment)
    WHERE any(name IN coalesce(d.secret_names, [])
              WHERE name =~ '{_STATIC_CREDENTIAL_PATTERN}')
    RETURN *
    """,
    cypher_count_query="""
    MATCH (d:LangSmithDeployment)
    RETURN COUNT(d) AS count
    """,
    asset_label="LangSmithDeployment",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.LANGSMITH,
    maturity=Maturity.EXPERIMENTAL,
)


class LangSmithDeploymentCredentialsOutput(Finding):
    id: str | None = None
    name: str | None = None
    secret_names: list[str] | None = None
    workspace: str | None = None


langsmith_deployment_static_cloud_credentials = Rule(
    id="langsmith_deployment_static_cloud_credentials",
    name="LangSmith Deployments Holding Static Cloud Credentials",
    description=(
        "Detects LangSmith deployments configured with long-lived cloud credentials."
    ),
    output_model=LangSmithDeploymentCredentialsOutput,
    facts=(_deployment_static_cloud_credentials,),
    tags=("credentials", "secrets", "ai", "stride:information_disclosure"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("5.17"),
        soc2_tsc("CC6.1"),
    ),
)


# ---------------------------------------------------------------------------
# Webhooks over plaintext HTTP
# ---------------------------------------------------------------------------
_webhook_plaintext = Fact(
    id="langsmith_webhook_plaintext",
    name="LangSmith Webhooks Over Plaintext HTTP",
    description=(
        "Enabled LangSmith webhooks that deliver runs or prompts over http, so trace "
        "contents and any auth headers cross the network unencrypted."
    ),
    cypher_query="""
    MATCH (w:LangSmithWorkspace)-[:RESOURCE]->(h:LangSmithWebhook)
    WHERE h.scheme = 'http' AND coalesce(h.enabled, true)
    RETURN
        h.id AS id,
        coalesce(h.rule_name, h.host) AS name,
        h.source AS sender,
        h.host AS host,
        w.name AS workspace
    """,
    cypher_visual_query="""
    MATCH p=(:LangSmithWorkspace)-[:RESOURCE]->(h:LangSmithWebhook)
    WHERE h.scheme = 'http' AND coalesce(h.enabled, true)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (h:LangSmithWebhook)
    RETURN COUNT(h) AS count
    """,
    asset_label="LangSmithWebhook",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.LANGSMITH,
    maturity=Maturity.EXPERIMENTAL,
)


class LangSmithWebhookOutput(Finding):
    id: str | None = None
    name: str | None = None
    sender: str | None = None
    host: str | None = None
    workspace: str | None = None


langsmith_webhook_plaintext = Rule(
    id="langsmith_webhook_plaintext",
    name="LangSmith Webhooks Over Plaintext HTTP",
    description="Detects LangSmith webhooks that send data unencrypted.",
    output_model=LangSmithWebhookOutput,
    facts=(_webhook_plaintext,),
    tags=("network", "data_exposure", "ai", "stride:information_disclosure"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.24"),
        soc2_tsc("CC6.7"),
    ),
)


# ---------------------------------------------------------------------------
# OAuth clients with insecure redirect URIs
# ---------------------------------------------------------------------------
_oauth_client_insecure_redirect = Fact(
    id="langsmith_oauth_client_insecure_redirect",
    name="LangSmith OAuth Clients With Insecure Redirect URIs",
    description=(
        "Enabled OAuth clients registered against LangSmith that accept an http "
        "redirect URI. A confidential client should never redirect over http, not even "
        "to a loopback address: any local process listening there can capture the "
        "authorization code. Public clients may use http only for a loopback address."
    ),
    cypher_query="""
    MATCH (w:LangSmithWorkspace)-[:RESOURCE]->(c:LangSmithOAuthClient)
    WHERE NOT coalesce(c.disabled, false)
    WITH w, c, [uri IN coalesce(c.redirect_uris, [])
                WHERE uri STARTS WITH 'http://'
                  AND (c.client_type = 'confidential'
                       OR NOT (uri STARTS WITH 'http://localhost'
                               OR uri STARTS WITH 'http://127.0.0.1'
                               OR uri STARTS WITH 'http://[::1]'))] AS insecure
    WHERE size(insecure) > 0
    RETURN
        c.id AS id,
        c.name AS name,
        c.client_type AS client_type,
        insecure AS insecure_redirect_uris,
        w.name AS workspace
    """,
    cypher_visual_query="""
    MATCH p=(:LangSmithWorkspace)-[:RESOURCE]->(c:LangSmithOAuthClient)
    WHERE NOT coalesce(c.disabled, false)
      AND any(uri IN coalesce(c.redirect_uris, [])
              WHERE uri STARTS WITH 'http://'
                AND (c.client_type = 'confidential'
                     OR NOT (uri STARTS WITH 'http://localhost'
                             OR uri STARTS WITH 'http://127.0.0.1'
                             OR uri STARTS WITH 'http://[::1]')))
    RETURN *
    """,
    cypher_count_query="""
    MATCH (c:LangSmithOAuthClient)
    RETURN COUNT(c) AS count
    """,
    asset_label="LangSmithOAuthClient",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.LANGSMITH,
    maturity=Maturity.EXPERIMENTAL,
)


class LangSmithOAuthClientOutput(Finding):
    id: str | None = None
    name: str | None = None
    client_type: str | None = None
    insecure_redirect_uris: list[str] | None = None
    workspace: str | None = None


langsmith_oauth_client_insecure_redirect = Rule(
    id="langsmith_oauth_client_insecure_redirect",
    name="LangSmith OAuth Clients With Insecure Redirect URIs",
    description="Detects LangSmith OAuth clients whose redirects can leak codes.",
    output_model=LangSmithOAuthClientOutput,
    facts=(_oauth_client_insecure_redirect,),
    tags=("identity", "oauth", "ai", "stride:spoofing"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.5"),
        soc2_tsc("CC6.1"),
    ),
)


# ---------------------------------------------------------------------------
# Credentials that outlive a member's deactivation
# ---------------------------------------------------------------------------
_agent_credential_for_disabled_member = Fact(
    id="langsmith_agent_credential_for_disabled_member",
    name="LangSmith Agent Credentials Acting for Deactivated Members",
    description=(
        "Third-party OAuth tokens an agent holds on behalf of a member whose LangSmith "
        "membership is deactivated. Deactivation doesn't revoke them, so the agent can "
        "still act as that person in GitHub, Google and other providers."
    ),
    cypher_query="""
    MATCH (c:LangSmithAgentCredential)-[:ON_BEHALF_OF]->(u:LangSmithUser)
    WHERE EXISTS {
        (u)-[:HAS_MEMBERSHIP]->(:LangSmithOrgMembership {is_disabled: true})
    }
    OPTIONAL MATCH (a:LangSmithAgent)-[:HAS_CREDENTIAL]->(c)
    OPTIONAL MATCH (c)-[:FOR_PROVIDER]->(p:LangSmithOAuthProvider)
    WITH c,
         collect(DISTINCT coalesce(a.name, a.agent_id))[0] AS agent,
         collect(DISTINCT p.name)[0] AS provider,
         collect(DISTINCT u.email)[0] AS owner_email
    RETURN
        c.id AS id,
        agent AS name,
        'agent_credential' AS credential_type,
        provider,
        owner_email
    """,
    cypher_visual_query="""
    MATCH p=(:LangSmithAgent)-[:HAS_CREDENTIAL]->(:LangSmithAgentCredential)
          -[:ON_BEHALF_OF]->(:LangSmithUser)
          -[:HAS_MEMBERSHIP]->(:LangSmithOrgMembership {is_disabled: true})
    RETURN *
    """,
    cypher_count_query="""
    MATCH (c:LangSmithAgentCredential)
    RETURN COUNT(c) AS count
    """,
    asset_label="LangSmithAgentCredential",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.LANGSMITH,
    maturity=Maturity.EXPERIMENTAL,
)

_tracing_key_of_disabled_member = Fact(
    id="langsmith_tracing_key_of_disabled_member",
    name="LangSmith Tracing Keys of Deactivated Members",
    description=(
        "Unrevoked tracing keys created by a member whose LangSmith membership is "
        "deactivated. Tracing keys keep working after their creator leaves."
    ),
    cypher_query="""
    MATCH (k:LangSmithApiKey)-[:OWNED_BY]->(u:LangSmithUser)
    WHERE (k.key_type = 'tracing_key' OR k.is_tracing_key = true)
      AND k.revoked_at IS NULL
      AND EXISTS {
        (u)-[:HAS_MEMBERSHIP]->(:LangSmithOrgMembership {is_disabled: true})
      }
    WITH k, collect(DISTINCT u.email)[0] AS owner_email
    RETURN
        k.id AS id,
        coalesce(k.name, k.short_key) AS name,
        'tracing_key' AS credential_type,
        null AS provider,
        owner_email
    """,
    cypher_visual_query="""
    MATCH p=(k:LangSmithApiKey)-[:OWNED_BY]->(:LangSmithUser)
          -[:HAS_MEMBERSHIP]->(:LangSmithOrgMembership {is_disabled: true})
    WHERE (k.key_type = 'tracing_key' OR k.is_tracing_key = true)
      AND k.revoked_at IS NULL
    RETURN *
    """,
    cypher_count_query="""
    MATCH (k:LangSmithApiKey)
    WHERE k.key_type = 'tracing_key' OR k.is_tracing_key = true
    RETURN COUNT(k) AS count
    """,
    asset_label="LangSmithApiKey",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.LANGSMITH,
    maturity=Maturity.EXPERIMENTAL,
)


class LangSmithDisabledMemberCredentialOutput(Finding):
    id: str | None = None
    name: str | None = None
    credential_type: str | None = None
    provider: str | None = None
    owner_email: str | None = None


langsmith_disabled_member_credentials = Rule(
    id="langsmith_disabled_member_credentials",
    name="LangSmith Credentials Outliving a Member's Deactivation",
    description=(
        "Detects agent OAuth tokens and tracing keys that keep working after their "
        "member is deactivated."
    ),
    output_model=LangSmithDisabledMemberCredentialOutput,
    facts=(_agent_credential_for_disabled_member, _tracing_key_of_disabled_member),
    tags=("identity", "credentials", "ai", "stride:spoofing"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("5.18"),
        soc2_tsc("CC6.2"),
    ),
)


# ---------------------------------------------------------------------------
# Bulk exports authenticated with static cloud keys
# ---------------------------------------------------------------------------
_bulk_export_static_credentials = Fact(
    id="langsmith_bulk_export_static_credentials",
    name="LangSmith Bulk Exports Using Static Storage Keys",
    description=(
        "LangSmith bulk export destinations that write traces to object storage with a "
        "stored access key rather than an assumed IAM role. The key sits in LangSmith, "
        "usually never expires, and can typically read the bucket's earlier exports too."
    ),
    cypher_query="""
    MATCH (w:LangSmithWorkspace)-[:RESOURCE]->(d:LangSmithBulkExportDestination)
    WHERE any(field IN coalesce(d.credential_fields, [])
              WHERE field IN ['access_key_id', 'secret_access_key'])
    RETURN
        d.id AS id,
        d.name AS name,
        d.bucket_name AS bucket_name,
        d.endpoint_url AS endpoint_url,
        w.name AS workspace
    """,
    cypher_visual_query="""
    MATCH p=(:LangSmithWorkspace)-[:RESOURCE]->(d:LangSmithBulkExportDestination)
    WHERE any(field IN coalesce(d.credential_fields, [])
              WHERE field IN ['access_key_id', 'secret_access_key'])
    OPTIONAL MATCH b=(d)-[:EXPORTS_TO]->(:S3Bucket)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (d:LangSmithBulkExportDestination)
    RETURN COUNT(d) AS count
    """,
    asset_label="LangSmithBulkExportDestination",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.LANGSMITH,
    maturity=Maturity.EXPERIMENTAL,
)


class LangSmithBulkExportOutput(Finding):
    id: str | None = None
    name: str | None = None
    bucket_name: str | None = None
    endpoint_url: str | None = None
    workspace: str | None = None


langsmith_bulk_export_static_credentials = Rule(
    id="langsmith_bulk_export_static_credentials",
    name="LangSmith Bulk Exports Using Static Storage Keys",
    description=(
        "Detects LangSmith trace exports authenticated with a stored access key "
        "instead of an IAM role."
    ),
    output_model=LangSmithBulkExportOutput,
    facts=(_bulk_export_static_credentials,),
    tags=("credentials", "data_exposure", "ai", "stride:information_disclosure"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("5.17"),
        soc2_tsc("CC6.1"),
    ),
)
