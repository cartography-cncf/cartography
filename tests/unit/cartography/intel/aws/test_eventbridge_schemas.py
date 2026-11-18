from unittest.mock import MagicMock

from cartography.intel.aws.eventbridge_schemas import get_event_schema_registries
from cartography.intel.aws.eventbridge_schemas import transform_event_schema_registries


def test_get_event_schema_registries_describes_every_page_without_a_scope_filter():
    described = {
        "aws.events": {
            "RegistryName": "aws.events",
            "RegistryArn": "arn:aws:schemas:us-east-1:aws:registry/aws.events",
            "Description": "Contains the schemas for AWS events.",
        },
        "custom-registry": {
            "RegistryName": "custom-registry",
            "RegistryArn": "arn:aws:schemas:us-east-1:123456789012:registry/custom-registry",
            "Description": "Application events",
            "Tags": {"env": "prod"},
        },
    }
    client = MagicMock()
    client.get_paginator.return_value.paginate.return_value = [
        {"Registries": [{"RegistryName": "aws.events"}]},
        {"Registries": [{"RegistryName": "custom-registry"}]},
    ]
    client.describe_registry.side_effect = lambda RegistryName: described[RegistryName]
    session = MagicMock()
    session.client.return_value = client

    result = get_event_schema_registries(session, "us-east-1")

    assert result == [
        described["aws.events"],
        described["custom-registry"],
    ]
    client.get_paginator.assert_called_once_with("list_registries")
    client.get_paginator.return_value.paginate.assert_called_once_with()
    assert client.describe_registry.call_args_list == [
        ((), {"RegistryName": "aws.events"}),
        ((), {"RegistryName": "custom-registry"}),
    ]


def test_transform_event_schema_registries_serializes_tags():
    transformed = transform_event_schema_registries(
        [
            {
                "RegistryName": "aws.events",
                "RegistryArn": "arn:aws:schemas:us-east-1:aws:registry/aws.events",
                "Description": "Contains the schemas for AWS events.",
                "ResponseMetadata": {"HTTPStatusCode": 200},
            },
            {
                "RegistryName": "custom-registry",
                "RegistryArn": "arn:aws:schemas:us-east-1:123456789012:registry/custom-registry",
                "Description": "Application events",
                "Tags": {"env": "prod"},
            },
        ],
    )

    assert transformed == [
        {
            "RegistryArn": "arn:aws:schemas:us-east-1:aws:registry/aws.events",
            "RegistryName": "aws.events",
            "Description": "Contains the schemas for AWS events.",
            "Tags": None,
        },
        {
            "RegistryArn": "arn:aws:schemas:us-east-1:123456789012:registry/custom-registry",
            "RegistryName": "custom-registry",
            "Description": "Application events",
            "Tags": '{"env": "prod"}',
        },
    ]
