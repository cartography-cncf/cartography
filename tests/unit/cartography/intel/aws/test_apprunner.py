from unittest.mock import MagicMock
from unittest.mock import patch

from botocore.exceptions import ClientError

from cartography.intel.aws.apprunner import get_apprunner_services
from cartography.intel.aws.apprunner import transform_apprunner_services
from tests.data.aws.apprunner import DESCRIBE_SERVICES


def test_transform_apprunner_services_flattens_nested_fields():
    transformed = transform_apprunner_services(DESCRIBE_SERVICES)

    by_arn = {svc["ServiceArn"]: svc for svc in transformed}

    image_svc = by_arn[
        "arn:aws:apprunner:us-east-1:123456789012:service/my-service/abc123"
    ]
    assert (
        image_svc["ImageIdentifier"]
        == "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo:latest"
    )
    assert image_svc["CodeRepositoryUrl"] is None
    assert image_svc["AccessRoleArn"] == "arn:aws:iam::1234:role/cartography-read-only"
    assert image_svc["InstanceRoleArn"] == "arn:aws:iam::1234:role/cartography-service"
    assert image_svc["Cpu"] == "1 vCPU"
    assert image_svc["Memory"] == "2 GB"
    assert image_svc["EgressType"] == "DEFAULT"
    assert image_svc["IsPubliclyAccessible"] is True
    assert image_svc["AutoDeploymentsEnabled"] is True

    code_svc = by_arn[
        "arn:aws:apprunner:us-east-1:123456789012:service/my-code-service/ghi789"
    ]
    assert code_svc["ImageIdentifier"] is None
    assert code_svc["CodeRepositoryUrl"] == "https://github.com/example/my-code-service"
    assert code_svc["AccessRoleArn"] is None
    assert code_svc["InstanceRoleArn"] == "arn:aws:iam::1234:role/cartography-service"


@patch("cartography.intel.aws.apprunner.time.sleep", return_value=None)
@patch("cartography.intel.aws.apprunner.create_boto3_client")
def test_get_apprunner_services_skips_resource_not_found(
    mock_create_boto3_client,
    _mock_sleep,
):
    client = MagicMock()
    paginator = MagicMock()
    paginator.paginate.return_value = [
        {
            "ServiceSummaryList": [
                {
                    "ServiceArn": "arn:aws:apprunner:us-east-1:123456789012:service/gone/abc",
                },
                {
                    "ServiceArn": "arn:aws:apprunner:us-east-1:123456789012:service/alive/def",
                },
            ],
        },
    ]
    client.get_paginator.return_value = paginator
    client.describe_service.side_effect = [
        ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "Service not found",
                },
            },
            "DescribeService",
        ),
        {"Service": DESCRIBE_SERVICES[0]},
    ]
    mock_create_boto3_client.return_value = client

    result = get_apprunner_services(MagicMock(), "us-east-1")

    assert result == [DESCRIBE_SERVICES[0]]
    assert client.describe_service.call_count == 2
