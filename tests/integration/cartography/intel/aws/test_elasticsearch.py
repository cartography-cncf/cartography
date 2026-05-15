from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.elasticsearch
from cartography.intel.aws.elasticsearch import sync
from tests.data.aws.elasticsearch import GET_ES_DOMAINS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def _create_test_subnets_and_security_groups(neo4j_session):
    """Create test subnets and security groups for relationship testing."""
    neo4j_session.run(
        """
        MERGE (s:EC2Subnet{id: 'subnet-11111111'})
        SET s.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (s:EC2Subnet{id: 'subnet-22222222'})
        SET s.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (sg:EC2SecurityGroup{id: 'sg-12345678'})
        SET sg.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )


@patch("cartography.intel.aws.elasticsearch.ingest_dns_record_by_fqdn")
@patch.object(
    cartography.intel.aws.elasticsearch,
    "_get_es_domains",
    return_value=GET_ES_DOMAINS,
)
def test_sync_elasticsearch(mock_get_es_domains, mock_dns_ingest, neo4j_session):
    """
    Ensure that Elasticsearch domains are synced correctly with their nodes and relationships.
    """
    # Arrange
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

    # Assert - ESDomain nodes exist with key properties
    assert check_nodes(
        neo4j_session,
        "ESDomain",
        ["id", "elasticsearch_version"],
    ) == {
        ("000000000000/test-es-domain-1", "7.10"),
        ("000000000000/test-es-domain-2", "6.8"),
    }

    # Assert - Relationships (AWSAccount)-[RESOURCE]->(ESDomain)
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "ESDomain",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "000000000000/test-es-domain-1"),
        (TEST_ACCOUNT_ID, "000000000000/test-es-domain-2"),
    }

    # Assert - Relationships (ESDomain)-[PART_OF_SUBNET]->(EC2Subnet)
    # Only domain-1 has VPCOptions with subnets
    assert check_rels(
        neo4j_session,
        "ESDomain",
        "id",
        "EC2Subnet",
        "id",
        "PART_OF_SUBNET",
        rel_direction_right=True,
    ) == {
        ("000000000000/test-es-domain-1", "subnet-11111111"),
        ("000000000000/test-es-domain-1", "subnet-22222222"),
    }

    # Assert - Relationships (ESDomain)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    # Only domain-1 has VPCOptions with security groups
    assert check_rels(
        neo4j_session,
        "ESDomain",
        "id",
        "EC2SecurityGroup",
        "id",
        "MEMBER_OF_EC2_SECURITY_GROUP",
        rel_direction_right=True,
    ) == {
        ("000000000000/test-es-domain-1", "sg-12345678"),
    }
