from cartography.intel.aws import iam

SINGLE_STATEMENT = {
    "Resource": "*",
    "Action": "*",
}

# Example principal field in an AWS policy statement
# see: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_principal.html
SINGLE_PRINCIPAL = {
    "AWS": "test-role-1",
    "Service": ["test-service-1", "test-service-2"],
    "Federated": "test-provider-1",
}


def test__generate_policy_statements():
    statements = iam._transform_policy_statements(SINGLE_STATEMENT, "test_policy_id")
    assert isinstance(statements, list)
    assert isinstance(statements[0]["Action"], list)
    assert isinstance(statements[0]["Resource"], list)
    assert statements[0]["id"] == "test_policy_id/statement/1"


def test__parse_principal_entries():
    principal_entries = iam._parse_principal_entries(SINGLE_PRINCIPAL)
    assert isinstance(principal_entries, list)
    assert len(principal_entries) == 4
    assert principal_entries[0] == ("AWS", "test-role-1")
    assert principal_entries[1] == ("Service", "test-service-1")
    assert principal_entries[2] == ("Service", "test-service-2")
    assert principal_entries[3] == ("Federated", "test-provider-1")


def test_get_account_from_arn():
    result = iam.get_account_from_arn("arn:aws:iam::081157660428:role/TestRole")
    assert result == "081157660428"


def test_aws_role_managed_type():
    # Roles AWS reserves for itself are predefined.
    assert iam._aws_role_managed_type("/aws-service-role/access-analyzer.amazonaws.com/") == "predefined"
    assert iam._aws_role_managed_type("/service-role/") == "predefined"
    assert iam._aws_role_managed_type("/aws-reserved/sso.amazonaws.com/") == "predefined"
    # Ordinary customer roles live at "/" or a custom path.
    assert iam._aws_role_managed_type("/") == "custom"
    assert iam._aws_role_managed_type("") == "custom"
    assert iam._aws_role_managed_type(None) == "custom"


def test_aws_policy_managed_type():
    # AWS-managed policy ARNs use the reserved aws account segment.
    assert iam._aws_policy_managed_type("arn:aws:iam::aws:policy/AdministratorAccess") == "predefined"
    # Customer-managed policy ARNs carry the customer account id.
    assert iam._aws_policy_managed_type("arn:aws:iam::000000000000:policy/my-policy") == "custom"
    assert iam._aws_policy_managed_type("") == "custom"


def test_transform_policies_data_sets_managed_type():
    policies = [
        {"PolicyName": "AdministratorAccess", "Arn": "arn:aws:iam::aws:policy/AdministratorAccess"},
        {"PolicyName": "my-policy", "Arn": "arn:aws:iam::000000000000:policy/my-policy"},
    ]
    result = iam.transform_policies_data("000000000000", policies)
    assert result[0]["managed_type"] == "predefined"
    assert result[1]["managed_type"] == "custom"
