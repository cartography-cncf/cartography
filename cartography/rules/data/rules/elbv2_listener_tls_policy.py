"""
ELBv2 listener TLS security policy

Three independent properties of the negotiated TLS configuration: FIPS
140 validation, post-quantum hybrid key exchange, and a modern TLS 1.2/1.3
baseline. Each is a separate policy family and a listener can satisfy one
without another, so they are separate rules rather than one severity.

Matching is by ``ssl_policy`` NAME, which is how AWS exposes the choice. The
name is the contract: it determines the ciphers, protocols and key-exchange
groups actually offered, so a name-based test is exact for what it asserts
and does not need the negotiated parameters.

No collector change is required: every property and relationship used
here is synced by the existing EC2 and WAFv2 modules. All rules are
EXPERIMENTAL until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsElbv2ListenerFipsTlsOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    listener_arn: str | None = None
    port: str | None = None
    protocol: str | None = None
    ssl_policy: str | None = None


_aws_elbv2_listener_fips_tls_fact = Fact(
    id="aws_elbv2_listener_fips_tls_fact",
    name="ELBv2 listener without FIPS TLS policy",
    description="HTTPS/TLS listeners whose ssl_policy is absent or not a FIPS policy.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(l:AWSELBV2Listener)
        WHERE coalesce(l.protocol, '') IN ['HTTPS', 'TLS']
          AND (l.ssl_policy IS NULL OR NOT l.ssl_policy =~ 'ELBSecurityPolicy-.*-FIPS-.*')
        RETURN a.id AS account_id, a.name AS account, l.id AS listener_arn,
               l.port AS port, l.protocol AS protocol, l.ssl_policy AS ssl_policy

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(l:AWSELBV2Listener)
        WHERE coalesce(l.protocol, '') IN ['HTTPS', 'TLS']
          AND (l.ssl_policy IS NULL OR NOT l.ssl_policy =~ 'ELBSecurityPolicy-.*-FIPS-.*')
        RETURN a.id AS account_id, a.name AS account, l.id AS listener_arn,
               l.port AS port, l.protocol AS protocol, l.ssl_policy AS ssl_policy

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(l:AWSELBV2Listener)
        WHERE coalesce(l.protocol, '') IN ['HTTPS', 'TLS']
          AND (l.ssl_policy IS NULL OR NOT l.ssl_policy =~ 'ELBSecurityPolicy-.*-FIPS-.*')
        RETURN a.id AS account_id, a.name AS account, l.id AS listener_arn,
               l.port AS port, l.protocol AS protocol, l.ssl_policy AS ssl_policy

    """,
    asset_label="AWSELBV2Listener",
    asset_id_field="listener_arn",
    identity_fields=("account_id", "account", "listener_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_elbv2_listener_fips_tls = Rule(
    id="aws_elbv2_listener_fips_tls",
    name="ELBv2 Listener FIPS TLS Policy",
    description="HTTPS/TLS listener whose ssl_policy does not match the FIPS pattern ELBSecurityPolicy-*-FIPS-* (FIPS 140 validated AWS-LC cryptographic module).",
    output_model=AwsElbv2ListenerFipsTlsOutput,
    facts=(_aws_elbv2_listener_fips_tls_fact,),
    tags=("security", "elbv2", "encryption", "cspm"),
    version="0.1.0",
)


class AwsElbv2ListenerPqcTlsOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    listener_arn: str | None = None
    port: str | None = None
    protocol: str | None = None
    ssl_policy: str | None = None


_aws_elbv2_listener_pqc_tls_fact = Fact(
    id="aws_elbv2_listener_pqc_tls_fact",
    name="ELBv2 listener without PQ TLS policy",
    description="HTTPS/TLS listeners whose ssl_policy is absent or outside the PQ policy family.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(l:AWSELBV2Listener)
        WHERE coalesce(l.protocol, '') IN ['HTTPS', 'TLS']
          AND (l.ssl_policy IS NULL OR NOT l.ssl_policy =~ 'ELBSecurityPolicy-TLS13-.*-PQ-.*')
        RETURN a.id AS account_id, a.name AS account, l.id AS listener_arn,
               l.port AS port, l.protocol AS protocol, l.ssl_policy AS ssl_policy

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(l:AWSELBV2Listener)
        WHERE coalesce(l.protocol, '') IN ['HTTPS', 'TLS']
          AND (l.ssl_policy IS NULL OR NOT l.ssl_policy =~ 'ELBSecurityPolicy-TLS13-.*-PQ-.*')
        RETURN a.id AS account_id, a.name AS account, l.id AS listener_arn,
               l.port AS port, l.protocol AS protocol, l.ssl_policy AS ssl_policy

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(l:AWSELBV2Listener)
        WHERE coalesce(l.protocol, '') IN ['HTTPS', 'TLS']
          AND (l.ssl_policy IS NULL OR NOT l.ssl_policy =~ 'ELBSecurityPolicy-TLS13-.*-PQ-.*')
        RETURN a.id AS account_id, a.name AS account, l.id AS listener_arn,
               l.port AS port, l.protocol AS protocol, l.ssl_policy AS ssl_policy

    """,
    asset_label="AWSELBV2Listener",
    asset_id_field="listener_arn",
    identity_fields=("account_id", "account", "listener_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_elbv2_listener_pqc_tls = Rule(
    id="aws_elbv2_listener_pqc_tls",
    name="ELBv2 Listener Post-Quantum TLS Policy",
    description="HTTPS/TLS listener whose ssl_policy is not a post-quantum policy (TLS 1.3 with ML-KEM hybrid key exchange). BEST-EFFORT: the approved PQ set is approximated by the documented ELBSecurityPolicy-TLS13-*-PQ-* family (e.g. ELBSecurityPolicy-TLS13-1-2-PQ-2025-09); the exact approved set could not be verified offline.",
    output_model=AwsElbv2ListenerPqcTlsOutput,
    facts=(_aws_elbv2_listener_pqc_tls_fact,),
    tags=("security", "elbv2", "encryption", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsElbv2ListenerSecureSslPolicyOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    listener_id: str | None = None
    port: str | None = None
    protocol: str | None = None
    ssl_policy: str | None = None
    load_balancer_arn: str | None = None


_aws_elbv2_listener_secure_ssl_policy_fact = Fact(
    id="aws_elbv2_listener_secure_ssl_policy_fact",
    name="ELBv2 insecure SSL policy",
    description="HTTPS/TLS listeners with a legacy or missing SSL security policy.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(l:AWSELBV2Listener)
        WHERE l.protocol IN ['HTTPS', 'TLS']
          AND (l.ssl_policy IS NULL OR NOT (
                l.ssl_policy STARTS WITH 'ELBSecurityPolicy-TLS13-'
                OR l.ssl_policy STARTS WITH 'ELBSecurityPolicy-FS-1-2'
                OR l.ssl_policy IN ['ELBSecurityPolicy-TLS-1-2-2017-04', 'ELBSecurityPolicy-TLS-1-2-Ext-2018-06']))
        OPTIONAL MATCH (lb:AWSLoadBalancerV2)-[:ELBV2_LISTENER]->(l)
        RETURN a.id AS account_id, a.name AS account, l.id AS listener_id,
               l.port AS port, l.protocol AS protocol, l.ssl_policy AS ssl_policy,
               lb.arn AS load_balancer_arn

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(l:AWSELBV2Listener)
        WHERE l.protocol IN ['HTTPS', 'TLS']
          AND (l.ssl_policy IS NULL OR NOT (
                l.ssl_policy STARTS WITH 'ELBSecurityPolicy-TLS13-'
                OR l.ssl_policy STARTS WITH 'ELBSecurityPolicy-FS-1-2'
                OR l.ssl_policy IN ['ELBSecurityPolicy-TLS-1-2-2017-04', 'ELBSecurityPolicy-TLS-1-2-Ext-2018-06']))
        OPTIONAL MATCH (lb:AWSLoadBalancerV2)-[:ELBV2_LISTENER]->(l)
        RETURN a.id AS account_id, a.name AS account, l.id AS listener_id,
               l.port AS port, l.protocol AS protocol, l.ssl_policy AS ssl_policy,
               lb.arn AS load_balancer_arn

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(l:AWSELBV2Listener)
        WHERE l.protocol IN ['HTTPS', 'TLS']
          AND (l.ssl_policy IS NULL OR NOT (
                l.ssl_policy STARTS WITH 'ELBSecurityPolicy-TLS13-'
                OR l.ssl_policy STARTS WITH 'ELBSecurityPolicy-FS-1-2'
                OR l.ssl_policy IN ['ELBSecurityPolicy-TLS-1-2-2017-04', 'ELBSecurityPolicy-TLS-1-2-Ext-2018-06']))
        OPTIONAL MATCH (lb:AWSLoadBalancerV2)-[:ELBV2_LISTENER]->(l)
        RETURN a.id AS account_id, a.name AS account, l.id AS listener_id,
               l.port AS port, l.protocol AS protocol, l.ssl_policy AS ssl_policy,
               lb.arn AS load_balancer_arn

    """,
    asset_label="AWSELBV2Listener",
    asset_id_field="listener_id",
    identity_fields=(
        "account_id",
        "account",
        "listener_id",
        "load_balancer_arn",
    ),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_elbv2_listener_secure_ssl_policy = Rule(
    id="aws_elbv2_listener_secure_ssl_policy",
    name="ELBv2 Listener Secure SSL Policy",
    description="HTTPS/TLS listener whose ssl_policy is not a modern TLS 1.2/1.3-focused policy. The approved set is approximated by prefix: ELBSecurityPolicy-TLS13-* (incl. Res/Ext/FIPS/PQ variants), ELBSecurityPolicy-FS-1-2-*, plus ELBSecurityPolicy-TLS-1-2-2017-04 and ELBSecurityPolicy-TLS-1-2-Ext-2018-06; legacy defaults (2016-08, TLS-1-0/1-1 families) and missing policies fail. The exact approved list is not in the local sources, so the allowlist needs live validation. Count denominator: HTTPS/TLS listeners only.",
    output_model=AwsElbv2ListenerSecureSslPolicyOutput,
    facts=(_aws_elbv2_listener_secure_ssl_policy_fact,),
    tags=("security", "elbv2", "encryption", "cspm"),
    version="0.1.0",
)
