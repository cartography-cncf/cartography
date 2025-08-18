# Test data for SES


LIST_IDENTITIES = ["example.com", "test@example.com", "noreply@testdomain.org"]

IDENTITY_VERIFICATION_ATTRIBUTES = {
    "example.com": {
        "VerificationStatus": "Success",
    },
    "test@example.com": {
        "VerificationStatus": "Success",
    },
    "noreply@testdomain.org": {
        "VerificationStatus": "Pending",
    },
}

IDENTITY_NOTIFICATION_ATTRIBUTES = {
    "example.com": {
        "BounceTopic": "arn:aws:sns:us-east-1:123456789012:ses-bounces",
        "ComplaintTopic": "arn:aws:sns:us-east-1:123456789012:ses-complaints",
        "DeliveryTopic": "",
        "ForwardingEnabled": True,
        "HeadersInBounceNotificationsEnabled": False,
        "HeadersInComplaintNotificationsEnabled": False,
        "HeadersInDeliveryNotificationsEnabled": False,
    },
    "test@example.com": {
        "BounceTopic": "",
        "ComplaintTopic": "",
        "DeliveryTopic": "",
        "ForwardingEnabled": True,
        "HeadersInBounceNotificationsEnabled": False,
        "HeadersInComplaintNotificationsEnabled": False,
        "HeadersInDeliveryNotificationsEnabled": False,
    },
    "noreply@testdomain.org": {
        "BounceTopic": "",
        "ComplaintTopic": "",
        "DeliveryTopic": "",
        "ForwardingEnabled": False,
        "HeadersInBounceNotificationsEnabled": False,
        "HeadersInComplaintNotificationsEnabled": False,
        "HeadersInDeliveryNotificationsEnabled": False,
    },
}

IDENTITY_DKIM_ATTRIBUTES = {
    "example.com": {},
    "test@example.com": {},
    "noreply@testdomain.org": {},
}

CONFIGURATION_SETS = [
    {"Name": "my-configuration-set"},
    {"Name": "production-config-set"},
]

# Transformed test data for testing transform functions
TRANSFORMED_IDENTITIES = [
    {
        "IdentityArn": "carto:ses:identity:us-east-1:123456789012:example.com",
        "Identity": "example.com",
        "IdentityType": "Domain",
        "VerificationStatus": "Success",
        "BounceTopic": "arn:aws:sns:us-east-1:123456789012:ses-bounces",
        "ComplaintTopic": "arn:aws:sns:us-east-1:123456789012:ses-complaints",
        "DeliveryTopic": "",
        "ForwardingEnabled": True,
        "HeadersInBounceNotificationsEnabled": False,
        "HeadersInComplaintNotificationsEnabled": False,
        "HeadersInDeliveryNotificationsEnabled": False,
    },
    {
        "IdentityArn": "carto:ses:identity:us-east-1:123456789012:test@example.com",
        "Identity": "test@example.com",
        "IdentityType": "EmailAddress",
        "VerificationStatus": "Success",
        "BounceTopic": "",
        "ComplaintTopic": "",
        "DeliveryTopic": "",
        "ForwardingEnabled": True,
        "HeadersInBounceNotificationsEnabled": False,
        "HeadersInComplaintNotificationsEnabled": False,
        "HeadersInDeliveryNotificationsEnabled": False,
    },
    {
        "IdentityArn": "carto:ses:identity:us-east-1:123456789012:noreply@testdomain.org",
        "Identity": "noreply@testdomain.org",
        "IdentityType": "EmailAddress",
        "VerificationStatus": "Pending",
        "BounceTopic": "",
        "ComplaintTopic": "",
        "DeliveryTopic": "",
        "ForwardingEnabled": False,
        "HeadersInBounceNotificationsEnabled": False,
        "HeadersInComplaintNotificationsEnabled": False,
        "HeadersInDeliveryNotificationsEnabled": False,
    },
]

TRANSFORMED_CONFIGURATION_SETS = [
    {
        "ConfigurationSetId": "carto:ses:configset:us-east-1:123456789012:my-configuration-set",
        "Name": "my-configuration-set",
    },
    {
        "ConfigurationSetId": "carto:ses:configset:us-east-1:123456789012:production-config-set",
        "Name": "production-config-set",
    },
]
