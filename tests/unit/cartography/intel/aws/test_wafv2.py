from cartography.intel.aws.wafv2 import transform_rule_groups
from cartography.intel.aws.wafv2 import transform_web_acls


def test_wafv2_transforms_pass_through():
    # Arrange
    data = [{"Id": "123", "Name": "Test"}]
    # Act
    web_acls = transform_web_acls(data)
    rule_groups = transform_rule_groups(data)
    # Assert
    assert web_acls == data
    assert rule_groups == data
