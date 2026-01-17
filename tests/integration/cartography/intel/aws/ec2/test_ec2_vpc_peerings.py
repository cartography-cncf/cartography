import cartography.intel.aws.ec2.vpc_peerings
import tests.data.aws.ec2.vpc_peerings

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-north-1"
TEST_UPDATE_TAG = 123456789


def test_load_vpc_peerings(neo4j_session):
    data = tests.data.aws.ec2.vpc_peerings.DESCRIBE_VPC_PEERINGS
    vpc_peerings, accepter_cidrs, requester_cidrs, vpc_nodes = (
        cartography.intel.aws.ec2.vpc_peerings.transform_vpc_peering_data(
            data,
        )
    )
    aws_accounts = (
        cartography.intel.aws.ec2.vpc_peerings.transform_aws_accounts_from_vpc_peering(
            data,
        )
    )

    cartography.intel.aws.ec2.vpc_peerings.load_aws_accounts_from_vpc_peering(
        neo4j_session,
        aws_accounts,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ec2.vpc_peerings.load_vpc_nodes(
        neo4j_session,
        vpc_nodes,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ec2.vpc_peerings.load_accepter_cidrs(
        neo4j_session,
        accepter_cidrs,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ec2.vpc_peerings.load_requester_cidrs(
        neo4j_session,
        requester_cidrs,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ec2.vpc_peerings.load_vpc_peerings(
        neo4j_session,
        vpc_peerings,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "pcx-09969456d9ec69ab6",
    }

    nodes = neo4j_session.run(
        """
        MATCH (pcx:AWSPeeringConnection) RETURN pcx.id;
        """,
    )
    actual_nodes = {n["pcx.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_vpc_peering_relationships_vpc(neo4j_session):
    data = tests.data.aws.ec2.vpc_peerings.DESCRIBE_VPC_PEERINGS
    vpc_peerings, accepter_cidrs, requester_cidrs, vpc_nodes = (
        cartography.intel.aws.ec2.vpc_peerings.transform_vpc_peering_data(
            data,
        )
    )
    aws_accounts = (
        cartography.intel.aws.ec2.vpc_peerings.transform_aws_accounts_from_vpc_peering(
            data,
        )
    )

    cartography.intel.aws.ec2.vpc_peerings.load_aws_accounts_from_vpc_peering(
        neo4j_session,
        aws_accounts,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ec2.vpc_peerings.load_vpc_nodes(
        neo4j_session,
        vpc_nodes,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ec2.vpc_peerings.load_accepter_cidrs(
        neo4j_session,
        accepter_cidrs,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ec2.vpc_peerings.load_requester_cidrs(
        neo4j_session,
        requester_cidrs,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ec2.vpc_peerings.load_vpc_peerings(
        neo4j_session,
        vpc_peerings,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "vpc-055d355d6d2e498fa",
            "pcx-09969456d9ec69ab6",
            "vpc-0015dc961e537676a",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH
        (rvpc:AWSVpc)-[:REQUESTER_VPC]-(pcx:AWSPeeringConnection)-[:ACCEPTER_VPC]-(avpc:AWSVpc)
        RETURN rvpc.id, pcx.id, avpc.id;
        """,
    )
    actual = {(r["rvpc.id"], r["pcx.id"], r["avpc.id"]) for r in result}

    assert actual == expected_nodes


def test_vpc_peering_relationships_cidr(neo4j_session):
    data = tests.data.aws.ec2.vpc_peerings.DESCRIBE_VPC_PEERINGS
    vpc_peerings, accepter_cidrs, requester_cidrs, vpc_nodes = (
        cartography.intel.aws.ec2.vpc_peerings.transform_vpc_peering_data(
            data,
        )
    )
    aws_accounts = (
        cartography.intel.aws.ec2.vpc_peerings.transform_aws_accounts_from_vpc_peering(
            data,
        )
    )

    cartography.intel.aws.ec2.vpc_peerings.load_aws_accounts_from_vpc_peering(
        neo4j_session,
        aws_accounts,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ec2.vpc_peerings.load_vpc_nodes(
        neo4j_session,
        vpc_nodes,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ec2.vpc_peerings.load_accepter_cidrs(
        neo4j_session,
        accepter_cidrs,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ec2.vpc_peerings.load_requester_cidrs(
        neo4j_session,
        requester_cidrs,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ec2.vpc_peerings.load_vpc_peerings(
        neo4j_session,
        vpc_peerings,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "vpc-055d355d6d2e498fa|10.1.0.0/16",
            "pcx-09969456d9ec69ab6",
            "vpc-0015dc961e537676a|10.0.0.0/16",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH
        (r:AWSIpv4CidrBlock)-[:REQUESTER_CIDR]-(p:AWSPeeringConnection)-[]-(a:AWSIpv4CidrBlock)
        RETURN r.id, p.id, a.id;
        """,
    )
    actual = {(r["r.id"], r["p.id"], r["a.id"]) for r in result}

    assert actual == expected_nodes
