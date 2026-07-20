from unittest.mock import MagicMock

import botocore.exceptions

from cartography.intel.aws import ses
from cartography.intel.aws.ses import get_ses_email_identities


def test_get_ses_email_identities_falls_back_when_not_pageable() -> None:
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    mock_client.get_paginator.side_effect = (
        botocore.exceptions.OperationNotPageableError(
            operation_name="list_email_identities",
        )
    )
    mock_client.list_email_identities.side_effect = [
        {
            "EmailIdentities": [
                {
                    "IdentityName": "example.com",
                    "IdentityType": "DOMAIN",
                    "SendingEnabled": True,
                },
            ],
            "NextToken": "token-1",
        },
        {
            "EmailIdentities": [
                {
                    "IdentityName": "user@example.com",
                    "IdentityType": "EMAIL_ADDRESS",
                    "SendingEnabled": False,
                },
            ],
        },
    ]
    mock_client.get_email_identity.side_effect = [
        {
            "VerificationStatus": "SUCCESS",
            "DkimAttributes": {"SigningEnabled": True, "Status": "SUCCESS"},
        },
        {
            "VerificationStatus": "PENDING",
            "DkimAttributes": {"SigningEnabled": False, "Status": "PENDING"},
        },
    ]

    result = get_ses_email_identities(
        mock_session,
        "us-east-1",
        "123456789012",
    )

    assert result == [
        {
            "Arn": "arn:aws:ses:us-east-1:123456789012:identity/example.com",
            "IdentityName": "example.com",
            "IdentityType": "DOMAIN",
            "SendingEnabled": True,
            "VerificationStatus": "SUCCESS",
            "DkimSigningEnabled": True,
            "DkimStatus": "SUCCESS",
        },
        {
            "Arn": "arn:aws:ses:us-east-1:123456789012:identity/user@example.com",
            "IdentityName": "user@example.com",
            "IdentityType": "EMAIL_ADDRESS",
            "SendingEnabled": False,
            "VerificationStatus": "PENDING",
            "DkimSigningEnabled": False,
            "DkimStatus": "PENDING",
        },
    ]


def test_ses_sync_skips_regions_where_sesv2_is_unsupported(mocker) -> None:
    boto3_session = MagicMock()
    boto3_session.get_partition_for_region.return_value = "aws"
    boto3_session.get_available_regions.return_value = ["us-east-1"]

    get_identities = mocker.patch(
        "cartography.intel.aws.ses.get_ses_email_identities",
        return_value=[],
    )
    load_identities = mocker.patch(
        "cartography.intel.aws.ses.load_ses_email_identities",
    )
    cleanup = mocker.patch("cartography.intel.aws.ses.cleanup")

    # eu-south-2 (Spain) has no SES endpoint, so it must be skipped.
    ses.sync(
        neo4j_session=MagicMock(),
        boto3_session=boto3_session,
        regions=["us-east-1", "eu-south-2"],
        current_aws_account_id="123456789012",
        update_tag=1,
        common_job_parameters={"UPDATE_TAG": 1, "AWS_ID": "123456789012"},
    )

    boto3_session.get_available_regions.assert_called_once_with(
        "sesv2",
        partition_name="aws",
    )
    called_regions = [call.args[1] for call in get_identities.call_args_list]
    assert called_regions == ["us-east-1"]
    assert load_identities.call_count == 1
    cleanup.assert_called_once()
