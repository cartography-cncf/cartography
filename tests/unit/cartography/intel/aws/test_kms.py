from cartography.intel.aws.kms import transform_kms_key_policies
from tests.data.aws.kms import ACCESS_DENIED_KMS_KEY_DETAILS


def test_transform_kms_key_policies_with_null_policy():
    """Test that KMS key policies with None values are gracefully handled."""
    # Arrange
    policy_alias_grants_data = ACCESS_DENIED_KMS_KEY_DETAILS

    # Act - This should fail initially due to NoneType error
    # After fix, this should gracefully skip keys with None policy
    result = transform_kms_key_policies(policy_alias_grants_data)

    # Assert - Keys with None policy should have default empty policy data
    assert len(result) == 2

    # First key
    key1_data = result["9a1ad414-6e3b-47ce-8366-6b8f26ba467d"]
    assert key1_data["kms_key"] == "9a1ad414-6e3b-47ce-8366-6b8f26ba467d"
    assert key1_data["anonymous_access"] is False
    assert key1_data["anonymous_actions"] == []

    # Second key
    key2_data = result["1b2cd345-7e8f-49ab-cdef-0123456789ab"]
    assert key2_data["kms_key"] == "1b2cd345-7e8f-49ab-cdef-0123456789ab"
    assert key2_data["anonymous_access"] is False
    assert key2_data["anonymous_actions"] == []
