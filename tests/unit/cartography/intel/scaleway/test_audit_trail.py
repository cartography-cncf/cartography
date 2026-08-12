from cartography.intel.scaleway.audit_trail.audit_trail import transform_alert_rules
from tests.data.scaleway.audit_trail import SCALEWAY_AUDIT_TRAIL_ALERT_RULES

PROJECTS = ["0681c477-fbb9-4820-b8d6-0eef10cfcd6d"]


def test_transform_alert_rules_attaches_to_all_projects():
    result = transform_alert_rules(SCALEWAY_AUDIT_TRAIL_ALERT_RULES, PROJECTS)
    assert "0681c477-fbb9-4820-b8d6-0eef10cfcd6d" in result
    rules = result["0681c477-fbb9-4820-b8d6-0eef10cfcd6d"]
    assert len(rules) == 2


def test_transform_alert_rules_fields():
    result = transform_alert_rules(SCALEWAY_AUDIT_TRAIL_ALERT_RULES, PROJECTS)
    rule = result["0681c477-fbb9-4820-b8d6-0eef10cfcd6d"][0]
    assert rule["id"] == "a1b2c3d4-0001-4000-8000-000000000001"
    assert rule["name"] == "critical-login-alert"
    assert rule["status"] == "enabled"


def test_transform_alert_rules_multiple_projects():
    result = transform_alert_rules(
        SCALEWAY_AUDIT_TRAIL_ALERT_RULES,
        ["proj-a", "proj-b"],
    )
    assert set(result.keys()) == {"proj-a", "proj-b"}
    assert len(result["proj-a"]) == 2
    assert len(result["proj-b"]) == 2
