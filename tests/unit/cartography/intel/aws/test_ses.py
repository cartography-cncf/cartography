import pytest

from cartography.intel.aws.ses import transform_ses_identities
from cartography.intel.aws.ses import transform_ses_configuration_sets
from tests.data.aws.ses import LIST_IDENTITIES
from tests.data.aws.ses import IDENTITY_VERIFICATION_ATTRIBUTES
from tests.data.aws.ses import IDENTITY_NOTIFICATION_ATTRIBUTES
from tests.data.aws.ses import IDENTITY_DKIM_ATTRIBUTES
from tests.data.aws.ses import CONFIGURATION_SETS
from tests.data.aws.ses import TRANSFORMED_IDENTITIES
from tests.data.aws.ses import TRANSFORMED_CONFIGURATION_SETS


def test_transform_ses_identities_happy_path():
    """Test that SES identity data is correctly transformed."""
    # Arrange
    region = "us-east-1"
    account_id = "123456789012"
    
    # Combine test data to mock what would come from AWS API
    identity_attributes = {}
    for identity in LIST_IDENTITIES:
        identity_attributes[identity] = {
            "verification": IDENTITY_VERIFICATION_ATTRIBUTES.get(identity, {}),
            "notification": IDENTITY_NOTIFICATION_ATTRIBUTES.get(identity, {}),
            "dkim": IDENTITY_DKIM_ATTRIBUTES.get(identity, {}),
        }

    # Act
    transformed = transform_ses_identities(LIST_IDENTITIES, identity_attributes, region, account_id)

    # Assert
    assert len(transformed) == 3, "Should transform all 3 identities"

    # Test domain identity
    domain_identity = transformed[0]
    expected_domain = TRANSFORMED_IDENTITIES[0]
    
    assert domain_identity["IdentityArn"] == expected_domain["IdentityArn"]
    assert domain_identity["Identity"] == "example.com"
    assert domain_identity["IdentityType"] == "Domain"
    assert domain_identity["VerificationStatus"] == "Success"
    assert domain_identity["DkimEnabled"] is True
    assert domain_identity["DkimVerificationStatus"] == "Success"
    assert len(domain_identity["DkimTokens"]) == 3
    assert domain_identity["BounceTopic"] == "arn:aws:sns:us-east-1:123456789012:ses-bounces"
    assert domain_identity["ForwardingEnabled"] is True

    # Test email identity
    email_identity = transformed[1]
    expected_email = TRANSFORMED_IDENTITIES[1]
    
    assert email_identity["IdentityArn"] == expected_email["IdentityArn"]
    assert email_identity["Identity"] == "test@example.com"
    assert email_identity["IdentityType"] == "EmailAddress"
    assert email_identity["VerificationStatus"] == "Success"
    assert email_identity["DkimEnabled"] is False
    assert email_identity["DkimVerificationStatus"] == "NotStarted"
    assert email_identity["DkimTokens"] == []
    assert email_identity["BounceTopic"] == ""
    assert email_identity["ForwardingEnabled"] is True

    # Test pending email identity
    pending_identity = transformed[2]
    expected_pending = TRANSFORMED_IDENTITIES[2]
    
    assert pending_identity["IdentityArn"] == expected_pending["IdentityArn"]
    assert pending_identity["Identity"] == "noreply@testdomain.org"
    assert pending_identity["IdentityType"] == "EmailAddress"
    assert pending_identity["VerificationStatus"] == "Pending"
    assert pending_identity["ForwardingEnabled"] is False


def test_transform_ses_identities_empty_attributes():
    """Test that transform handles empty/missing attributes gracefully."""
    # Arrange
    region = "us-west-2"
    account_id = "987654321098"
    identities = ["test@example.com"]
    identity_attributes = {}  # Empty attributes

    # Act
    transformed = transform_ses_identities(identities, identity_attributes, region, account_id)

    # Assert
    assert len(transformed) == 1
    identity = transformed[0]
    
    assert identity["IdentityArn"] == "arn:aws:ses:us-west-2:987654321098:identity/test@example.com"
    assert identity["Identity"] == "test@example.com"
    assert identity["IdentityType"] == "EmailAddress"
    assert identity["VerificationStatus"] == ""
    assert identity["DkimEnabled"] is False
    assert identity["DkimVerificationStatus"] == ""
    assert identity["DkimTokens"] == []
    assert identity["BounceTopic"] == ""
    assert identity["ForwardingEnabled"] is False


def test_transform_ses_configuration_sets_happy_path():
    """Test that SES configuration set data is correctly transformed."""
    # Arrange
    region = "us-east-1"
    account_id = "123456789012"

    # Act
    transformed = transform_ses_configuration_sets(CONFIGURATION_SETS, region, account_id)

    # Assert
    assert len(transformed) == 2, "Should transform all 2 configuration sets"

    # Test first configuration set
    config_set_1 = transformed[0]
    expected_1 = TRANSFORMED_CONFIGURATION_SETS[0]
    
    assert config_set_1["ConfigurationSetArn"] == expected_1["ConfigurationSetArn"]
    assert config_set_1["Name"] == "my-configuration-set"

    # Test second configuration set
    config_set_2 = transformed[1]
    expected_2 = TRANSFORMED_CONFIGURATION_SETS[1]
    
    assert config_set_2["ConfigurationSetArn"] == expected_2["ConfigurationSetArn"]
    assert config_set_2["Name"] == "production-config-set"


def test_transform_ses_configuration_sets_empty():
    """Test that transform handles empty configuration sets list."""
    # Arrange
    region = "us-west-2"
    account_id = "987654321098"
    configuration_sets = []

    # Act
    transformed = transform_ses_configuration_sets(configuration_sets, region, account_id)

    # Assert
    assert len(transformed) == 0, "Should return empty list for empty input"


def test_identity_type_detection():
    """Test that identity type is correctly detected for various inputs."""
    # Arrange
    region = "us-east-1"
    account_id = "123456789012"
    
    test_cases = [
        ("example.com", "Domain"),
        ("subdomain.example.com", "Domain"), 
        ("test@example.com", "EmailAddress"),
        ("user+tag@subdomain.example.org", "EmailAddress"),
        ("simple", "EmailAddress"),  # Edge case - no dot or @, defaults to EmailAddress
    ]
    
    for identity, expected_type in test_cases:
        identities = [identity]
        identity_attributes = {}
        
        # Act
        transformed = transform_ses_identities(identities, identity_attributes, region, account_id)
        
        # Assert
        assert len(transformed) == 1
        assert transformed[0]["IdentityType"] == expected_type, f"Failed for identity: {identity}"
