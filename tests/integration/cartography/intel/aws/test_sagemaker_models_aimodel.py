from cartography.intel.aws.sagemaker.models import load_models
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def test_sagemaker_model_carries_aimodel_label(neo4j_session):
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    transformed_models = [
        {
            "ModelArn": (
                f"arn:aws:sagemaker:{TEST_REGION}:{TEST_ACCOUNT_ID}:model/test-model"
            ),
            "ModelName": "test-model",
            "CreationTime": "2025-01-01T00:00:00.000000+00:00",
            "ExecutionRoleArn": (
                f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/test-execution-role"
            ),
            "PrimaryContainerImage": "123.dkr.ecr.us-east-1.amazonaws.com/test:latest",
            "ModelPackageName": None,
            "ModelPackageArn": None,
            "ModelArtifactsS3BucketId": "test-bucket",
            "Region": TEST_REGION,
        }
    ]

    load_models(
        neo4j_session,
        transformed_models,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    assert check_nodes(
        neo4j_session,
        "AIModel",
        ["_ont_name", "_ont_provider", "_ont_type", "_ont_source"],
    ) == {
        ("test-model", "aws", "custom", "aws"),
    }
