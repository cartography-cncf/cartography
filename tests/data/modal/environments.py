"""Shape returned by cartography.intel.modal.util.list_environments()."""

from datetime import datetime
from datetime import timezone

MODAL_ENVIRONMENTS = [
    {
        "id": "en-C3umado26sLFrhYfZjoWjL",
        "name": "main",
        # Modal leaves the webhook suffix empty on the default environment.
        "webhook_suffix": None,
        "created_at": datetime(2026, 7, 29, 20, 4, 3, tzinfo=timezone.utc),
        "is_default": True,
        "is_managed": False,
        "environment_type": "ENVIRONMENT_TYPE_UNSPECIFIED",
        "max_concurrent_tasks": 0,
        "max_concurrent_gpus": 0,
        "current_concurrent_tasks": 0,
        "current_concurrent_gpus": 0,
        "spend_limit_reached": False,
    },
    {
        "id": "en-9ZKpQr4tVbNmXsLdEfGhJk",
        "name": "prod",
        "webhook_suffix": "prod",
        "created_at": datetime(2026, 7, 30, 8, 15, 0, tzinfo=timezone.utc),
        "is_default": False,
        "is_managed": True,
        "environment_type": "ENVIRONMENT_TYPE_PUBLIC",
        "max_concurrent_tasks": 100,
        "max_concurrent_gpus": 8,
        "current_concurrent_tasks": 12,
        "current_concurrent_gpus": 2,
        "spend_limit_reached": True,
    },
]
