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


# Note: a "workspace without a token lifetime cap" rule was considered but
# dropped. Ingestion normalises Databricks maxTokenLifetimeDays "0"
# (system-default cap) and an unset value both to null, and the account default
# (730 days) is always a cap, so a null value cannot distinguish "truly
# unbounded" from "default cap" and the rule would misfire on every workspace
# that never set an explicit override. The never-expiring PAT rule above carries
# the real signal.


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
