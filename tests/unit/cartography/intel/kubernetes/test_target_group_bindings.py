import pytest

from cartography.intel.kubernetes.target_group_bindings import (
    transform_target_group_bindings,
)

TARGET_GROUP_ARN = "arn:aws:elasticloadbalancing:us-east-1:000000000000:targetgroup/web/0123456789abcdef"


def test_transform_target_group_bindings_keeps_named_service_port():
    # Arrange
    bindings = [
        {
            "metadata": {"name": "web-binding", "namespace": "shop"},
            "spec": {
                "targetGroupARN": TARGET_GROUP_ARN,
                "targetType": "instance",
                "serviceRef": {"name": "web", "port": "http"},
            },
        },
    ]

    # Act
    result = transform_target_group_bindings(bindings, "prod-cluster")

    # Assert
    assert result == [
        {
            "target_group_arn": TARGET_GROUP_ARN,
            "cluster_name": "prod-cluster",
            "service_qualified_name": "shop/web",
            "binding_name": "web-binding",
            "target_type": "instance",
            "service_port": "http",
        },
    ]


@pytest.mark.parametrize(
    "spec",
    [
        pytest.param(
            {"targetGroupName": "web", "serviceRef": {"name": "web", "port": 80}},
            id="target-group-name-only",
        ),
        pytest.param(
            {"targetGroupARN": TARGET_GROUP_ARN, "serviceRef": {"port": 80}},
            id="no-service-name",
        ),
    ],
)
def test_transform_target_group_bindings_skips_unmatchable_bindings(spec):
    # Arrange
    bindings = [
        {"metadata": {"name": "web-binding", "namespace": "shop"}, "spec": spec}
    ]

    # Act
    result = transform_target_group_bindings(bindings, "prod-cluster")

    # Assert
    assert result == []
