"""
ELBv2 load balancer exposure, coverage and resilience

Internet-reachable ALBs without WAF, listeners that cannot serve, single-AZ
placement, and NLBs that do not terminate TLS.

Exposure here is computed from the graph rather than trusted from
``exposed_internet`` alone: upstream's analysis job sets that property for
internet-facing NLBs and for ELBv2 whose listener port falls inside a
0.0.0.0/0 security-group rule, but it does not cover an ALB that is
internet-facing with a world-open group on a different port. The ALB rule
tests both the property and the security-group path directly.

No collector change is required: every property and relationship used
here is synced by the existing EC2 and WAFv2 modules. All rules are
EXPERIMENTAL until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsElbv2AlbPublicIngressOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    lb_arn: str | None = None
    lb_name: str | None = None
    scheme: str | None = None
    exposed_internet: str | None = None


_aws_elbv2_alb_public_ingress_fact = Fact(
    id="aws_elbv2_alb_public_ingress_fact",
    name="ALB public ingress",
    description="Internet-facing ALBs with world-open inbound TCP or exposed_internet=true, without WAF protection.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancerV2)
        WHERE lb.type = 'application' AND lb.scheme = 'internet-facing'
        WITH a, lb,
             EXISTS {
               MATCH (lb)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:AWSEC2SecurityGroup)
                     <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
                     <-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
               WHERE ip.range IN ['0.0.0.0/0', '::/0']
                 AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
             } AS world_open
        WHERE (lb.exposed_internet = true OR world_open)
          AND NOT (:AWSWebACL)-[:PROTECTS]->(lb)
        RETURN a.id AS account_id, a.name AS account, lb.arn AS lb_arn,
               lb.name AS lb_name, lb.scheme AS scheme,
               lb.exposed_internet AS exposed_internet

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancerV2)
        WHERE lb.type = 'application' AND lb.scheme = 'internet-facing'
        WITH a, lb,
             EXISTS {
               MATCH (lb)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:AWSEC2SecurityGroup)
                     <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
                     <-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
               WHERE ip.range IN ['0.0.0.0/0', '::/0']
                 AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
             } AS world_open
        WHERE (lb.exposed_internet = true OR world_open)
          AND NOT (:AWSWebACL)-[:PROTECTS]->(lb)
        RETURN a.id AS account_id, a.name AS account, lb.arn AS lb_arn,
               lb.name AS lb_name, lb.scheme AS scheme,
               lb.exposed_internet AS exposed_internet

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancerV2)
        WHERE lb.type = 'application' AND lb.scheme = 'internet-facing'
        WITH a, lb,
             EXISTS {
               MATCH (lb)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:AWSEC2SecurityGroup)
                     <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
                     <-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
               WHERE ip.range IN ['0.0.0.0/0', '::/0']
                 AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
             } AS world_open
        WHERE (lb.exposed_internet = true OR world_open)
          AND NOT (:AWSWebACL)-[:PROTECTS]->(lb)
        RETURN a.id AS account_id, a.name AS account, lb.arn AS lb_arn,
               lb.name AS lb_name, lb.scheme AS scheme,
               lb.exposed_internet AS exposed_internet

    """,
    asset_label="AWSLoadBalancerV2",
    asset_id_field="lb_arn",
    identity_fields=("account_id", "account", "lb_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_elbv2_alb_public_ingress = Rule(
    id="aws_elbv2_alb_public_ingress",
    name="ELBv2 ALB Public Ingress",
    description="Application load balancer with scheme 'internet-facing' that is reachable from the internet - either exposed_internet is already set, or a security group attached to it admits 0.0.0.0/0 or ::/0 on tcp/all - and has no AWSWebACL PROTECTS edge. CloudFront-fronted ALBs are reported too: the distribution-to-origin relation is not modelled upstream (no origin_endpoints property), so this cannot tell that only CloudFront reaches the load balancer.",
    output_model=AwsElbv2AlbPublicIngressOutput,
    facts=(_aws_elbv2_alb_public_ingress_fact,),
    tags=("security", "elbv2", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsElbv2HasListenersOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    lb_arn: str | None = None
    lb_name: str | None = None
    lb_type: str | None = None
    listener_count: int | None = None


_aws_elbv2_has_listeners_fact = Fact(
    id="aws_elbv2_has_listeners_fact",
    name="ELBv2 no listeners",
    description="Load balancers without any listener.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancerV2)
        OPTIONAL MATCH (lb)-[:ELBV2_LISTENER]->(l:AWSELBV2Listener)
        WITH a, lb, COUNT(l) AS listener_count
        WHERE listener_count = 0
        RETURN a.id AS account_id, a.name AS account, lb.arn AS lb_arn,
               lb.name AS lb_name, lb.type AS lb_type, listener_count AS listener_count

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancerV2)
        OPTIONAL MATCH (lb)-[:ELBV2_LISTENER]->(l:AWSELBV2Listener)
        WITH a, lb, COUNT(l) AS listener_count
        WHERE listener_count = 0
        RETURN a.id AS account_id, a.name AS account, lb.arn AS lb_arn,
               lb.name AS lb_name, lb.type AS lb_type, listener_count AS listener_count

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancerV2)
        OPTIONAL MATCH (lb)-[:ELBV2_LISTENER]->(l:AWSELBV2Listener)
        WITH a, lb, COUNT(l) AS listener_count
        WHERE listener_count = 0
        RETURN a.id AS account_id, a.name AS account, lb.arn AS lb_arn,
               lb.name AS lb_name, lb.type AS lb_type, listener_count AS listener_count

    """,
    asset_label="AWSLoadBalancerV2",
    asset_id_field="lb_arn",
    identity_fields=("account_id", "account", "lb_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_elbv2_has_listeners = Rule(
    id="aws_elbv2_has_listeners",
    name="ELBv2 Load Balancer Has Listeners",
    description="Load balancer has no ELBV2_LISTENER relationship to any AWSELBV2Listener and therefore cannot serve traffic.",
    output_model=AwsElbv2HasListenersOutput,
    facts=(_aws_elbv2_has_listeners_fact,),
    tags=("infrastructure", "elbv2", "availability", "cspm"),
    version="0.1.0",
)


class AwsElbv2MultiAzOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    lb_arn: str | None = None
    lb_name: str | None = None
    lb_type: str | None = None
    az_count: int | None = None


_aws_elbv2_multi_az_fact = Fact(
    id="aws_elbv2_multi_az_fact",
    name="ELBv2 single-AZ",
    description="Load balancers with fewer than 2 distinct subnet availability zones.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancerV2)
        OPTIONAL MATCH (lb)-[:SUBNET]->(s:AWSEC2Subnet)
        WITH a, lb, COUNT(DISTINCT s.availability_zone) AS az_count
        WHERE az_count < 2
        RETURN a.id AS account_id, a.name AS account, lb.arn AS lb_arn,
               lb.name AS lb_name, lb.type AS lb_type, az_count AS az_count

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancerV2)
        OPTIONAL MATCH (lb)-[:SUBNET]->(s:AWSEC2Subnet)
        WITH a, lb, COUNT(DISTINCT s.availability_zone) AS az_count
        WHERE az_count < 2
        RETURN a.id AS account_id, a.name AS account, lb.arn AS lb_arn,
               lb.name AS lb_name, lb.type AS lb_type, az_count AS az_count

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancerV2)
        OPTIONAL MATCH (lb)-[:SUBNET]->(s:AWSEC2Subnet)
        WITH a, lb, COUNT(DISTINCT s.availability_zone) AS az_count
        WHERE az_count < 2
        RETURN a.id AS account_id, a.name AS account, lb.arn AS lb_arn,
               lb.name AS lb_name, lb.type AS lb_type, az_count AS az_count

    """,
    asset_label="AWSLoadBalancerV2",
    asset_id_field="lb_arn",
    identity_fields=("account_id", "account", "lb_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_elbv2_multi_az = Rule(
    id="aws_elbv2_multi_az",
    name="ELBv2 Load Balancer Multi-AZ",
    description="Load balancer spans fewer than 2 distinct availability zones across its SUBNET relationships (including load balancers with no subnet links). AZ values come from AWSEC2Subnet.availability_zone and require the EC2 subnet sync; subnet nodes lacking that property count as 0 AZs.",
    output_model=AwsElbv2MultiAzOutput,
    facts=(_aws_elbv2_multi_az_fact,),
    tags=("infrastructure", "elbv2", "availability", "cspm"),
    version="0.1.0",
)


class AwsElbv2NlbTlsTerminationOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    lb_arn: str | None = None
    lb_name: str | None = None
    listener_count: int | None = None
    tls_listener_count: int | None = None


_aws_elbv2_nlb_tls_termination_fact = Fact(
    id="aws_elbv2_nlb_tls_termination_fact",
    name="NLB without TLS listener",
    description="NLBs with zero TLS-protocol listeners.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancerV2)
        WHERE lb.type = 'network'
        OPTIONAL MATCH (lb)-[:ELBV2_LISTENER]->(l:AWSELBV2Listener)
        WITH a, lb, COUNT(l) AS listener_count,
             COUNT(CASE WHEN l.protocol = 'TLS' THEN 1 END) AS tls_listener_count
        WHERE tls_listener_count = 0
        RETURN a.id AS account_id, a.name AS account, lb.arn AS lb_arn,
               lb.name AS lb_name, listener_count AS listener_count,
               tls_listener_count AS tls_listener_count

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancerV2)
        WHERE lb.type = 'network'
        OPTIONAL MATCH (lb)-[:ELBV2_LISTENER]->(l:AWSELBV2Listener)
        WITH a, lb, COUNT(l) AS listener_count,
             COUNT(CASE WHEN l.protocol = 'TLS' THEN 1 END) AS tls_listener_count
        WHERE tls_listener_count = 0
        RETURN a.id AS account_id, a.name AS account, lb.arn AS lb_arn,
               lb.name AS lb_name, listener_count AS listener_count,
               tls_listener_count AS tls_listener_count

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancerV2)
        WHERE lb.type = 'network'
        OPTIONAL MATCH (lb)-[:ELBV2_LISTENER]->(l:AWSELBV2Listener)
        WITH a, lb, COUNT(l) AS listener_count,
             COUNT(CASE WHEN l.protocol = 'TLS' THEN 1 END) AS tls_listener_count
        WHERE tls_listener_count = 0
        RETURN a.id AS account_id, a.name AS account, lb.arn AS lb_arn,
               lb.name AS lb_name, listener_count AS listener_count,
               tls_listener_count AS tls_listener_count

    """,
    asset_label="AWSLoadBalancerV2",
    asset_id_field="lb_arn",
    identity_fields=("account_id", "account", "lb_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_elbv2_nlb_tls_termination = Rule(
    id="aws_elbv2_nlb_tls_termination",
    name="ELBv2 NLB TLS Termination",
    description="Network load balancer (type='network') has no listener using protocol='TLS', so TLS is not terminated at the load balancer. Count denominator: network load balancers.",
    output_model=AwsElbv2NlbTlsTerminationOutput,
    facts=(_aws_elbv2_nlb_tls_termination_fact,),
    tags=("security", "elbv2", "encryption", "cspm"),
    version="0.1.0",
)


class AwsElbv2WafAttachedOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    load_balancer_id: str | None = None
    load_balancer_arn: str | None = None
    load_balancer_name: str | None = None
    scheme: str | None = None
    region: str | None = None


_aws_elbv2_waf_attached_fact = Fact(
    id="aws_elbv2_waf_attached_fact",
    name="ALB without a WAFv2 WebACL",
    description="Internet-facing application load balancers with no inbound PROTECTS edge from any AWSWebACL.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancerV2)
        WHERE lb.type = 'application' AND lb.scheme = 'internet-facing'
          AND NOT (:AWSWebACL)-[:PROTECTS]->(lb)
        RETURN a.id AS account_id, a.name AS account, lb.id AS load_balancer_id,
               lb.arn AS load_balancer_arn, lb.name AS load_balancer_name,
               lb.scheme AS scheme, lb.region AS region

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancerV2)
        WHERE lb.type = 'application' AND lb.scheme = 'internet-facing'
          AND NOT (:AWSWebACL)-[:PROTECTS]->(lb)
        RETURN a.id AS account_id, a.name AS account, lb.id AS load_balancer_id,
               lb.arn AS load_balancer_arn, lb.name AS load_balancer_name,
               lb.scheme AS scheme, lb.region AS region

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lb:AWSLoadBalancerV2)
        WHERE lb.type = 'application' AND lb.scheme = 'internet-facing'
          AND NOT (:AWSWebACL)-[:PROTECTS]->(lb)
        RETURN a.id AS account_id, a.name AS account, lb.id AS load_balancer_id,
               lb.arn AS load_balancer_arn, lb.name AS load_balancer_name,
               lb.scheme AS scheme, lb.region AS region

    """,
    asset_label="AWSLoadBalancerV2",
    asset_id_field="load_balancer_id",
    identity_fields=("account_id", "account", "load_balancer_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_elbv2_waf_attached = Rule(
    id="aws_elbv2_waf_attached",
    name="Application Load Balancer WAFv2 WebACL Attached",
    description="An application load balancer with no WAFv2 WebACL associated (no inbound AWSWebACL-[:PROTECTS] edge). Requires the wafv2 sync (custom cartography build, upstream #2911). Network load balancers are excluded: WAFv2 only associates with ALBs. Internal ALBs are skipped: WAF protects the public edge.",
    output_model=AwsElbv2WafAttachedOutput,
    facts=(_aws_elbv2_waf_attached_fact,),
    tags=("security", "elbv2", "wafv2", "cspm"),
    version="0.1.0",
)
