import json
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.instances
import cartography.intel.aws.ssm
import tests.data.aws.ec2.instances
import tests.data.aws.ssm
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.integration.cartography.intel.aws.common import create_test_account

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def _ensure_load_instances(neo4j_session):
    boto3_session = MagicMock()
    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )


@patch.object(
    cartography.intel.aws.ec2.instances,
    "get_ec2_instances",
    return_value=DESCRIBE_INSTANCES["Reservations"],
)
def test_load_instance_information(mock_get_instances, neo4j_session):
    # Arrange
    # load account and instances, to be able to test relationships
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _ensure_load_instances(neo4j_session)

    # Act
    data_list = cartography.intel.aws.ssm.transform_instance_information(
        tests.data.aws.ssm.INSTANCE_INFORMATION,
    )
    cartography.intel.aws.ssm.load_instance_information(
        neo4j_session,
        data_list,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ("i-01", 1647233782, 1647233908, 1647232108),
        ("i-02", 1647233782, 1647233908, 1647232108),
    }

    nodes = neo4j_session.run(
        """
        MATCH (:AWSAccount{id: "000000000000"})-[:RESOURCE]->(n:SSMInstanceInformation)
        RETURN n.id,
               n.last_ping_date_time,
               n.last_association_execution_date,
               n.last_successful_association_execution_date
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.last_ping_date_time"],
            n["n.last_association_execution_date"],
            n["n.last_successful_association_execution_date"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

    nodes = neo4j_session.run(
        """
        MATCH (:EC2Instance{id: "i-01"})-[:HAS_INFORMATION]->(n:SSMInstanceInformation)
        RETURN n.id
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == {"i-01"}

    nodes = neo4j_session.run(
        """
        MATCH (:EC2Instance{id: "i-02"})-[:HAS_INFORMATION]->(n:SSMInstanceInformation)
        RETURN n.id
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == {"i-02"}


@patch.object(
    cartography.intel.aws.ec2.instances,
    "get_ec2_instances",
    return_value=DESCRIBE_INSTANCES["Reservations"],
)
def test_load_instance_patches(mock_get_instances, neo4j_session):
    # Arrange: load account and instances, to be able to test relationships
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _ensure_load_instances(neo4j_session)

    # Act
    data_list = cartography.intel.aws.ssm.transform_instance_patches(
        tests.data.aws.ssm.INSTANCE_PATCHES,
    )
    cartography.intel.aws.ssm.load_instance_patches(
        neo4j_session,
        data_list,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {
        (
            "i-01-test.x86_64:0:4.2.46-34.amzn2",
            1636404678,
            ("CVE-2022-0000", "CVE-2022-0001"),
        ),
        (
            "i-02-test.x86_64:0:4.2.46-34.amzn2",
            1636404678,
            ("CVE-2022-0000", "CVE-2022-0001"),
        ),
    }
    nodes = neo4j_session.run(
        """
        MATCH (:AWSAccount{id: "000000000000"})-[:RESOURCE]->(n:SSMInstancePatch)
        RETURN n.id,
               n.installed_time,
               n.cve_ids
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.installed_time"],
            tuple(n["n.cve_ids"]),
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

    # Assert
    nodes = neo4j_session.run(
        """
        MATCH (:EC2Instance{id: "i-01"})-[:HAS_PATCH]->(n:SSMInstancePatch)
        RETURN n.id
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == {"i-01-test.x86_64:0:4.2.46-34.amzn2"}

    # Assert
    nodes = neo4j_session.run(
        """
        MATCH (:EC2Instance{id: "i-02"})-[:HAS_PATCH]->(n:SSMInstancePatch)
        RETURN n.id
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == {"i-02-test.x86_64:0:4.2.46-34.amzn2"}


def test_load_ssm_parameters(neo4j_session):
    # Arrange: load account
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    ssm_param_test_data = tests.data.aws.ssm.SSM_PARAMETERS_DATA
    transformed_data = cartography.intel.aws.ssm.transform_ssm_parameters(
        ssm_param_test_data,
    )
    cartography.intel.aws.ssm.load_ssm_parameters(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert: Check SSMParameter nodes and their properties
    expected_nodes = {
        (
            "arn:aws:ssm:us-east-1:123456789012:parameter/my/app/config/db-host",
            "/my/app/config/db-host",
            "String",
            1673776800,
            "Hostname for the primary application database.",
            None,
            json.dumps([]),
        ),
        (
            "arn:aws:ssm:us-east-1:123456789012:parameter/my/secure/api-key",
            "/my/secure/api-key",
            "SecureString",
            1676903400,
            "A super secret API key.",
            "^[a-zA-Z0-9]{32}$",
            json.dumps(
                [
                    {
                        "PolicyText": '{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": "*", "Action": "ssm:GetParameter", "Resource": "*"}]}',
                        "PolicyType": "ResourceBased",
                        "PolicyStatus": "Finished",
                    }
                ]
            ),
        ),
    }

    query = """
    MATCH (p:SSMParameter)
    RETURN p.id, p.name, p.type, p.lastmodifieddate, p.description, p.allowedpattern, p.policies_json
    ORDER BY p.name // Optional: Order to make comparison easier if set iteration order isn't guaranteed
    """
    nodes = neo4j_session.run(query)
    actual_nodes = {
        (
            n["p.id"],
            n["p.name"],
            n["p.type"],
            n["p.lastmodifieddate"],
            n["p.description"],
            n["p.allowedpattern"],
            n["p.policies_json"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

    # Assert: Relationship to AWSAccount
    expected_rels_to_account = {
        (
            "arn:aws:ssm:us-east-1:123456789012:parameter/my/app/config/db-host",
            TEST_ACCOUNT_ID,
        ),
        (
            "arn:aws:ssm:us-east-1:123456789012:parameter/my/secure/api-key",
            TEST_ACCOUNT_ID,
        ),
    }
    query_account_rels = """
    MATCH (p:SSMParameter)<-[r:RESOURCE]-(a:AWSAccount{id: $AccountId})
    RETURN p.id AS ParamId, a.id AS AccountId
    ORDER BY p.id // Optional: Order for consistent comparison
    """
    rels = neo4j_session.run(query_account_rels, AccountId=TEST_ACCOUNT_ID)
    actual_rels_to_account = {(r["ParamId"], r["AccountId"]) for r in rels}
    assert actual_rels_to_account == expected_rels_to_account
