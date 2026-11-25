from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.apprunner
from cartography.intel.aws.apprunner import get_apprunner_services

SERVICE_ONE_ARN = "arn:aws:apprunner:us-east-1:123456789012:service/one/aaa"
SERVICE_TWO_ARN = "arn:aws:apprunner:us-east-1:123456789012:service/two/bbb"


@patch.object(cartography.intel.aws.apprunner, "create_boto3_client")
def test_get_apprunner_services_follows_list_services_pages(mock_create_boto3_client):
    client = MagicMock()
    mock_create_boto3_client.return_value = client
    client.list_services.side_effect = [
        {
            "ServiceSummaryList": [{"ServiceArn": SERVICE_ONE_ARN}],
            "NextToken": "page-2",
        },
        {
            "ServiceSummaryList": [{"ServiceArn": SERVICE_TWO_ARN}],
        },
    ]
    client.describe_service.side_effect = [
        {"Service": {"ServiceArn": SERVICE_ONE_ARN, "ServiceName": "one"}},
        {"Service": {"ServiceArn": SERVICE_TWO_ARN, "ServiceName": "two"}},
    ]

    result = get_apprunner_services(MagicMock(), "us-east-1")

    assert result == [
        {"ServiceArn": SERVICE_ONE_ARN, "ServiceName": "one"},
        {"ServiceArn": SERVICE_TWO_ARN, "ServiceName": "two"},
    ]
    assert client.list_services.call_count == 2
    client.list_services.assert_any_call()
    client.list_services.assert_any_call(NextToken="page-2")
    client.describe_service.assert_any_call(ServiceArn=SERVICE_ONE_ARN)
    client.describe_service.assert_any_call(ServiceArn=SERVICE_TWO_ARN)
