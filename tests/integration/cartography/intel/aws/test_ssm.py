import json
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.instances
import cartography.intel.aws.kms
import cartography.intel.aws.ssm
import tests.data.aws.ec2.instances
import tests.data.aws.kms
import tests.data.aws.ssm
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_REGION_FOR_KMS = "eu-west-1"
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


def _ensure_local_neo4j_has_test_kms_keys(neo4j_session):
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    kms_keys_data = tests.data.aws.kms.DESCRIBE_KEYS
    cartography.intel.aws.kms.load_kms_keys(
        neo4j_session,
        kms_keys_data,
        TEST_REGION_FOR_KMS,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
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


@patch.object(cartography.intel.aws.ssm, "get_instance_ids", return_value=[])
@patch.object(cartography.intel.aws.ssm, "get_instance_information", return_value=[])
@patch.object(cartography.intel.aws.ssm, "get_instance_patches", return_value=[])
@patch.object(
    cartography.intel.aws.ssm,
    "get_ssm_parameters",
    return_value=tests.data.aws.ssm.SSM_PARAMETERS_DATA,
)
def test_load_ssm_parameters(
    mock_get_ssm_parameters,
    mock_get_instance_patches,
    mock_get_instance_information,
    mock_get_instance_ids,
    neo4j_session,
):
    # Arrange
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    _ensure_local_neo4j_has_test_kms_keys(neo4j_session)

    # Act
    mock_boto3_session = MagicMock()
    common_params = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AWS_ID": TEST_ACCOUNT_ID,
    }
    cartography.intel.aws.ssm.sync(
        neo4j_session,
        mock_boto3_session,
        [TEST_REGION_FOR_KMS],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_params,
    )

    # Assert: Check SSMParameter nodes and their properties
    expected_ssm_parameter_data = {
        (
            "arn:aws:ssm:eu-west-1:000000000000:parameter/my/app/config/db-host",
            "/my/app/config/db-host",
            "SecureString",
            1673776800,
            "Hostname for the primary application database.",
            "^[a-zA-Z0-9.-]+$",
            json.dumps(
                [
                    {
                        "PolicyText": '{"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Principal": "*", "Action": "ssm:DeleteParameter", "Resource": "*"}]}',
                        "PolicyType": "ResourceBased",
                        "PolicyStatus": "Finished",
                    },
                ]
            ),
            TEST_REGION_FOR_KMS,
            TEST_UPDATE_TAG,
        ),
        (
            "arn:aws:ssm:eu-west-1:000000000000:parameter/my/secure/api-key",
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
            TEST_REGION_FOR_KMS,
            TEST_UPDATE_TAG,
        ),
    }

    actual_ssm_parameter_data = check_nodes(
        neo4j_session,
        "SSMParameter",
        [
            "id",
            "name",
            "type",
            "lastmodifieddate",
            "description",
            "allowedpattern",
            "policies_json",
            "region",
            "lastupdated",
        ],
    )
    assert actual_ssm_parameter_data == expected_ssm_parameter_data

    # Assert: Check SSMParameter to AWSAccount relationships (RESOURCE)
    expected_rels_account_to_ssm = {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:ssm:eu-west-1:000000000000:parameter/my/app/config/db-host",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:ssm:eu-west-1:000000000000:parameter/my/secure/api-key",
        ),
    }
    actual_rels_account_to_ssm = check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "SSMParameter",
        "id",
        "RESOURCE",
        True,
    )
    assert actual_rels_account_to_ssm == expected_rels_account_to_ssm

    # Assert: Check SSMParameter to KMSKey relationships (ENCRYPTED_BY)
    expected_rels_ssm_to_kms = {
        (
            "arn:aws:ssm:eu-west-1:000000000000:parameter/my/app/config/db-host",
            "9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        ),
        (
            "arn:aws:ssm:eu-west-1:000000000000:parameter/my/secure/api-key",
            "9a1ad414-6e3b-47ce-8366-6b8f28bc777g",
        ),
    }
    actual_rels_ssm_to_kms = check_rels(
        neo4j_session,
        "SSMParameter",
        "id",
        "KMSKey",
        "id",
        "ENCRYPTED_BY",
        True,
    )
    assert actual_rels_ssm_to_kms == expected_rels_ssm_to_kms
