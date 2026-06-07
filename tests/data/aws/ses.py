GET_EMAIL_IDENTITIES = [
    {
        "Arn": "arn:aws:ses:us-east-1:000000000000:identity/example.com",
        "IdentityName": "example.com",
        "IdentityType": "DOMAIN",
        "SendingEnabled": True,
        "VerificationStatus": "SUCCESS",
        "DkimSigningEnabled": True,
        "DkimStatus": "SUCCESS",
    },
    {
        "Arn": "arn:aws:ses:us-east-1:000000000000:identity/user@example.com",
        "IdentityName": "user@example.com",
        "IdentityType": "EMAIL_ADDRESS",
        "SendingEnabled": True,
        "VerificationStatus": "SUCCESS",
        "DkimSigningEnabled": False,
        "DkimStatus": "NOT_STARTED",
    },
    {
        "Arn": "arn:aws:ses:us-east-1:000000000000:identity/pending.io",
        "IdentityName": "pending.io",
        "IdentityType": "DOMAIN",
        "SendingEnabled": False,
        "VerificationStatus": "PENDING",
        "DkimSigningEnabled": False,
        "DkimStatus": "PENDING",
    },
]
