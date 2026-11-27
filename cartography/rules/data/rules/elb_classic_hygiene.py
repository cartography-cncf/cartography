"""
Classic Load Balancer listener and exposure checks

Plaintext listeners, internet-facing scheme, and TLS security policy for
classic ELBs. ``policy_names`` is only populated for HTTPS/SSL listeners.

No collector change is required: every property and relationship used
here is synced by the existing EC2 and WAFv2 modules. All rules are
EXPERIMENTAL until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsElbEncryptedListenersOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    listener_id: str | None = None
    port: str | None = None
    protocol: str | None = None
    load_balancer_name: str | None = None


_aws_elb_encrypted_listeners_fact = Fact(
    id="aws_elb_encrypted_listeners_fact",
    name="ELB plaintext listener",
    description="Listeners with protocol HTTP or TCP.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(l:AWSELBListener)
        WHERE l.protocol = 'HTTP'
        OPTIONAL MATCH (lb:AWSLoadBalancer)-[:ELB_LISTENER]->(l)
        RETURN a.id AS account_id, a.name AS account, l.id AS listener_id,
               l.port AS port, l.protocol AS protocol, lb.name AS load_balancer_name

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(l:AWSELBListener)
        WHERE l.protocol = 'HTTP'
        OPTIONAL MATCH (lb:AWSLoadBalancer)-[:ELB_LISTENER]->(l)
        RETURN a.id AS account_id, a.name AS account, l.id AS listener_id,
               l.port AS port, l.protocol AS protocol, lb.name AS load_balancer_name

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(l:AWSELBListener)
        WHERE l.protocol = 'HTTP'
        OPTIONAL MATCH (lb:AWSLoadBalancer)-[:ELB_LISTENER]->(l)
        RETURN a.id AS account_id, a.name AS account, l.id AS listener_id,
               l.port AS port, l.protocol AS protocol, lb.name AS load_balancer_name

    """,
    asset_label="AWSELBListener",
    asset_id_field="listener_id",
    identity_fields=(
        "account_id",
        "account",
        "listener_id",
        "load_balancer_name",
    ),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_elb_encrypted_listeners = Rule(
    id="aws_elb_encrypted_listeners",
    name="ELB Encrypted Listeners",
    description="Classic ELB listener uses HTTP, so client traffic to the load balancer is plaintext. TCP listeners are not reported: a layer-4 listener passes TLS through end to end.",
    output_model=AwsElbEncryptedListenersOutput,
    facts=(_aws_elb_encrypted_listeners_fact,),
    tags=("security", "elb", "encryption", "cspm"),
    version="0.1.0",
)


class AwsElbInternetFacingOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    load_balancer_id: str | None = None
    load_balancer_name: str | None = None
    dns_name: str | None = None
    scheme: str | None = None
    exposed_internet: str | None = None


_aws_elb_internet_facing_fact = Fact(
    id="aws_elb_internet_facing_fact",
    name="ELB internet-facing",
    description="Load balancers with scheme internet-facing.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancer)
        WHERE lb.scheme = 'internet-facing'
        RETURN a.id AS account_id, a.name AS account, lb.id AS load_balancer_id,
               lb.name AS load_balancer_name, lb.dnsname AS dns_name,
               lb.scheme AS scheme, lb.exposed_internet AS exposed_internet

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancer)
        WHERE lb.scheme = 'internet-facing'
        RETURN a.id AS account_id, a.name AS account, lb.id AS load_balancer_id,
               lb.name AS load_balancer_name, lb.dnsname AS dns_name,
               lb.scheme AS scheme, lb.exposed_internet AS exposed_internet

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancer)
        WHERE lb.scheme = 'internet-facing'
        RETURN a.id AS account_id, a.name AS account, lb.id AS load_balancer_id,
               lb.name AS load_balancer_name, lb.dnsname AS dns_name,
               lb.scheme AS scheme, lb.exposed_internet AS exposed_internet

    """,
    asset_label="AWSLoadBalancer",
    asset_id_field="load_balancer_id",
    identity_fields=("account_id", "account", "load_balancer_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_elb_internet_facing = Rule(
    id="aws_elb_internet_facing",
    name="ELB Internet-Facing",
    description="Classic load balancer has scheme 'internet-facing', so its endpoint is publicly reachable. exposed_internet (computed by the EC2 exposure analysis jobs) is returned for context. Classic ELB only per the spec asset label.",
    output_model=AwsElbInternetFacingOutput,
    facts=(_aws_elb_internet_facing_fact,),
    tags=("security", "elb", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsElbListenerTlsPolicyOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    listener_id: str | None = None
    port: str | None = None
    protocol: str | None = None
    policy_names: str | None = None
    load_balancer_name: str | None = None


_aws_elb_listener_tls_policy_fact = Fact(
    id="aws_elb_listener_tls_policy_fact",
    name="ELB weak TLS policy",
    description="HTTPS/SSL listeners without the pinned TLS-1-2 policy.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(l:AWSELBListener)
        WHERE l.protocol IN ['HTTPS', 'SSL']
          AND (l.policy_names IS NULL OR NOT 'ELBSecurityPolicy-TLS-1-2-2017-01' IN l.policy_names)
        OPTIONAL MATCH (lb:AWSLoadBalancer)-[:ELB_LISTENER]->(l)
        RETURN a.id AS account_id, a.name AS account, l.id AS listener_id,
               l.port AS port, l.protocol AS protocol, l.policy_names AS policy_names,
               lb.name AS load_balancer_name

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(l:AWSELBListener)
        WHERE l.protocol IN ['HTTPS', 'SSL']
          AND (l.policy_names IS NULL OR NOT 'ELBSecurityPolicy-TLS-1-2-2017-01' IN l.policy_names)
        OPTIONAL MATCH (lb:AWSLoadBalancer)-[:ELB_LISTENER]->(l)
        RETURN a.id AS account_id, a.name AS account, l.id AS listener_id,
               l.port AS port, l.protocol AS protocol, l.policy_names AS policy_names,
               lb.name AS load_balancer_name

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(l:AWSELBListener)
        WHERE l.protocol IN ['HTTPS', 'SSL']
          AND (l.policy_names IS NULL OR NOT 'ELBSecurityPolicy-TLS-1-2-2017-01' IN l.policy_names)
        OPTIONAL MATCH (lb:AWSLoadBalancer)-[:ELB_LISTENER]->(l)
        RETURN a.id AS account_id, a.name AS account, l.id AS listener_id,
               l.port AS port, l.protocol AS protocol, l.policy_names AS policy_names,
               lb.name AS load_balancer_name

    """,
    asset_label="AWSELBListener",
    asset_id_field="listener_id",
    identity_fields=(
        "account_id",
        "account",
        "listener_id",
        "load_balancer_name",
    ),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_elb_listener_tls_policy = Rule(
    id="aws_elb_listener_tls_policy",
    name="ELB Listener TLS Policy",
    description="Classic ELB HTTPS/SSL listener whose policy_names does not include ELBSecurityPolicy-TLS-1-2-2017-01. The policy name is pinned exactly per the spec predicate (newer strong policies also flag); classic ELB only, not ALB/NLB. policy_names population for SSL listeners needs live verification.",
    output_model=AwsElbListenerTlsPolicyOutput,
    facts=(_aws_elb_listener_tls_policy_fact,),
    tags=("security", "elb", "encryption", "cspm"),
    version="0.1.0",
)
