from cartography.intel.tailscale.postureresolution import device_matches_condition
from cartography.intel.tailscale.utils import ACLParser


def test_acl_parser_handles_case_insensitive_set_operators_and_lists() -> None:
    acl = ACLParser(
        """
        {
            "postures": {
                "posture:test": [
                    "ip:country in ['us']",
                    "custom:tier not set",
                    "custom:managed IS SET"
                ]
            }
        }
        """,
    )

    postures, conditions = acl.get_postures()

    assert postures == [
        {
            "id": "posture:test",
            "name": "test",
            "description": (
                "ip:country in ['us']; custom:tier not set; custom:managed IS SET"
            ),
            "condition_ids": [
                "posture:test:0",
                "posture:test:1",
                "posture:test:2",
            ],
        },
    ]
    assert conditions == [
        {
            "id": "posture:test:0",
            "posture_id": "posture:test",
            "name": "ip:country",
            "provider": "ip",
            "operator": "IN",
            "value": '["us"]',
        },
        {
            "id": "posture:test:1",
            "posture_id": "posture:test",
            "name": "custom:tier",
            "provider": "custom",
            "operator": "NOT SET",
            "value": None,
        },
        {
            "id": "posture:test:2",
            "posture_id": "posture:test",
            "name": "custom:managed",
            "provider": "custom",
            "operator": "IS SET",
            "value": None,
        },
    ]


def test_device_matches_condition_supports_not_set() -> None:
    condition = {
        "name": "custom:tier",
        "operator": "NOT SET",
        "value": None,
    }

    assert device_matches_condition({}, condition) is True
    assert device_matches_condition({"custom:tier": None}, condition) is True
    assert device_matches_condition({"custom:tier": "prod"}, condition) is False


def test_device_matches_condition_uses_tailscale_version_comparison() -> None:
    condition = {
        "name": "node:tsVersion",
        "operator": "<",
        "value": "1.2.3-10",
    }

    assert device_matches_condition({"node:tsVersion": "1.2.3-9"}, condition) is True
    assert device_matches_condition({"node:tsVersion": "1.2.3-11"}, condition) is False
