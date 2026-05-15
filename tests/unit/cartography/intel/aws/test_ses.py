from unittest.mock import MagicMock

import botocore.exceptions

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
