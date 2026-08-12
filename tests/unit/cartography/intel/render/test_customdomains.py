"""
Cron jobs have no persistent HTTP listener to attach a custom domain to. Confirmed live:
GET /services/{cronJobId}/custom-domains returns 400 ("service not found") instead of an
empty list, unlike every other service type. sync() must skip cron_job services rather
than call that endpoint and crash the whole render sync stage.
"""

from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.render.customdomains as customdomains


@patch.object(customdomains, "cleanup")
@patch.object(customdomains, "load_custom_domains")
@patch.object(customdomains, "get")
def test_sync_skips_cron_job_services(mock_get, mock_load, mock_cleanup):
    services = [
        {"id": "srv-1", "type": "web_service"},
        {"id": "crn-1", "type": "cron_job"},
        {"id": "srv-2", "type": "background_worker"},
    ]
    mock_get.return_value = []

    customdomains.sync(
        Mock(),
        Mock(),
        "tea-1",
        services,
        123,
        {"UPDATE_TAG": 123, "OWNER_ID": "tea-1"},
    )

    called_service_ids = {call.args[1] for call in mock_get.call_args_list}
    assert called_service_ids == {"srv-1", "srv-2"}
