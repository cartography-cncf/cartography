import copy
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.apprunner
import tests.data.aws.apprunner
from cartography.client.core.tx import run_write_query
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = tests.data.aws.apprunner.TEST_ACCOUNT_ID
TEST_REGION = tests.data.aws.apprunner.TEST_REGION
TEST_UPDATE_TAG = tests.data.aws.apprunner.TEST_UPDATE_TAG


@patch.object(
    cartography.intel.aws.apprunner,
    "get_apprunner_services",
)
def test_sync_apprunner_services(mock_get_services, neo4j_session):
    mock_get_services.return_value = copy.deepcopy(
        tests.data.aws.apprunner.DESCRIBE_SERVICES
    )

    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    run_write_query(
        neo4j_session,
        "MERGE (r:AWSRole {arn: $arn})",
        arn=f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/AppRunnerInstanceRole",
    )

    cartography.intel.aws.apprunner.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(
        neo4j_session,
        "AppRunnerService",
        ["id", "service_name", "status", "instance_role_arn"],
    ) == {
        (
            (
                f"arn:aws:apprunner:{TEST_REGION}:{TEST_ACCOUNT_ID}:service/"
                "test-service-1/service-11111111111111111"
            ),
            "test-service-1",
            "RUNNING",
            f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/AppRunnerInstanceRole",
        ),
        (
            (
                f"arn:aws:apprunner:{TEST_REGION}:{TEST_ACCOUNT_ID}:service/"
                "test-service-2/service-22222222222222222"
            ),
            "test-service-2",
            "OPERATION_IN_PROGRESS",
            None,
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AppRunnerService",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            (
                f"arn:aws:apprunner:{TEST_REGION}:{TEST_ACCOUNT_ID}:service/"
                "test-service-1/service-11111111111111111"
            ),
        ),
        (
            TEST_ACCOUNT_ID,
            (
                f"arn:aws:apprunner:{TEST_REGION}:{TEST_ACCOUNT_ID}:service/"
                "test-service-2/service-22222222222222222"
            ),
        ),
    }

    assert check_rels(
        neo4j_session,
        "AppRunnerService",
        "id",
        "AWSRole",
        "arn",
        "HAS_INSTANCE_ROLE",
        rel_direction_right=True,
    ) == {
        (
            (
                f"arn:aws:apprunner:{TEST_REGION}:{TEST_ACCOUNT_ID}:service/"
                "test-service-1/service-11111111111111111"
            ),
            f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/AppRunnerInstanceRole",
        ),
    }


def test_cleanup_apprunner_services(neo4j_session):
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    stale_service_arn = (
        f"arn:aws:apprunner:{TEST_REGION}:{TEST_ACCOUNT_ID}:service/"
        "stale-service/service-00000000000000000"
    )
    stale_service_data = [
        {
            "ServiceArn": stale_service_arn,
            "ServiceId": "service-00000000000000000",
            "ServiceName": "stale-service",
            "ServiceUrl": "stale-service.us-east-1.awsapprunner.com",
            "Status": "RUNNING",
            "InstanceRoleArn": None,
            "Region": TEST_REGION,
        },
    ]
    cartography.intel.aws.apprunner.load_apprunner_services(
        neo4j_session,
        stale_service_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    pre = neo4j_session.run(
        "MATCH (s:AppRunnerService {id: $id}) RETURN s",
        id=stale_service_arn,
    ).data()
    assert len(pre) == 1

    cartography.intel.aws.apprunner.cleanup(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "AWS_ID": TEST_ACCOUNT_ID},
    )

    post = neo4j_session.run(
        "MATCH (s:AppRunnerService {id: $id}) RETURN s",
        id=stale_service_arn,
    ).data()
    assert len(post) == 0
