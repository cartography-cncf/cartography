# Test data for SES


LIST_IDENTITIES = [
    "example.com",
    "test@example.com", 
    "noreply@testdomain.org"
]

IDENTITY_VERIFICATION_ATTRIBUTES = {
    "example.com": {
        "VerificationStatus": "Success",
        "VerificationToken": "123abc456def789ghi012jkl345mno678pqr901stu234vwx567yz"
    },
    "test@example.com": {
        "VerificationStatus": "Success",
    },
    "noreply@testdomain.org": {
        "VerificationStatus": "Pending",
    }
}

IDENTITY_NOTIFICATION_ATTRIBUTES = {
    "example.com": {
        "BounceTopic": "arn:aws:sns:us-east-1:123456789012:ses-bounces",
        "ComplaintTopic": "arn:aws:sns:us-east-1:123456789012:ses-complaints",
        "DeliveryTopic": "",
        "ForwardingEnabled": True,
        "HeadersInBounceNotificationsEnabled": False,
        "HeadersInComplaintNotificationsEnabled": False,
        "HeadersInDeliveryNotificationsEnabled": False
    },
    "test@example.com": {
        "BounceTopic": "",
        "ComplaintTopic": "",
        "DeliveryTopic": "",
        "ForwardingEnabled": True,
        "HeadersInBounceNotificationsEnabled": False,
        "HeadersInComplaintNotificationsEnabled": False,
        "HeadersInDeliveryNotificationsEnabled": False
    },
    "noreply@testdomain.org": {
        "BounceTopic": "",
        "ComplaintTopic": "",
        "DeliveryTopic": "",
        "ForwardingEnabled": False,
        "HeadersInBounceNotificationsEnabled": False,
        "HeadersInComplaintNotificationsEnabled": False,
        "HeadersInDeliveryNotificationsEnabled": False
    }
}

IDENTITY_DKIM_ATTRIBUTES = {
    "example.com": {
        "DkimEnabled": True,
        "DkimVerificationStatus": "Success",
        "DkimTokens": [
            "EXAMPLEjcs5xoyqytjsotsijas7236gr",
            "EXAMPLEjr76cvoc6mysspnioorxsn6ep",
            "EXAMPLEk3newbm7ruf77a2wllnkl5ug"
        ]
    },
    "test@example.com": {
        "DkimEnabled": False,
        "DkimVerificationStatus": "NotStarted",
        "DkimTokens": []
    },
    "noreply@testdomain.org": {
        "DkimEnabled": False,
        "DkimVerificationStatus": "NotStarted", 
        "DkimTokens": []
    }
}

CONFIGURATION_SETS = [
    {
        "Name": "my-configuration-set"
    },
    {
        "Name": "production-config-set"
    }
]

# Transformed test data for testing transform functions
TRANSFORMED_IDENTITIES = [
    {
        "IdentityArn": "arn:aws:ses:us-east-1:123456789012:identity/example.com",
        "Identity": "example.com",
        "IdentityType": "Domain",
        "VerificationStatus": "Success",
        "VerificationToken": "123abc456def789ghi012jkl345mno678pqr901stu234vwx567yz",
        "DkimEnabled": True,
        "DkimVerificationStatus": "Success",
        "DkimTokens": [
            "EXAMPLEjcs5xoyqytjsotsijas7236gr",
            "EXAMPLEjr76cvoc6mysspnioorxsn6ep",
            "EXAMPLEk3newbm7ruf77a2wllnkl5ug"
        ],
        "BounceTopic": "arn:aws:sns:us-east-1:123456789012:ses-bounces",
        "ComplaintTopic": "arn:aws:sns:us-east-1:123456789012:ses-complaints",
        "DeliveryTopic": "",
        "ForwardingEnabled": True,
        "HeadersInBounceNotificationsEnabled": False,
        "HeadersInComplaintNotificationsEnabled": False,
        "HeadersInDeliveryNotificationsEnabled": False,
    },
    {
        "IdentityArn": "arn:aws:ses:us-east-1:123456789012:identity/test@example.com",
        "Identity": "test@example.com",
        "IdentityType": "EmailAddress",
        "VerificationStatus": "Success",
        "VerificationToken": "",
        "DkimEnabled": False,
        "DkimVerificationStatus": "NotStarted",
        "DkimTokens": [],
        "BounceTopic": "",
        "ComplaintTopic": "",
        "DeliveryTopic": "",
        "ForwardingEnabled": True,
        "HeadersInBounceNotificationsEnabled": False,
        "HeadersInComplaintNotificationsEnabled": False,
        "HeadersInDeliveryNotificationsEnabled": False,
    },
    {
        "IdentityArn": "arn:aws:ses:us-east-1:123456789012:identity/noreply@testdomain.org",
        "Identity": "noreply@testdomain.org",
        "IdentityType": "EmailAddress",
        "VerificationStatus": "Pending",
        "VerificationToken": "",
        "DkimEnabled": False,
        "DkimVerificationStatus": "NotStarted",
        "DkimTokens": [],
        "BounceTopic": "",
        "ComplaintTopic": "",
        "DeliveryTopic": "",
        "ForwardingEnabled": False,
        "HeadersInBounceNotificationsEnabled": False,
        "HeadersInComplaintNotificationsEnabled": False,
        "HeadersInDeliveryNotificationsEnabled": False,
    }
]

TRANSFORMED_CONFIGURATION_SETS = [
    {
        "ConfigurationSetArn": "arn:aws:ses:us-east-1:123456789012:configuration-set/my-configuration-set",
        "Name": "my-configuration-set",
    },
    {
        "ConfigurationSetArn": "arn:aws:ses:us-east-1:123456789012:configuration-set/production-config-set",
        "Name": "production-config-set",
    }
]
