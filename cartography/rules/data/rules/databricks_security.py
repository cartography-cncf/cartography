"""Databricks security detection rules.

Each rule is a single-provider (Databricks) attack-surface / misconfiguration
detection. Compliance-framework mappings are intentionally left off for now:
the Databricks control set is not yet wired into the shared frameworks, so
mapping here would create orphan scopes. TODO: map onto ISO 27001 / SOC 2 once
a Databricks framework scope exists.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# ---------------------------------------------------------------------------
# Personal access tokens that never expire
# ---------------------------------------------------------------------------
_pat_never_expires = Fact(
    id="databricks_pat_never_expires",
    name="Databricks Personal Access Tokens Without Expiry",
    description=(
        "Databricks personal access tokens with no expiry. The token API "
        "encodes an unbounded lifetime as a null expiry_time; a leaked "
        "never-expiring token grants indefinite programmatic access."
    ),
    cypher_query="""
    MATCH (t:DatabricksToken)
    WHERE t.expiry_time IS NULL
    RETURN
        t.id AS id,
        coalesce(t.comment, t.token_id) AS name,
        t.created_by_username AS created_by,
        t.creation_time AS creation_time
    """,
    cypher_visual_query="""
    MATCH p=(w:DatabricksWorkspace)-[:RESOURCE]->(t:DatabricksToken)
    WHERE t.expiry_time IS NULL
    RETURN *
    """,
    cypher_count_query="""
    MATCH (t:DatabricksToken)
    RETURN COUNT(t) AS count
    """,
    identity_fields=("id",),
    module=Module.DATABRICKS,
    maturity=Maturity.EXPERIMENTAL,
)


class DatabricksTokenNeverExpiresOutput(Finding):
    name: str | None = None
    id: str | None = None
    created_by: str | None = None
    creation_time: str | None = None


databricks_pat_never_expires = Rule(
    id="databricks_pat_never_expires",
    name="Databricks Personal Access Tokens Without Expiry",
    description=(
        "Detects Databricks personal access tokens that never expire, an "
        "indefinite credential-theft risk."
    ),
    output_model=DatabricksTokenNeverExpiresOutput,
    facts=(_pat_never_expires,),
    tags=("identity", "credentials", "stride:elevation_of_privilege"),
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Workspaces that allow tokens with an unbounded lifetime
# ---------------------------------------------------------------------------
_workspace_unbounded_token_lifetime = Fact(
    id="databricks_workspace_unbounded_token_lifetime",
    name="Databricks Workspaces Without a Token Lifetime Cap",
    description=(
        "Databricks workspaces with personal access tokens enabled but no "
        "maximum token lifetime configured, so users can mint tokens that "
        "never expire."
    ),
    cypher_query="""
    MATCH (w:DatabricksWorkspace)
    WHERE w.tokens_enabled = true
      AND w.max_token_lifetime_days IS NULL
    RETURN
        w.id AS id,
        coalesce(w.workspace_name, w.host) AS name,
        w.host AS host
    """,
    cypher_visual_query="""
    MATCH (w:DatabricksWorkspace)
    WHERE w.tokens_enabled = true
      AND w.max_token_lifetime_days IS NULL
    RETURN w
    """,
    cypher_count_query="""
    MATCH (w:DatabricksWorkspace)
    RETURN COUNT(w) AS count
    """,
    identity_fields=("id",),
    module=Module.DATABRICKS,
    maturity=Maturity.EXPERIMENTAL,
)


class DatabricksWorkspaceTokenLifetimeOutput(Finding):
    name: str | None = None
    id: str | None = None
    host: str | None = None


databricks_workspace_unbounded_token_lifetime = Rule(
    id="databricks_workspace_unbounded_token_lifetime",
    name="Databricks Workspaces Without a Token Lifetime Cap",
    description=(
        "Detects Databricks workspaces that permit personal access tokens "
        "without enforcing a maximum lifetime."
    ),
    output_model=DatabricksWorkspaceTokenLifetimeOutput,
    facts=(_workspace_unbounded_token_lifetime,),
    tags=("identity", "credentials"),
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# IP access lists that allow the entire internet
# ---------------------------------------------------------------------------
_ip_access_list_allows_all = Fact(
    id="databricks_ip_access_list_allows_all",
    name="Databricks IP Access Lists Allowing All Addresses",
    description=(
        "Enabled Databricks ALLOW-type IP access lists that include a "
        "0.0.0.0/0 or ::/0 entry, which permits access from any source "
        "address and defeats the IP allowlist control."
    ),
    cypher_query="""
    MATCH (l:DatabricksIpAccessList)
    WHERE l.enabled = true
      AND l.list_type = 'ALLOW'
      AND any(addr IN l.ip_addresses WHERE addr IN ['0.0.0.0/0', '::/0'])
    RETURN
        l.id AS id,
        l.label AS name,
        l.list_type AS list_type,
        l.ip_addresses AS ip_addresses
    """,
    cypher_visual_query="""
    MATCH p=(w:DatabricksWorkspace)-[:RESOURCE]->(l:DatabricksIpAccessList)
    WHERE l.enabled = true
      AND l.list_type = 'ALLOW'
      AND any(addr IN l.ip_addresses WHERE addr IN ['0.0.0.0/0', '::/0'])
    RETURN *
    """,
    cypher_count_query="""
    MATCH (l:DatabricksIpAccessList)
    RETURN COUNT(l) AS count
    """,
    identity_fields=("id",),
    module=Module.DATABRICKS,
    maturity=Maturity.EXPERIMENTAL,
)


class DatabricksIpAccessListAllowsAllOutput(Finding):
    name: str | None = None
    id: str | None = None
    list_type: str | None = None
    ip_addresses: list | None = None


databricks_ip_access_list_allows_all = Rule(
    id="databricks_ip_access_list_allows_all",
    name="Databricks IP Access Lists Allowing All Addresses",
    description=(
        "Detects Databricks IP access lists whose ALLOW entries include the "
        "whole internet, negating the network access control."
    ),
    output_model=DatabricksIpAccessListAllowsAllOutput,
    facts=(_ip_access_list_allows_all,),
    tags=("network", "attack_surface", "stride:spoofing"),
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Delta Sharing recipients using open bearer-token authentication
# ---------------------------------------------------------------------------
_public_delta_sharing_recipient = Fact(
    id="databricks_public_delta_sharing_recipient",
    name="Databricks Delta Sharing Recipients Using Token Authentication",
    description=(
        "Activated Delta Sharing recipients authenticated by bearer token "
        "(open sharing) rather than Databricks-to-Databricks identity "
        "federation. The activation link and token are internet-reachable, so "
        "anyone holding them can read the shared data."
    ),
    cypher_query="""
    MATCH (r:DatabricksRecipient)
    WHERE r.authentication_type = 'TOKEN'
      AND r.activated = true
    RETURN
        r.id AS id,
        r.name AS name,
        r.authentication_type AS authentication_type,
        r.cloud AS cloud,
        r.region AS region
    """,
    cypher_visual_query="""
    MATCH p=(w:DatabricksWorkspace)-[:RESOURCE]->(r:DatabricksRecipient)
    WHERE r.authentication_type = 'TOKEN'
      AND r.activated = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (r:DatabricksRecipient)
    RETURN COUNT(r) AS count
    """,
    identity_fields=("id",),
    module=Module.DATABRICKS,
    maturity=Maturity.EXPERIMENTAL,
)


class DatabricksPublicDeltaSharingRecipientOutput(Finding):
    name: str | None = None
    id: str | None = None
    authentication_type: str | None = None
    cloud: str | None = None
    region: str | None = None


databricks_public_delta_sharing_recipient = Rule(
    id="databricks_public_delta_sharing_recipient",
    name="Databricks Delta Sharing Recipients Using Token Authentication",
    description=(
        "Detects Delta Sharing recipients that use open bearer-token "
        "authentication, exposing shared data over the internet."
    ),
    output_model=DatabricksPublicDeltaSharingRecipientOutput,
    facts=(_public_delta_sharing_recipient,),
    tags=("data", "attack_surface", "stride:information_disclosure"),
    version="0.1.0",
)
