import cartography.intel.aws.route53
import cartography.util
import tests.data.aws.ec2.elastic_ip_addresses
import tests.data.aws.ec2.load_balancers
import tests.data.aws.route53
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ZONE_ID = "TESTZONEID"
TEST_ZONE_NAME = "TESTZONENAME"
TEST_AWS_ACCOUNTID = "AWSID"
TEST_AWS_REGION = "us-east-1"


def _ensure_local_neo4j_has_test_route53_records(neo4j_session):
    """
    Populate graph with fake paths
    (:AWSAccount)--(:AWSDNSZone)--(:AWSDNSRecord),
    (:AWSDNSZone)--(:NameServer),
    (:AWSDNSRecord{type:"NS"})-[:DNS_POINTS_TO]->(:NameServer),
    (:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSDNSRecord),
    (:AWSDNSZone)-[:SUBZONE]->(:AWSDNSZone)
    based on fake data.
    """
    neo4j_session.run(
        """
        MERGE (a:AWSAccount{id:$AccountId})
        SET a.lastupdated=$UpdateTag
        """,
        AccountId=TEST_AWS_ACCOUNTID,
        UpdateTag=TEST_UPDATE_TAG,
    )
    cartography.intel.aws.route53.load_dns_details(
        neo4j_session,
        tests.data.aws.route53.GET_ZONES_SAMPLE_RESPONSE,
        TEST_AWS_ACCOUNTID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.route53.link_sub_zones(
        neo4j_session, TEST_UPDATE_TAG, TEST_AWS_ACCOUNTID
    )


def _ensure_local_neo4j_has_test_ec2_records(neo4j_session):
    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2s(
        neo4j_session,
        tests.data.aws.ec2.load_balancers.LOAD_BALANCER_DATA,
        TEST_AWS_REGION,
        TEST_AWS_ACCOUNTID,
        TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_test_elasticip_records(neo4j_session):
    """Ensure that the test ElasticIP records are loaded in the database."""
    data = tests.data.aws.ec2.elastic_ip_addresses.GET_ELASTIC_IP_ADDRESSES
    cartography.intel.aws.ec2.elastic_ip_addresses.load_elastic_ip_addresses(
        neo4j_session,
        data,
        TEST_AWS_REGION,
        TEST_AWS_ACCOUNTID,
        TEST_UPDATE_TAG,
    )


def test_transform_and_load_ns(neo4j_session):
    # Test that NS records can be parsed and loaded
    data = tests.data.aws.route53.NS_RECORD
    parsed_data = cartography.intel.aws.route53.transform_ns_record_set(
        data,
        TEST_ZONE_ID,
    )
    assert "ns-856.awsdns-43.net" in parsed_data["servers"]
    cartography.intel.aws.route53.load_ns_records(
        neo4j_session,
        [parsed_data],
        TEST_ZONE_NAME,
        TEST_UPDATE_TAG,
    )


def test_transform_and_load_zones(neo4j_session):
    # Test that zones are being added by zone id
    data = tests.data.aws.route53.ZONE_RECORDS

    for zone in data:
        parsed_zone = cartography.intel.aws.route53.transform_zone(zone)
        cartography.intel.aws.route53.load_zones(
            neo4j_session,
            [parsed_zone],
            TEST_AWS_ACCOUNTID,
            TEST_UPDATE_TAG,
        )
    result = neo4j_session.run("MATCH (n:AWSDNSZone) RETURN count(n) as zonecount")
    for r in result:
        assert r["zonecount"] == 2


def test_transform_and_load_cname_records(neo4j_session):
    # Test that CNAME records are correctly transformed and loaded
    data = tests.data.aws.route53.CNAME_RECORD
    first_data = cartography.intel.aws.route53.transform_record_set(
        data,
        TEST_ZONE_ID,
        data["Name"][:-1],
    )
    cartography.intel.aws.route53.load_cname_records(
        neo4j_session,
        [first_data],
        TEST_UPDATE_TAG,
        TEST_AWS_ACCOUNTID,
    )

    second_data = cartography.intel.aws.route53.transform_record_set(
        data,
        TEST_ZONE_ID + "2",
        data["Name"][:-1],
    )
    cartography.intel.aws.route53.load_cname_records(
        neo4j_session,
        [second_data],
        TEST_UPDATE_TAG,
        TEST_AWS_ACCOUNTID,
    )
    result = neo4j_session.run(
        "MATCH (n:AWSDNSRecord{name:'subdomain.lyft.com'}) return count(n) as recordcount",
    )
    for r in result:
        assert r["recordcount"] == 2


def test_transform_and_load_ns_records(neo4j_session):
    # Test that NS records are correctly transformed and loaded
    data = tests.data.aws.route53.NS_RECORD
    first_data = [
        cartography.intel.aws.route53.transform_ns_record_set(data, TEST_ZONE_ID),
    ]
    cartography.intel.aws.route53.load_ns_records(
        neo4j_session,
        first_data,
        TEST_ZONE_NAME,
        TEST_UPDATE_TAG,
    )

    second_data = [
        cartography.intel.aws.route53.transform_ns_record_set(data, TEST_ZONE_ID + "2"),
    ]
    cartography.intel.aws.route53.load_ns_records(
        neo4j_session,
        second_data,
        TEST_ZONE_NAME,
        TEST_UPDATE_TAG,
    )
    result = neo4j_session.run(
        "MATCH (n:AWSDNSRecord{name:'testdomain.net'}) return count(n) as recordcount",
    )
    for r in result:
        assert r["recordcount"] == 2


def test_load_dnspointsto_ec2_relationships(neo4j_session):
    """
    1. Load DNS and EC2 resources
    2. Ensure that the expected :DNS_POINTS_TO relationships have been created
    """
    # EC2 resources must be loaded first; it's the Route53 module that links DNS to EC2 resources.
    _ensure_local_neo4j_has_test_ec2_records(neo4j_session)
    _ensure_local_neo4j_has_test_route53_records(neo4j_session)

    # Verify that the expected DNS record points to the expected ELBv2
    result = neo4j_session.run(
        """
        MATCH (n:AWSDNSRecord{id:"/hostedzone/HOSTED_ZONE/elbv2.example.com/ALIAS"})
        -[:DNS_POINTS_TO]->(l:LoadBalancerV2{id:"myawesomeloadbalancer.amazonaws.com"})
        return n.name, l.name
        """,
    )
    expected = {("elbv2.example.com", "myawesomeloadbalancer")}
    actual = {(r["n.name"], r["l.name"]) for r in result}
    assert actual == expected


def test_cleanup_dnspointsto_relationships(neo4j_session):
    # Arrange: load dns resources with update tag of TEST_UPDATE_TAG
    _ensure_local_neo4j_has_test_route53_records(neo4j_session)
    # Have one DNS record point to another object.
    # This is to simulate having a DNS record pointing to a node that was synced in another module.
    neo4j_session.run(
        """
        MERGE (n1:AWSDNSRecord{id:"/hostedzone/HOSTED_ZONE/example.com/NS", lastupdated:$UpdateTag})
        -[:DNS_POINTS_TO{lastupdated:$UpdateTag}]->
        (:NewTestAsset{name:"hello", lastupdated:$UpdateTag})
        """,
        UpdateTag=TEST_UPDATE_TAG,
    )
    # Imagine it's a new sync run so we set a new update tag
    new_update_tag = 1337

    # Act: Run all cleanup jobs where DNS_POINTS_TO is mentioned in the AWS sync.
    cartography.intel.aws.route53.cleanup_route53(
        neo4j_session,
        TEST_AWS_ACCOUNTID,
        new_update_tag,
    )
    cartography.intel.aws.elasticsearch.cleanup(
        neo4j_session,
        update_tag=new_update_tag,
        aws_account_id=TEST_AWS_ACCOUNTID,
    )

    # Assert: Verify that the AWSDNSRecord-->AWSDNSRecord relationships don't exist anymore
    result = neo4j_session.run(
        """
        MATCH (n1:AWSDNSRecord{id:"/hostedzone/HOSTED_ZONE/example.com/NS"})-[r:DNS_POINTS_TO]->(n2:AWSDNSRecord)
        RETURN count(n2) as recordcount
        """,
    )
    for r in result:
        assert r["recordcount"] == 0

    # Assert: Verify that the AWSDNSRecord-->NewTestAsset relationship still exists
    result = neo4j_session.run(
        """
        MATCH (n1:AWSDNSRecord{id:"/hostedzone/HOSTED_ZONE/example.com/NS"})-[:DNS_POINTS_TO]->(n2:NewTestAsset)
        RETURN n1.id, n2.name
        """,
    )
    actual = {(r["n1.id"], r["n2.name"]) for r in result}
    expected = {("/hostedzone/HOSTED_ZONE/example.com/NS", "hello")}
    assert actual == expected


def test_load_dnspointsto_elasticip_relationships(neo4j_session):
    """
    1. Start with a clean database
    2. Load DNS and ElasticIP resources
    3. Ensure that the expected :DNS_POINTS_TO relationships have been created
    """

    # Start with a clean db
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    cartography.intel.aws.ec2.elastic_ip_addresses.load_elastic_ip_addresses(
        neo4j_session,
        tests.data.aws.ec2.elastic_ip_addresses.GET_ELASTIC_IP_ADDRESSES,
        TEST_AWS_REGION,
        TEST_AWS_ACCOUNTID,
        TEST_UPDATE_TAG,
    )

    cartography.intel.aws.route53.load_dns_details(
        neo4j_session,
        tests.data.aws.route53.ELASTIC_IP_RELATIONSHIP_TEST_RECORDS,
        TEST_AWS_ACCOUNTID,
        TEST_UPDATE_TAG,
    )

    # Verify that the expected DNS record points to the expected ElasticIP using check_rels
    from tests.integration.util import check_rels

    actual = check_rels(
        neo4j_session,
        "AWSDNSRecord",
        "name",
        "ElasticIPAddress",
        "public_ip",
        "DNS_POINTS_TO",
        rel_direction_right=True,
    )
    expected = {("hello.what.example.com", "192.168.1.1")}
    assert actual == expected


def test_link_sub_zones_handles_cycles(neo4j_session):
    """
    Test that link_sub_zones correctly creates a valid [:SUBZONE] relationship
    but does NOT create an incorrect one between unrelated zones that share a name server.
    """
    # Arrange: Create the AWSAccount node that the link_sub_zones query depends on.
    neo4j_session.run(
        """
        MERGE (a:AWSAccount{id:$AccountId})
        SET a.lastupdated=$UpdateTag
        """,
        AccountId=TEST_AWS_ACCOUNTID,
        UpdateTag=TEST_UPDATE_TAG,
    )

    # Arrange: Load the test DNS data. This will now correctly link to the account created above.
    cartography.intel.aws.route53.load_dns_details(
        neo4j_session,
        tests.data.aws.route53.GET_ZONES_FOR_CYCLE_TEST,
        TEST_AWS_ACCOUNTID,
        TEST_UPDATE_TAG,
    )

    # Act: Run the subzone linking function that contains the fix.
    cartography.intel.aws.route53.link_sub_zones(
        neo4j_session,
        TEST_UPDATE_TAG,
        TEST_AWS_ACCOUNTID,
    )

    # Assert: Verify the graph state is correct after the run.
    # This single check verifies that the correct relationship `(example.com)->[:SUBZONE]->(sub.example.com)` exists
    # and that no incorrect relationships (e.g. to 'unrelated.io') exist.
    expected = {("example.com", "sub.example.com")}
    actual = check_rels(
        neo4j_session,
        "AWSDNSZone",
        "name",
        "AWSDNSZone",
        "name",
        "SUBZONE",
        rel_direction_right=True,
    )
    assert actual == expected
