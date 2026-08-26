import pytest

import cartography.intel.gcp.log_sink
from tests.data.gcp.log_sink import FOLDER_LOG_SINKS
from tests.data.gcp.log_sink import ORG_LOG_SINKS


def test_transform_gcp_log_sinks_for_org_scope():
    sinks = cartography.intel.gcp.log_sink.transform_gcp_log_sinks(
        ORG_LOG_SINKS,
        "organization",
        "organizations/123456789012",
    )

    assert sinks == [
        {
            "id": "organizations/123456789012/sinks/org-audit-sink",
            "name": "organizations/123456789012/sinks/org-audit-sink",
            "sink_name": "org-audit-sink",
            "destination": "bigquery.googleapis.com/projects/log-project/datasets/audit_logs",
            "bigquery_dataset_id": "log-project:audit_logs",
            "filter": 'logName:"cloudaudit.googleapis.com/activity"',
            "description": "Organization audit sink",
            "disabled": False,
            "include_children": True,
            "writer_identity": "serviceAccount:org-writer@gcp-sa-logging.iam.gserviceaccount.com",
            "output_version_format": "V2",
            "parent_type": "organization",
            "parent_id": "organizations/123456789012",
        },
    ]


def test_transform_gcp_log_sinks_qualifies_short_sink_names():
    sinks = cartography.intel.gcp.log_sink.transform_gcp_log_sinks(
        [
            {
                "name": "audit-sink",
                "destination": "bigquery.googleapis.com/projects/log-project/datasets/audit_logs",
            },
        ],
        "project",
        "projects/test-project",
    )

    assert sinks[0]["id"] == "projects/test-project/sinks/audit-sink"
    assert sinks[0]["name"] == "projects/test-project/sinks/audit-sink"
    assert sinks[0]["sink_name"] == "audit-sink"


def test_transform_gcp_log_sinks_defaults_missing_include_children_to_false():
    sinks = cartography.intel.gcp.log_sink.transform_gcp_log_sinks(
        FOLDER_LOG_SINKS,
        "folder",
        "folders/987654321098",
    )

    assert sinks[0]["bigquery_dataset_id"] is None
    assert sinks[0]["disabled"] is True
    assert sinks[0]["include_children"] is False
    assert sinks[0]["parent_type"] == "folder"
    assert sinks[0]["parent_id"] == "folders/987654321098"


@pytest.mark.parametrize(
    ("destination", "expected"),
    [
        (
            "bigquery.googleapis.com/projects/log-project/datasets/audit_logs",
            "log-project:audit_logs",
        ),
        (
            "logging.googleapis.com/projects/log-project/locations/global/buckets/audit",
            None,
        ),
        (
            "pubsub.googleapis.com/projects/log-project/topics/audit-topic",
            None,
        ),
        ("bigquery.googleapis.com/projects/log-project/topics/not-a-dataset", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_bigquery_dataset_id(destination, expected):
    assert (
        cartography.intel.gcp.log_sink._parse_bigquery_dataset_id(destination)
        == expected
    )
