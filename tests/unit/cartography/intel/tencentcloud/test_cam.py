from cartography.intel.tencentcloud.cam import parse_trust_policy
from cartography.intel.tencentcloud.cam import transform_policies


def test_parse_trust_policy_separates_principals_from_services():
    # Arrange
    document = (
        '{"version":"2.0","statement":[{"action":"name/sts:AssumeRole","effect":"allow",'
        '"principal":{"qcs":["qcs::cam::uin/200000000001:root"],'
        '"service":"scf.qcloud.com"}}]}'
    )

    # Act
    principals, services = parse_trust_policy(document)

    # Assert
    assert principals == ["qcs::cam::uin/200000000001:root"]
    assert services == ["scf.qcloud.com"]


def test_parse_trust_policy_ignores_deny_statements():
    # Arrange
    document = (
        '{"version":"2.0","statement":[{"action":"name/sts:AssumeRole","effect":"deny",'
        '"principal":{"qcs":["qcs::cam::anyone"]}}]}'
    )

    # Act
    principals, services = parse_trust_policy(document)

    # Assert
    assert principals == []
    assert services == []


def test_parse_trust_policy_decodes_url_encoded_documents():
    # Arrange
    document = (
        "%7B%22version%22%3A%222.0%22%2C%22statement%22%3A%5B%7B%22effect%22%3A%22allow"
        "%22%2C%22principal%22%3A%7B%22service%22%3A%5B%22cvm.qcloud.com%22%5D%7D%7D%5D%7D"
    )

    # Act
    principals, services = parse_trust_policy(document)

    # Assert
    assert principals == []
    assert services == ["cvm.qcloud.com"]


def test_transform_policies_scopes_preset_policy_ids_to_the_account():
    # Arrange
    administrator_access = {
        "PolicyId": 1,
        "PolicyName": "AdministratorAccess",
        "PolicyType": "QCS",
    }

    # Act
    policies = transform_policies(
        account_id="100000000001",
        custom_policies=[],
        user_policies={},
        group_policies={"2001": [administrator_access]},
        role_policies={},
    )

    # Assert
    assert [(policy["id"], policy["type"]) for policy in policies] == [
        ("100000000001:1", "preset"),
    ]


def test_transform_policies_merges_attachments_of_one_policy():
    # Arrange
    custom_policy = {
        "PolicyId": 30001,
        "PolicyName": "cos-read-logs",
        "Type": 1,
        "PolicyDocument": '{"version":"2.0","statement":[]}',
    }
    attachment = {
        "PolicyId": 30001,
        "PolicyName": "cos-read-logs",
        "PolicyType": "User",
    }

    # Act
    policies = transform_policies(
        account_id="100000000001",
        custom_policies=[custom_policy],
        user_policies={"100000000012": [attachment]},
        group_policies={},
        role_policies={"4611686018427397921": [attachment]},
    )

    # Assert
    assert len(policies) == 1
    assert policies[0]["type"] == "custom"
    assert policies[0]["policy_document"] == '{"version":"2.0","statement":[]}'
    assert policies[0]["attached_user_uins"] == ["100000000012"]
    assert policies[0]["attached_role_ids"] == ["4611686018427397921"]
