"""
AWS VPC and subnet network placement and peering routes

Single-AZ subnet placement, subnets that auto-assign public IPv4 on launch,
and peering routes that carry a default route or the peer's whole CIDR.

The peering check reads peer CIDRs from AWSCidrBlock nodes reached over
REQUESTER_CIDR/ACCEPTER_CIDR, matched by the route's peering connection id.
A route whose destination is a narrower prefix inside the peer range is not
reported; a route to a prefix list carries no CIDR and is never evaluated.

No collector change is required: every property and relationship used
here is synced by the existing EC2 module. All rules are EXPERIMENTAL
until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsVpcPeeringLeastPrivilegeRoutesOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    route_id: str | None = None
    route_table_id: str | None = None
    destination_cidr_block: str | None = None
    destination_ipv6_cidr_block: str | None = None
    vpc_peering_connection_id: str | None = None


_aws_vpc_peering_least_privilege_routes_fact = Fact(
    id="aws_vpc_peering_least_privilege_routes_fact",
    name="Over-broad peering route",
    description="Peering-targeted routes with 0.0.0.0/0, ::/0 or a full peer VPC CIDR destination.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(rt:AWSEC2RouteTable)-[:ROUTE]->(r:AWSEC2Route)
        WHERE r.vpc_peering_connection_id IS NOT NULL
          AND (
            r.destination_cidr_block = '0.0.0.0/0'
            OR r.destination_ipv6_cidr_block = '::/0'
            OR EXISTS {
                MATCH (pc:AWSPeeringConnection)-[:REQUESTER_CIDR|ACCEPTER_CIDR]->(cidr:AWSCidrBlock)
                WHERE pc.id = r.vpc_peering_connection_id
                  AND (cidr.cidr_block = r.destination_cidr_block
                       OR cidr.cidr_block = r.destination_ipv6_cidr_block)
            }
          )
        RETURN a.id AS account_id, a.name AS account, r.id AS route_id,
               rt.id AS route_table_id,
               r.destination_cidr_block AS destination_cidr_block,
               r.destination_ipv6_cidr_block AS destination_ipv6_cidr_block,
               r.vpc_peering_connection_id AS vpc_peering_connection_id

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(rt:AWSEC2RouteTable)-[:ROUTE]->(r:AWSEC2Route)
        WHERE r.vpc_peering_connection_id IS NOT NULL
          AND (
            r.destination_cidr_block = '0.0.0.0/0'
            OR r.destination_ipv6_cidr_block = '::/0'
            OR EXISTS {
                MATCH (pc:AWSPeeringConnection)-[:REQUESTER_CIDR|ACCEPTER_CIDR]->(cidr:AWSCidrBlock)
                WHERE pc.id = r.vpc_peering_connection_id
                  AND (cidr.cidr_block = r.destination_cidr_block
                       OR cidr.cidr_block = r.destination_ipv6_cidr_block)
            }
          )
        RETURN a.id AS account_id, a.name AS account, r.id AS route_id,
               rt.id AS route_table_id,
               r.destination_cidr_block AS destination_cidr_block,
               r.destination_ipv6_cidr_block AS destination_ipv6_cidr_block,
               r.vpc_peering_connection_id AS vpc_peering_connection_id

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(rt:AWSEC2RouteTable)-[:ROUTE]->(r:AWSEC2Route)
        WHERE r.vpc_peering_connection_id IS NOT NULL
          AND (
            r.destination_cidr_block = '0.0.0.0/0'
            OR r.destination_ipv6_cidr_block = '::/0'
            OR EXISTS {
                MATCH (pc:AWSPeeringConnection)-[:REQUESTER_CIDR|ACCEPTER_CIDR]->(cidr:AWSCidrBlock)
                WHERE pc.id = r.vpc_peering_connection_id
                  AND (cidr.cidr_block = r.destination_cidr_block
                       OR cidr.cidr_block = r.destination_ipv6_cidr_block)
            }
          )
        RETURN a.id AS account_id, a.name AS account, r.id AS route_id,
               rt.id AS route_table_id,
               r.destination_cidr_block AS destination_cidr_block,
               r.destination_ipv6_cidr_block AS destination_ipv6_cidr_block,
               r.vpc_peering_connection_id AS vpc_peering_connection_id

    """,
    asset_label="AWSEC2Route",
    asset_id_field="route_id",
    identity_fields=(
        "account_id",
        "account",
        "route_id",
        "route_table_id",
    ),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_vpc_peering_least_privilege_routes = Rule(
    id="aws_vpc_peering_least_privilege_routes",
    name="VPC Peering Least-Privilege Routes",
    description="BEST-EFFORT (EXPERIMENTAL): a route targeting a VPC peering connection uses destination 0.0.0.0/0 (or ::/0) or the entire peer VPC CIDR instead of narrower prefixes. Peer CIDRs are read from AWSPeeringConnection-[:REQUESTER_CIDR|ACCEPTER_CIDR]->AWSCidrBlock and compared by exact string equality (no CIDR containment math); the upstream CIS AWS 6.6 TODO claims route/peering data is missing, so edge and property population must be verified live. Route state (blackhole) is not filtered.",
    output_model=AwsVpcPeeringLeastPrivilegeRoutesOutput,
    facts=(_aws_vpc_peering_least_privilege_routes_fact,),
    tags=("infrastructure", "vpc", "network", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsVpcSubnetMultiAzOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    vpc_id: str | None = None
    region: str | None = None
    az_count: int | None = None


_aws_vpc_subnet_multi_az_fact = Fact(
    id="aws_vpc_subnet_multi_az_fact",
    name="VPC subnets single-AZ",
    description="VPCs whose subnets span fewer than 2 distinct AZs (or have no subnets).",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(v:AWSVpc)
        OPTIONAL MATCH (s:AWSEC2Subnet)-[:MEMBER_OF_AWS_VPC]->(v)
        WITH a, v, collect(DISTINCT s.availability_zone) AS azs
        WITH a, v, [az IN azs WHERE az IS NOT NULL] AS valid_azs
        WHERE size(valid_azs) < 2
        RETURN a.id AS account_id, a.name AS account, v.id AS vpc_id,
               v.region AS region, size(valid_azs) AS az_count

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(v:AWSVpc)
        OPTIONAL MATCH (s:AWSEC2Subnet)-[:MEMBER_OF_AWS_VPC]->(v)
        WITH a, v, collect(DISTINCT s.availability_zone) AS azs
        WITH a, v, [az IN azs WHERE az IS NOT NULL] AS valid_azs
        WHERE size(valid_azs) < 2
        RETURN a.id AS account_id, a.name AS account, v.id AS vpc_id,
               v.region AS region, size(valid_azs) AS az_count

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(v:AWSVpc)
        OPTIONAL MATCH (s:AWSEC2Subnet)-[:MEMBER_OF_AWS_VPC]->(v)
        WITH a, v, collect(DISTINCT s.availability_zone) AS azs
        WITH a, v, [az IN azs WHERE az IS NOT NULL] AS valid_azs
        WHERE size(valid_azs) < 2
        RETURN a.id AS account_id, a.name AS account, v.id AS vpc_id,
               v.region AS region, size(valid_azs) AS az_count

    """,
    asset_label="AWSVpc",
    asset_id_field="vpc_id",
    identity_fields=("account_id", "account", "vpc_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_vpc_subnet_multi_az = Rule(
    id="aws_vpc_subnet_multi_az",
    name="VPC Subnet Multi-AZ",
    description="A VPC's subnets span fewer than two distinct availability zones, or the VPC has no subnets. Subnets joined via MEMBER_OF_AWS_VPC. The spec lists AWSEC2Subnet as asset label, but the predicate evaluates VPCs, so findings are per VPC (asset_label=AWSVpc).",
    output_model=AwsVpcSubnetMultiAzOutput,
    facts=(_aws_vpc_subnet_multi_az_fact,),
    tags=("infrastructure", "vpc", "resilience", "cspm"),
    version="0.1.0",
)


class AwsVpcSubnetNoAutoPublicIpOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    subnet_id: str | None = None
    cidr_block: str | None = None
    vpc_id: str | None = None
    availability_zone: str | None = None
    map_public_ip_on_launch: bool | None = None


_aws_vpc_subnet_no_auto_public_ip_fact = Fact(
    id="aws_vpc_subnet_no_auto_public_ip_fact",
    name="Subnet auto-assign public IP",
    description="Subnets with map_public_ip_on_launch=true.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(subnet:AWSEC2Subnet)
        WHERE subnet.map_public_ip_on_launch = true
        RETURN a.id AS account_id, a.name AS account, subnet.id AS subnet_id,
               subnet.cidr_block AS cidr_block, subnet.vpc_id AS vpc_id,
               subnet.availability_zone AS availability_zone,
               subnet.map_public_ip_on_launch AS map_public_ip_on_launch

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(subnet:AWSEC2Subnet)
        WHERE subnet.map_public_ip_on_launch = true
        RETURN a.id AS account_id, a.name AS account, subnet.id AS subnet_id,
               subnet.cidr_block AS cidr_block, subnet.vpc_id AS vpc_id,
               subnet.availability_zone AS availability_zone,
               subnet.map_public_ip_on_launch AS map_public_ip_on_launch

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(subnet:AWSEC2Subnet)
        WHERE subnet.map_public_ip_on_launch = true
        RETURN a.id AS account_id, a.name AS account, subnet.id AS subnet_id,
               subnet.cidr_block AS cidr_block, subnet.vpc_id AS vpc_id,
               subnet.availability_zone AS availability_zone,
               subnet.map_public_ip_on_launch AS map_public_ip_on_launch

    """,
    asset_label="AWSEC2Subnet",
    asset_id_field="subnet_id",
    identity_fields=("subnet_id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_vpc_subnet_no_auto_public_ip = Rule(
    id="aws_vpc_subnet_no_auto_public_ip",
    name="VPC Subnet No Auto-Assign Public IP",
    description="Subnet has map_public_ip_on_launch=true, auto-assigning public IPv4 addresses to instances at launch.",
    output_model=AwsVpcSubnetNoAutoPublicIpOutput,
    facts=(_aws_vpc_subnet_no_auto_public_ip_fact,),
    tags=("security", "vpc", "network", "attack_surface", "cspm"),
    version="0.1.0",
)
