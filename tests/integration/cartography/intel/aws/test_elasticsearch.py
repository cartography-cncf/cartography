import copy
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.elasticsearch
import cartography.intel.aws.route53
import cartography.intel.dns
from cartography.intel.aws.elasticsearch import sync
from tests.data.aws.elasticsearch import GET_ES_DOMAINS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789
DOMAIN_1_ID = "000000000000/test-es-domain-1"
DOMAIN_2_ID = "000000000000/test-es-domain-2"
DOMAIN_1_ENDPOINT = "search-test-es-domain-1.us-east-1.es.amazonaws.com"
DOMAIN_2_ENDPOINT = "search-test-es-domain-2.us-east-1.es.amazonaws.com"
ENDPOINT_IPS = {
    DOMAIN_1_ENDPOINT: ["192.0.2.1", "192.0.2.10"],
    DOMAIN_2_ENDPOINT: ["192.0.2.2"],
}


def test_transform_es_domains_calculates_internet_exposure():
    domains = [
        {
            "DomainId": "public-domain",
            "Endpoint": "search-public.example.com",
            "AccessPolicies": (
                '{"Version":"2012-10-17","Statement":[{"Effect":"Allow",'
                '"Principal":"*","Action":"es:*","Resource":"*"}]}'
            ),
        },
        {
            "DomainId": "private-domain",
            "Endpoint": "search-private.example.com",
            "AccessPolicies": '{"Version":"2012-10-17","Statement":[]}',
        },
    ]

    transformed = cartography.intel.aws.elasticsearch._transform_es_domains(domains)

    assert {
        domain["DomainId"]: domain["exposed_internet"] for domain in transformed
    } == {
        "public-domain": True,
        "private-domain": False,
    }


def _create_test_subnets_and_security_groups(neo4j_session):
    """Create test subnets and security groups for relationship testing."""
    neo4j_session.run(
        """
        MERGE (s:AWSEC2Subnet{id: 'subnet-11111111'})
        SET s.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (s:AWSEC2Subnet{id: 'subnet-22222222'})
        SET s.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (sg:AWSEC2SecurityGroup{id: 'sg-12345678'})
        SET sg.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )


def _sync(neo4j_session, update_tag, domains, endpoint_ips):
    with (
        patch.object(
            cartography.intel.aws.elasticsearch,
            "_get_es_domains",
            return_value=copy.deepcopy(domains),
        ),
        patch.object(
            cartography.intel.dns,
            "get_dns_resolution_by_fqdn",
            side_effect=lambda fqdn: endpoint_ips[fqdn],
        ),
        patch.object(cartography.intel.dns, "get_dns_record_type", return_value="A"),
    ):
        sync(
            neo4j_session,
            MagicMock(),
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            update_tag,
            {"UPDATE_TAG": update_tag, "AWS_ID": TEST_ACCOUNT_ID},
        )


@patch.object(
    cartography.intel.dns,
    "get_dns_resolution_by_fqdn",
    side_effect=lambda fqdn: ENDPOINT_IPS[fqdn],
)
@patch.object(cartography.intel.dns, "get_dns_record_type", return_value="A")
@patch.object(
    cartography.intel.aws.elasticsearch,
    "_get_es_domains",
    return_value=GET_ES_DOMAINS,
)
def test_sync_elasticsearch(
    mock_get_es_domains, mock_record_type, mock_resolve, neo4j_session
):
    """
    Ensure that Elasticsearch domains are synced correctly with their nodes and relationships.
    """
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _create_test_subnets_and_security_groups(neo4j_session)

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert - AWSESDomain nodes exist with key properties
    assert check_nodes(
        neo4j_session,
        "AWSESDomain",
        ["id", "elasticsearch_version", "exposed_internet"],
    ) == {
        ("000000000000/test-es-domain-1", "7.10", False),
        ("000000000000/test-es-domain-2", "6.8", False),
    }

    # Assert - Relationships (AWSAccount)-[RESOURCE]->(AWSESDomain)
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSESDomain",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "000000000000/test-es-domain-1"),
        (TEST_ACCOUNT_ID, "000000000000/test-es-domain-2"),
    }

    # Assert - Relationships (AWSESDomain)-[PART_OF_SUBNET]->(AWSEC2Subnet)
    # Only domain-1 has VPCOptions with subnets
    assert check_rels(
        neo4j_session,
        "AWSESDomain",
        "id",
        "AWSEC2Subnet",
        "id",
        "PART_OF_SUBNET",
        rel_direction_right=True,
    ) == {
        ("000000000000/test-es-domain-1", "subnet-11111111"),
        ("000000000000/test-es-domain-1", "subnet-22222222"),
    }

    # Assert - Relationships (AWSESDomain)-[MEMBER_OF_EC2_SECURITY_GROUP]->(AWSEC2SecurityGroup)
    # Only domain-1 has VPCOptions with security groups
    assert check_rels(
        neo4j_session,
        "AWSESDomain",
        "id",
        "AWSEC2SecurityGroup",
        "id",
        "MEMBER_OF_EC2_SECURITY_GROUP",
        rel_direction_right=True,
    ) == {
        ("000000000000/test-es-domain-1", "sg-12345678"),
    }

    # Assert - endpoint A records keep the shape of the legacy loader and gain ontology fields
    assert check_nodes(
        neo4j_session,
        "DNSRecord",
        ["id", "name", "type", "value", "_ont_name", "_ont_type"],
    ) == {
        (
            f"{DOMAIN_1_ENDPOINT}+A",
            DOMAIN_1_ENDPOINT,
            "A",
            "192.0.2.1,192.0.2.10",
            DOMAIN_1_ENDPOINT,
            "A",
        ),
        (
            f"{DOMAIN_2_ENDPOINT}+A",
            DOMAIN_2_ENDPOINT,
            "A",
            "192.0.2.2",
            DOMAIN_2_ENDPOINT,
            "A",
        ),
    }
    assert check_nodes(neo4j_session, "AWSDNSRecord", ["id"]) == {
        (f"{DOMAIN_1_ENDPOINT}+A",),
        (f"{DOMAIN_2_ENDPOINT}+A",),
    }
    assert check_nodes(neo4j_session, "Ip", ["id", "ip"]) == {
        ("192.0.2.1", "192.0.2.1"),
        ("192.0.2.10", "192.0.2.10"),
        ("192.0.2.2", "192.0.2.2"),
    }

    # Assert - (AWSDNSRecord)-[DNS_POINTS_TO]->(AWSESDomain) and (Ip)
    assert check_rels(
        neo4j_session,
        "AWSDNSRecord",
        "id",
        "AWSESDomain",
        "id",
        "DNS_POINTS_TO",
        rel_direction_right=True,
    ) == {
        (f"{DOMAIN_1_ENDPOINT}+A", DOMAIN_1_ID),
        (f"{DOMAIN_2_ENDPOINT}+A", DOMAIN_2_ID),
    }
    assert check_rels(
        neo4j_session,
        "AWSDNSRecord",
        "id",
        "Ip",
        "id",
        "DNS_POINTS_TO",
        rel_direction_right=True,
    ) == {
        (f"{DOMAIN_1_ENDPOINT}+A", "192.0.2.1"),
        (f"{DOMAIN_1_ENDPOINT}+A", "192.0.2.10"),
        (f"{DOMAIN_2_ENDPOINT}+A", "192.0.2.2"),
    }

    # Assert - endpoint records are not account resources, so Route53 cleanup cannot reach them
    assert (
        check_rels(
            neo4j_session,
            "AWSAccount",
            "id",
            "AWSDNSRecord",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == set()
    )


def test_sync_elasticsearch_upgrades_legacy_endpoint_record(neo4j_session):
    """The legacy loader wrote the same node without ontology fields. The data model must
    update that node in place rather than create a second one."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    neo4j_session.run(
        """
        MERGE (record:DNSRecord:AWSDNSRecord{id: $id})
        SET record.name = $name, record.type = 'A', record.value = '192.0.2.1',
            record.firstseen = 1, record.lastupdated = 1
        MERGE (ip:Ip{id: '192.0.2.1'})
        SET ip.ip = '192.0.2.1', ip.firstseen = 1, ip.lastupdated = 1
        MERGE (record)-[:DNS_POINTS_TO]->(ip)
        """,
        id=f"{DOMAIN_1_ENDPOINT}+A",
        name=DOMAIN_1_ENDPOINT,
    )

    # Act
    _sync(neo4j_session, TEST_UPDATE_TAG, GET_ES_DOMAINS[:1], ENDPOINT_IPS)

    # Assert
    assert check_nodes(
        neo4j_session,
        "AWSDNSRecord",
        ["id", "firstseen", "lastupdated", "_ont_name"],
    ) == {
        (f"{DOMAIN_1_ENDPOINT}+A", 1, TEST_UPDATE_TAG, DOMAIN_1_ENDPOINT),
    }
    assert check_nodes(neo4j_session, "Ip", ["id", "lastupdated"]) == {
        ("192.0.2.1", TEST_UPDATE_TAG),
        ("192.0.2.10", TEST_UPDATE_TAG),
    }


def test_sync_elasticsearch_cleans_up_endpoint_records(neo4j_session):
    """Stale endpoint records and stale IP edges go away, including the record of a deleted
    domain. A Route53 record that points at a domain is not the Elasticsearch sync's to clean.
    """
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _sync(neo4j_session, TEST_UPDATE_TAG, GET_ES_DOMAINS, ENDPOINT_IPS)
    route53_record_id = "/hostedzone/ZONE/search.example.com/CNAME"
    cartography.intel.aws.route53.load_cname_records(
        neo4j_session,
        [
            {
                "id": route53_record_id,
                "name": "search.example.com",
                "name_normalized": "search.example.com",
                "type": "CNAME",
                "zoneid": "/hostedzone/ZONE",
                "value": DOMAIN_1_ENDPOINT,
                "target_hostname": DOMAIN_1_ENDPOINT,
            },
        ],
        TEST_UPDATE_TAG,
        TEST_ACCOUNT_ID,
    )
    new_update_tag = TEST_UPDATE_TAG + 1

    # Act - domain 2 is deleted and domain 1 moved to a new address
    _sync(
        neo4j_session,
        new_update_tag,
        GET_ES_DOMAINS[:1],
        {DOMAIN_1_ENDPOINT: ["192.0.2.1", "192.0.2.11"]},
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSDNSRecord", ["id"]) == {
        (f"{DOMAIN_1_ENDPOINT}+A",),
        (route53_record_id,),
    }
    assert check_rels(
        neo4j_session,
        "AWSDNSRecord",
        "id",
        "Ip",
        "id",
        "DNS_POINTS_TO",
        rel_direction_right=True,
    ) == {
        (f"{DOMAIN_1_ENDPOINT}+A", "192.0.2.1"),
        (f"{DOMAIN_1_ENDPOINT}+A", "192.0.2.11"),
    }
    assert check_rels(
        neo4j_session,
        "AWSDNSRecord",
        "id",
        "AWSESDomain",
        "id",
        "DNS_POINTS_TO",
        rel_direction_right=True,
    ) == {
        (f"{DOMAIN_1_ENDPOINT}+A", DOMAIN_1_ID),
        (route53_record_id, DOMAIN_1_ID),
    }
