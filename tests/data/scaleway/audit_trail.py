from scaleway.audit_trail.v1alpha1 import AlertRule
from scaleway.audit_trail.v1alpha1.types import AlertRuleStatus

SCALEWAY_AUDIT_TRAIL_ALERT_RULES = [
    AlertRule(
        id="a1b2c3d4-0001-4000-8000-000000000001",
        name="critical-login-alert",
        description="Alert on critical login events",
        status=AlertRuleStatus.ENABLED,
    ),
    AlertRule(
        id="a1b2c3d4-0002-4000-8000-000000000002",
        name="api-key-usage-alert",
        description="Alert on unusual API key usage",
        status=AlertRuleStatus.DISABLED,
    ),
]
