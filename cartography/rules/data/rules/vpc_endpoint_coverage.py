"""
AWS VPC endpoint coverage, resilience and access policy

A VPC with no Interface endpoint for the EC2 API, Interface endpoints whose
subnets sit in a single availability zone, and endpoint policies that allow
any principal.

The EC2-service endpoint check is a private-API-access posture control: without
it, EC2 API calls from the VPC leave over the internet or a NAT gateway. It is
advisory and depends on the organisation actually standardising on VPC
endpoints.

No collector change is required: every property and relationship used
here is synced by the existing EC2 module. All rules are EXPERIMENTAL
until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsVpcEc2InterfaceEndpointPresentOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    vpc_id: str | None = None
    region: str | None = None


_aws_vpc_ec2_interface_endpoint_present_fact = Fact(
    id="aws_vpc_ec2_interface_endpoint_present_fact",
    name="VPC missing EC2 endpoint",
    description="VPCs without an Interface endpoint whose service_name is com.amazonaws.<region>.ec2.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(v:AWSVpc)
        WHERE NOT EXISTS {
            MATCH (e:AWSVpcEndpoint)-[:MEMBER_OF_AWS_VPC]->(v)
            WHERE e.vpc_endpoint_type = 'Interface'
              AND e.service_name = 'com.amazonaws.' + v.region + '.ec2'
        }
        RETURN a.id AS account_id, a.name AS account, v.id AS vpc_id,
               v.region AS region

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(v:AWSVpc)
        WHERE NOT EXISTS {
            MATCH (e:AWSVpcEndpoint)-[:MEMBER_OF_AWS_VPC]->(v)
            WHERE e.vpc_endpoint_type = 'Interface'
              AND e.service_name = 'com.amazonaws.' + v.region + '.ec2'
        }
        RETURN a.id AS account_id, a.name AS account, v.id AS vpc_id,
               v.region AS region

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(v:AWSVpc)
        WHERE NOT EXISTS {
            MATCH (e:AWSVpcEndpoint)-[:MEMBER_OF_AWS_VPC]->(v)
            WHERE e.vpc_endpoint_type = 'Interface'
              AND e.service_name = 'com.amazonaws.' + v.region + '.ec2'
        }
        RETURN a.id AS account_id, a.name AS account, v.id AS vpc_id,
               v.region AS region

    """,
    asset_label="AWSVpc",
    asset_id_field="vpc_id",
    identity_fields=("account_id", "account", "vpc_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_vpc_ec2_interface_endpoint_present = Rule(
    id="aws_vpc_ec2_interface_endpoint_present",
    name="VPC EC2 Interface Endpoint Present",
    description="VPC has no Interface-type endpoint for the EC2 service (com.amazonaws.<region>.ec2), so EC2 API traffic cannot stay on the private network. Endpoints joined via MEMBER_OF_AWS_VPC. The spec lists AWSVpcEndpoint as asset label, but the absence predicate evaluates VPCs, so findings are per VPC (asset_label=AWSVpc).",
    output_model=AwsVpcEc2InterfaceEndpointPresentOutput,
    facts=(_aws_vpc_ec2_interface_endpoint_present_fact,),
    tags=("infrastructure", "vpc", "network", "cspm"),
    version="0.1.0",
)


class AwsVpcEndpointMultiAzOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    endpoint_id: str | None = None
    vpc_id: str | None = None
    service_name: str | None = None
    az_count: int | None = None


_aws_vpc_endpoint_multi_az_fact = Fact(
    id="aws_vpc_endpoint_multi_az_fact",
    name="Interface endpoint single-AZ",
    description="Interface endpoints whose resolved subnets span fewer than 2 distinct AZs.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(e:AWSVpcEndpoint)
        WHERE e.vpc_endpoint_type = 'Interface'
        OPTIONAL MATCH (s:AWSEC2Subnet)
        WHERE s.subnet_id IN e.subnet_ids
        WITH a, e, collect(DISTINCT s.availability_zone) AS azs
        WITH a, e, [az IN azs WHERE az IS NOT NULL] AS valid_azs
        WHERE size(valid_azs) < 2
        RETURN a.id AS account_id, a.name AS account, e.id AS endpoint_id,
               e.vpc_id AS vpc_id, e.service_name AS service_name,
               size(valid_azs) AS az_count

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(e:AWSVpcEndpoint)
        WHERE e.vpc_endpoint_type = 'Interface'
        OPTIONAL MATCH (s:AWSEC2Subnet)
        WHERE s.subnet_id IN e.subnet_ids
        WITH a, e, collect(DISTINCT s.availability_zone) AS azs
        WITH a, e, [az IN azs WHERE az IS NOT NULL] AS valid_azs
        WHERE size(valid_azs) < 2
        RETURN a.id AS account_id, a.name AS account, e.id AS endpoint_id,
               e.vpc_id AS vpc_id, e.service_name AS service_name,
               size(valid_azs) AS az_count

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(e:AWSVpcEndpoint)
        WHERE e.vpc_endpoint_type = 'Interface'
        OPTIONAL MATCH (s:AWSEC2Subnet)
        WHERE s.subnet_id IN e.subnet_ids
        WITH a, e, collect(DISTINCT s.availability_zone) AS azs
        WITH a, e, [az IN azs WHERE az IS NOT NULL] AS valid_azs
        WHERE size(valid_azs) < 2
        RETURN a.id AS account_id, a.name AS account, e.id AS endpoint_id,
               e.vpc_id AS vpc_id, e.service_name AS service_name,
               size(valid_azs) AS az_count

    """,
    asset_label="AWSVpcEndpoint",
    asset_id_field="endpoint_id",
    identity_fields=("account_id", "account", "endpoint_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_vpc_endpoint_multi_az = Rule(
    id="aws_vpc_endpoint_multi_az",
    name="VPC Interface Endpoint Multi-AZ",
    description="An Interface VPC endpoint's subnets span fewer than two distinct availability zones (single-AZ endpoint is not resilient to an AZ failure). Subnets resolved by property join: AWSVpcEndpoint.subnet_ids against AWSEC2Subnet.subnet_id (the modeled USES_SUBNET edge is an alternative if live population differs); endpoints with unresolvable or empty subnet lists count as 0 AZs.",
    output_model=AwsVpcEndpointMultiAzOutput,
    facts=(_aws_vpc_endpoint_multi_az_fact,),
    tags=("infrastructure", "vpc", "resilience", "cspm"),
    version="0.1.0",
)


class AwsVpcEndpointPolicyTrustedPrincipalsOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    endpoint_id: str | None = None
    vpc_endpoint_id: str | None = None
    service_name: str | None = None
    vpc_id: str | None = None
    state: str | None = None
    policy_document: str | None = None


_aws_vpc_endpoint_policy_trusted_principals_fact = Fact(
    id="aws_vpc_endpoint_policy_trusted_principals_fact",
    name="VPC endpoint wildcard policy",
    description="Non-requester-managed endpoints whose policy document contains a wildcard principal (approximate).",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(e:AWSVpcEndpoint)
        WHERE coalesce(e.requester_managed, false) = false
          AND e.policy_document IS NOT NULL
          AND (e.policy_document CONTAINS '"Principal":"*"'
            OR e.policy_document CONTAINS '"Principal": "*"'
            OR e.policy_document CONTAINS '"AWS":"*"'
            OR e.policy_document CONTAINS '"AWS": "*"')
        RETURN a.id AS account_id, a.name AS account, e.id AS endpoint_id,
               e.vpc_endpoint_id AS vpc_endpoint_id, e.service_name AS service_name,
               e.vpc_id AS vpc_id, e.state AS state,
               e.policy_document AS policy_document

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(e:AWSVpcEndpoint)
        WHERE coalesce(e.requester_managed, false) = false
          AND e.policy_document IS NOT NULL
          AND (e.policy_document CONTAINS '"Principal":"*"'
            OR e.policy_document CONTAINS '"Principal": "*"'
            OR e.policy_document CONTAINS '"AWS":"*"'
            OR e.policy_document CONTAINS '"AWS": "*"')
        RETURN a.id AS account_id, a.name AS account, e.id AS endpoint_id,
               e.vpc_endpoint_id AS vpc_endpoint_id, e.service_name AS service_name,
               e.vpc_id AS vpc_id, e.state AS state,
               e.policy_document AS policy_document

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(e:AWSVpcEndpoint)
        WHERE coalesce(e.requester_managed, false) = false
          AND e.policy_document IS NOT NULL
          AND (e.policy_document CONTAINS '"Principal":"*"'
            OR e.policy_document CONTAINS '"Principal": "*"'
            OR e.policy_document CONTAINS '"AWS":"*"'
            OR e.policy_document CONTAINS '"AWS": "*"')
        RETURN a.id AS account_id, a.name AS account, e.id AS endpoint_id,
               e.vpc_endpoint_id AS vpc_endpoint_id, e.service_name AS service_name,
               e.vpc_id AS vpc_id, e.state AS state,
               e.policy_document AS policy_document

    """,
    asset_label="AWSVpcEndpoint",
    asset_id_field="endpoint_id",
    identity_fields=("endpoint_id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_vpc_endpoint_policy_trusted_principals = Rule(
    id="aws_vpc_endpoint_policy_trusted_principals",
    name="VPC Endpoint Policy Trusted Principals",
    description="BEST-EFFORT (EXPERIMENTAL): VPC endpoint access policy contains a wildcard principal ('*' or AWS:'*'), allowing access from any account. policy_document is a raw JSON string, so this CONTAINS approximation cannot evaluate restrictive conditions, and untrusted non-wildcard account ARNs are not detected: the trusted-account allowlist is rule configuration that does not exist in the graph. Requester-managed endpoints (no editable policy) are excluded. Needs Python JSON parsing for full coverage.",
    output_model=AwsVpcEndpointPolicyTrustedPrincipalsOutput,
    facts=(_aws_vpc_endpoint_policy_trusted_principals_fact,),
    tags=("security", "vpc", "attack_surface", "cspm", "best-effort"),
    version="0.1.0",
)
