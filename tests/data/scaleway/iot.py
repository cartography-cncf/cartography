from datetime import datetime

from dateutil.tz import tzutc
from scaleway.iot.v1 import Device
from scaleway.iot.v1 import DeviceStatus
from scaleway.iot.v1 import Hub
from scaleway.iot.v1 import HubProductPlan
from scaleway.iot.v1 import HubStatus

TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"

TEST_HUB_ID = "hbhbhbhb-1111-4820-b8d6-0eef10cfcd6d"
TEST_DEVICE_ID = "dvdvdvdv-1111-4820-b8d6-0eef10cfcd6d"

SCALEWAY_IOT_HUBS = [
    Hub(
        id=TEST_HUB_ID,
        name="demo-hub",
        status=HubStatus.READY,
        product_plan=HubProductPlan.PLAN_SHARED,
        enabled=True,
        device_count=1,
        connected_device_count=0,
        endpoint="demo-hub.fr-par.iot.scw.cloud",
        disable_events=False,
        events_topic_prefix=None,
        region="fr-par",
        project_id=TEST_PROJECT_ID,
        organization_id=TEST_ORG_ID,
        enable_device_auto_provisioning=False,
        has_custom_ca=False,
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        twins_graphite_config=None,
    ),
]

SCALEWAY_IOT_DEVICES = [
    Device(
        id=TEST_DEVICE_ID,
        name="demo-device",
        description="Demo device",
        status=DeviceStatus.ENABLED,
        hub_id=TEST_HUB_ID,
        is_connected=False,
        allow_insecure=False,
        allow_multiple_connections=False,
        has_custom_certificate=False,
        region="fr-par",
        last_activity_at=None,
        message_filters=None,
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    ),
]
