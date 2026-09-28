"""Shapes returned by the compute-related adapter helpers.

Field values mirror responses captured from a real Modal workspace on modal 1.5.3.
"""

from datetime import datetime
from datetime import timezone

TEST_APP_ID = "ap-7fkFcwJ6OVd57wM78ERlH1"
TEST_STOPPED_APP_ID = "ap-2BnMqWeRtYuIoPaSdFgHjK"
TEST_CLASS_ID = "cs-35B2OoyjwFlvFPNjBMCrPK"
TEST_IMAGE_ID = "im-m0JhBY9qYlH5iisTrhhftT"
TEST_SANDBOX_ID = "sb-iSd0kw3efjqPw0yPVelPit"
TEST_CLUSTER_ID = "cl-7YhNjUmIkOlPaQsWdEfRgT"

# cartography.intel.modal.util.list_apps()
MODAL_APPS = [
    {
        "id": TEST_APP_ID,
        "name": "cartography-e2e-app",
        "description": "cartography-e2e-app",
        "state": "APP_STATE_DEPLOYED",
        "created_at": datetime(2026, 7, 29, 21, 37, 56, tzinfo=timezone.utc),
        "stopped_at": None,
        "n_running_tasks": 2,
    },
    {
        # An ephemeral app has no name, only a description.
        "id": TEST_STOPPED_APP_ID,
        "name": None,
        "description": "one-off job",
        "state": "APP_STATE_STOPPED",
        "created_at": datetime(2026, 7, 28, 10, 0, 0, tzinfo=timezone.utc),
        "stopped_at": datetime(2026, 7, 28, 10, 5, 0, tzinfo=timezone.utc),
        "n_running_tasks": 0,
    },
]

# cartography.intel.modal.util.get_app_layout(), keyed by app id
MODAL_APP_LAYOUTS = {
    TEST_APP_ID: {
        "functions": [
            {
                "id": "fu-Z8U7DHNMEog5ogYErpRIW8",
                "name": "plain_function",
                "app_id": TEST_APP_ID,
                # A non-web function: no URL.
                "web_url": None,
                "is_web_endpoint": False,
                "function_type": "FUNCTION_TYPE_FUNCTION",
                "is_method": False,
                "definition_id": None,
                "input_plane_url": "https://input-plane.us-east.modal.com:443",
                "input_plane_region": "us-east",
            },
            {
                "id": "fu-fIcWoJkWsn7vpPO8klfds5",
                "name": "web_endpoint",
                "app_id": TEST_APP_ID,
                "web_url": "https://example--cartography-e2e-app-web-endpoint.modal.run",
                "is_web_endpoint": True,
                "function_type": "FUNCTION_TYPE_FUNCTION",
                "is_method": False,
                "definition_id": None,
                "input_plane_url": "https://input-plane.us-east.modal.com:443",
                "input_plane_region": "us-east",
            },
            {
                # Modal names a class's service function "<Class>.*".
                "id": "fu-izrEFw6QJG8Td1o1VXY90Z",
                "name": "Worker.*",
                "app_id": TEST_APP_ID,
                "web_url": None,
                "is_web_endpoint": False,
                "function_type": "FUNCTION_TYPE_FUNCTION",
                "is_method": False,
                "definition_id": None,
                "input_plane_url": "https://input-plane.us-east.modal.com:443",
                "input_plane_region": "us-east",
            },
            {
                # A dotted name whose prefix matches no class must get no HAS_METHOD edge.
                "id": "fu-9OrphanMethodXXXXXXXXX",
                "name": "GhostClass.run",
                "app_id": TEST_APP_ID,
                "web_url": None,
                "is_web_endpoint": False,
                "function_type": "FUNCTION_TYPE_FUNCTION",
                "is_method": True,
                "definition_id": None,
                "input_plane_url": None,
                "input_plane_region": None,
            },
        ],
        "classes": [
            {"id": TEST_CLASS_ID, "name": "Worker", "app_id": TEST_APP_ID},
        ],
    },
    TEST_STOPPED_APP_ID: {"functions": [], "classes": []},
}

# cartography.intel.modal.util.list_image_tags()
# Modal lists tags, not images, so one image published under several tags appears several
# times. The first two rows here are the same image under two tags.
MODAL_IMAGES = [
    {
        "id": TEST_IMAGE_ID,
        "tag": "my-base-image:latest",
        "revision_id": "rev-2",
        "created_at": datetime(2026, 7, 29, 21, 37, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 7, 29, 21, 37, 0, tzinfo=timezone.utc),
    },
    {
        "id": TEST_IMAGE_ID,
        "tag": "my-base-image:v1.2.0",
        "revision_id": "rev-2",
        "created_at": datetime(2026, 7, 29, 21, 37, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 7, 29, 21, 37, 0, tzinfo=timezone.utc),
    },
    {
        "id": "im-2ndNamedImageXXXXXXXX",
        "tag": "other-image:latest",
        "revision_id": "rev-1",
        "created_at": datetime(2026, 7, 28, 10, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 7, 28, 10, 0, 0, tzinfo=timezone.utc),
    },
]

# cartography.intel.modal.util.list_sandboxes() -> (rows, complete)
MODAL_SANDBOXES = [
    {
        "id": TEST_SANDBOX_ID,
        "sandbox_version": "v1",
        "name": None,
        "app_id": TEST_APP_ID,
        # Ready with no result yet.
        "state": "RUNNING",
        "created_at": datetime(2026, 7, 29, 21, 39, 2, tzinfo=timezone.utc),
        "ready_at": datetime(2026, 7, 29, 21, 39, 10, tzinfo=timezone.utc),
        "image_id": TEST_IMAGE_ID,
        "memory_mb": 128,
        "memory_mb_max": None,
        "milli_cpu": 125,
        "milli_cpu_max": None,
        "gpu_type": None,
        "ephemeral_disk_mb": None,
        "regions": ["us-east-1"],
        "region": "us-east-1",
        "timeout_secs": 360,
        "idle_timeout_secs": None,
        "tags": ["owner=team-a"],
        "tunnels": [
            {
                # An encrypted port: no unencrypted endpoint is exposed.
                "host": "ta-abc-8080-xyz.w.modal.host",
                "port": 443,
                "unencrypted_host": None,
                "unencrypted_port": None,
                "container_port": 8080,
            },
        ],
    },
    {
        "id": "sb-JeuHHabrBlXBhVE3eHSTn5",
        "sandbox_version": "v1",
        "name": "agent-sandbox",
        "app_id": TEST_APP_ID,
        # Created but not ready yet.
        "state": "PENDING",
        "created_at": datetime(2026, 7, 29, 21, 39, 2, tzinfo=timezone.utc),
        "ready_at": None,
        # An anonymous build image, which is not enumerable, so HAS_IMAGE cannot resolve.
        "image_id": "im-R5Wufnqy0S6jjwIcH8Q8fV",
        "memory_mb": 512,
        "memory_mb_max": 1024,
        "milli_cpu": 250,
        "milli_cpu_max": 1000,
        "gpu_type": "GPU_TYPE_T4",
        "ephemeral_disk_mb": 4096,
        # Multi-region: the scalar region stays null on purpose.
        "regions": ["us-east-1", "us-west-2"],
        "region": None,
        "timeout_secs": 3600,
        "idle_timeout_secs": 300,
        "tags": [],
        "tunnels": [
            {
                # An unencrypted port: cleartext over the public internet.
                "host": "ta-def-9000-uvw.w.modal.host",
                "port": 443,
                "unencrypted_host": "ta-def-9000-uvw.unencrypted.modal.host",
                "unencrypted_port": 9000,
                "container_port": 9000,
            },
        ],
    },
    {
        "id": "sb-3FinishedSandboxXXXXXX",
        "sandbox_version": "v1",
        "name": None,
        "app_id": TEST_APP_ID,
        "state": "GENERIC_STATUS_FAILURE",
        "created_at": datetime(2026, 7, 29, 20, 0, 0, tzinfo=timezone.utc),
        "ready_at": datetime(2026, 7, 29, 20, 0, 5, tzinfo=timezone.utc),
        "image_id": TEST_IMAGE_ID,
        "memory_mb": 128,
        "memory_mb_max": None,
        "milli_cpu": 125,
        "milli_cpu_max": None,
        "gpu_type": None,
        "ephemeral_disk_mb": None,
        "regions": [],
        "region": None,
        "timeout_secs": 60,
        "idle_timeout_secs": None,
        "tags": [],
        "tunnels": [],
    },
]

# cartography.intel.modal.util.list_clusters()
MODAL_CLUSTERS = [
    {
        "id": TEST_CLUSTER_ID,
        "app_id": TEST_APP_ID,
        "started_at": datetime(2026, 7, 29, 21, 39, 3, tzinfo=timezone.utc),
        "task_ids": ["ta-01KYQX24W4D7NW306JQ5D98X7S"],
    },
]

# cartography.intel.modal.util.list_tasks(), keyed by app id
MODAL_TASKS = {
    TEST_APP_ID: [
        {
            # This one belongs to the cluster above.
            "id": "ta-01KYQX24W4D7NW306JQ5D98X7S",
            "app_id": TEST_APP_ID,
            "app_description": "cartography-e2e-app",
            "started_at": datetime(2026, 7, 29, 21, 39, 3, tzinfo=timezone.utc),
            "enqueued_at": datetime(2026, 7, 29, 21, 39, 2, tzinfo=timezone.utc),
        },
        {
            # A standalone task: no cluster.
            "id": "ta-01KYQX2WEK8T065MFN98455J9S",
            "app_id": TEST_APP_ID,
            "app_description": "cartography-e2e-app",
            "started_at": datetime(2026, 7, 29, 21, 39, 27, tzinfo=timezone.utc),
            "enqueued_at": datetime(2026, 7, 29, 21, 39, 26, tzinfo=timezone.utc),
        },
    ],
    TEST_STOPPED_APP_ID: [],
}

TEST_V2_SANDBOX_ID = "sb-01KYQX24W4D7NW306JQ5D98X7S"

# cartography.intel.modal.util.list_sandboxes_v2() -> (rows, complete), keyed by app id.
# Modal's docs state v2 sandboxes are not returned by the ordinary listing, so they arrive
# through a separate per-app RPC. The id is a 26-char ULID, which is what marks it as v2.
MODAL_V2_SANDBOXES = {
    TEST_APP_ID: [
        {
            "id": TEST_V2_SANDBOX_ID,
            "sandbox_version": "v2",
            "name": "v2-agent-sandbox",
            "app_id": TEST_APP_ID,
            "state": "RUNNING",
            "created_at": datetime(2026, 7, 30, 9, 0, 0, tzinfo=timezone.utc),
            "ready_at": datetime(2026, 7, 30, 9, 0, 5, tzinfo=timezone.utc),
            "image_id": TEST_IMAGE_ID,
            "memory_mb": 256,
            "memory_mb_max": None,
            "milli_cpu": 250,
            "milli_cpu_max": None,
            "gpu_type": None,
            "ephemeral_disk_mb": None,
            "regions": [],
            "region": None,
            "timeout_secs": 600,
            "idle_timeout_secs": None,
            "tags": [],
            "tunnels": [],
        },
    ],
    TEST_STOPPED_APP_ID: [],
}
