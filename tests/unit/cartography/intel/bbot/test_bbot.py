import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.bbot import parse_completed_scan_runs
from cartography.intel.bbot import sync_bbot_from_report_reader
from cartography.intel.bbot import transform
from cartography.intel.common.object_store import ReportRef

SCAN_ID = "SCAN:stable-scan-id"


def _scan_event(
    status: str,
    uuid: str,
    timestamp: float,
    *,
    finished_at: str | None = None,
    scan_id: str = SCAN_ID,
    legacy_data: bool = False,
) -> dict:
    data = {
        "name": "synthetic-scan",
        "status": status,
        "started_at": "2026-01-01T00:00:00Z",
        "target": {"seeds": ["example.test"]},
    }
    if finished_at:
        data["finished_at"] = finished_at
    return {
        "type": "SCAN",
        "id": scan_id,
        "uuid": uuid,
        "timestamp": timestamp,
        "data" if legacy_data else "data_json": data,
    }


def _event(
    event_type: str,
    event_id: str,
    uuid: str,
    data: str | dict,
    *,
    timestamp: float,
    parent_uuid: str | None = None,
    **properties,
) -> dict:
    event = {
        "type": event_type,
        "id": event_id,
        "uuid": uuid,
        "scan": SCAN_ID,
        "timestamp": timestamp,
        "data_json" if isinstance(data, dict) else "data": data,
        **properties,
    }
    if parent_uuid:
        event["parent_uuid"] = parent_uuid
    return event


def _jsonl(events: list[dict]) -> str:
    return "\n".join(json.dumps(event) for event in events)


def test_parse_completed_scan_accepts_different_occurrence_uuids() -> None:
    # Arrange
    events = [
        _scan_event("RUNNING", "SCAN:run-start", 1, legacy_data=True),
        _event(
            "DNS_NAME", "DNS_NAME:example", "DNS_NAME:one", "example.test", timestamp=2
        ),
        _scan_event(
            "FINISHED",
            "SCAN:run-finish",
            3,
            finished_at="2026-01-01T00:01:00Z",
        ),
    ]

    # Act
    runs = parse_completed_scan_runs(_jsonl(events), "synthetic.json")

    # Assert
    assert len(runs) == 1
    assert runs[0][1] == events


def test_parse_completed_scan_rejects_changed_stable_scan_id() -> None:
    # Arrange
    events = [
        _scan_event("RUNNING", "SCAN:run-start", 1),
        _scan_event(
            "FINISHED",
            "SCAN:run-finish",
            2,
            finished_at="2026-01-01T00:01:00Z",
            scan_id="SCAN:different-id",
        ),
    ]

    # Act and assert
    with pytest.raises(ValueError, match="scan ID changed"):
        parse_completed_scan_runs(_jsonl(events), "synthetic.json")


def test_transform_aggregates_occurrences_and_builds_stable_relationships() -> None:
    # Arrange
    events = [
        _scan_event("RUNNING", "SCAN:run-start", 1),
        _event(
            "DNS_NAME",
            "DNS_NAME:example",
            "DNS_NAME:first",
            "Example.Test.",
            timestamp=3,
            parent_uuid="SCAN:run-start",
            host="Example.Test.",
            resolved_hosts=["8.8.8.8"],
            tags=["a-record"],
            module="dnsresolve",
            scope_distance=1,
            discovery_context="latest context",
        ),
        _event(
            "DNS_NAME",
            "DNS_NAME:example",
            "DNS_NAME:second",
            "example.test",
            timestamp=2,
            parent_uuid="SCAN:run-start",
            host="example.test",
            resolved_hosts=["8.8.8.8"],
            tags=["in-scope"],
            module="speculate",
            scope_distance=0,
            discovery_context="older context",
        ),
        _event(
            "IP_ADDRESS",
            "IP_ADDRESS:google-dns",
            "IP_ADDRESS:one",
            "8.8.8.8",
            timestamp=4,
            parent_uuid="DNS_NAME:first",
            host="8.8.8.8",
        ),
        _scan_event(
            "FINISHED",
            "SCAN:run-finish",
            5,
            finished_at="2026-01-01T00:01:00Z",
        ),
    ]

    # Act
    nodes, relationships = transform(events, "synthetic.json")

    # Assert
    dns = nodes["BbotDNSName"][0]
    assert dns["id"] == "DNS_NAME:example"
    assert dns["occurrence_count"] == 2
    assert dns["occurrence_uuids"] == ["DNS_NAME:first", "DNS_NAME:second"]
    assert dns["tags"] == ["a-record", "in-scope"]
    assert dns["modules"] == ["dnsresolve", "speculate"]
    assert dns["scope_distance"] == 0
    assert dns["discovery_contexts"] == ["latest context", "older context"]
    assert dns["observed_at"] == 3
    assert relationships[("BbotDNSName", "BbotIPAddress", "RESOLVES_TO")] == [
        {"source_id": "DNS_NAME:example", "target_id": "IP_ADDRESS:google-dns"},
    ]
    assert relationships[("BbotDNSName", "BbotScan", "OBSERVED_IN")] == [
        {"source_id": "DNS_NAME:example", "target_id": SCAN_ID},
    ]
    assert relationships[("BbotIPAddress", "BbotDNSName", "DISCOVERED_FROM")] == [
        {"source_id": "IP_ADDRESS:google-dns", "target_id": "DNS_NAME:example"},
    ]


def test_transform_uses_custom_stable_identities() -> None:
    # Arrange
    events = [
        _scan_event("RUNNING", "SCAN:run-start", 1),
        _event(
            "FINDING",
            "FINDING:bbot-id-one",
            "FINDING:one",
            {
                "name": " Exposed Admin Panel ",
                "description": "Original explanation",
                "severity": "MEDIUM",
                "confidence": "LOW",
                "url": "https://EXAMPLE.test:443/admin#fragment",
            },
            timestamp=2,
            module="nuclei",
        ),
        _event(
            "FINDING",
            "FINDING:bbot-id-two",
            "FINDING:two",
            {
                "name": "exposed admin panel",
                "description": "Updated explanation",
                "severity": "HIGH",
                "confidence": "CONFIRMED",
                "url": "https://example.test/admin",
            },
            timestamp=3,
            module="nuclei",
        ),
        _event(
            "STORAGE_BUCKET",
            "STORAGE_BUCKET:one",
            "STORAGE_BUCKET:occurrence-one",
            {
                "name": "Example-Bucket",
                "provider": "AWS",
                "url": "https://example-bucket.s3.us-east-1.amazonaws.com",
            },
            timestamp=2,
            module="bucket_amazon",
        ),
        _event(
            "STORAGE_BUCKET",
            "STORAGE_BUCKET:two",
            "STORAGE_BUCKET:occurrence-two",
            {
                "name": "example-bucket",
                "provider": "aws",
                "url": "https://example-bucket.s3.us-west-2.amazonaws.com",
            },
            timestamp=3,
            module="bucket_amazon",
        ),
        _event(
            "SOCIAL",
            "SOCIAL:one",
            "SOCIAL:occurrence-one",
            {
                "platform": "GitHub",
                "url": "https://GITHUB.com:443/example#profile",
                "profile_name": "example",
            },
            timestamp=2,
        ),
        _event(
            "SOCIAL",
            "SOCIAL:two",
            "SOCIAL:occurrence-two",
            {
                "platform": "github",
                "url": "https://github.com/example",
                "profile_name": "example-renamed",
            },
            timestamp=3,
        ),
        _scan_event(
            "FINISHED",
            "SCAN:run-finish",
            4,
            finished_at="2026-01-01T00:01:00Z",
        ),
    ]

    # Act
    nodes, _ = transform(events, "synthetic.json")

    # Assert
    assert len(nodes["BbotFinding"]) == 1
    assert nodes["BbotFinding"][0]["occurrence_count"] == 2
    assert nodes["BbotFinding"][0]["severity"] == "HIGH"
    assert nodes["BbotFinding"][0]["confidence"] == "CONFIRMED"
    assert nodes["BbotFinding"][0]["description"] == "Updated explanation"
    assert len(nodes["BbotStorageBucket"]) == 1
    assert nodes["BbotStorageBucket"][0]["occurrence_count"] == 2
    assert len(nodes["BbotSocial"]) == 1
    assert nodes["BbotSocial"][0]["occurrence_count"] == 2


@patch("cartography.intel.bbot.sync")
def test_report_reader_selects_latest_completed_scan(mock_sync: MagicMock) -> None:
    # Arrange
    older_ref = ReportRef("s3://example/older.json", "older.json")
    newer_ref = ReportRef("s3://example/newer.jsonl", "newer.jsonl")
    incomplete_ref = ReportRef("s3://example/incomplete.json", "incomplete.json")
    older = _jsonl(
        [
            _scan_event("RUNNING", "SCAN:older-start", 1, legacy_data=True),
            _scan_event(
                "FINISHED",
                "SCAN:older-finish",
                2,
                finished_at="2026-01-01T00:01:00Z",
                legacy_data=True,
            ),
        ],
    )
    newer = _jsonl(
        [
            _scan_event("RUNNING", "SCAN:newer-start", 3),
            _scan_event(
                "FINISHED",
                "SCAN:newer-finish",
                4,
                finished_at="2026-01-02T00:01:00Z",
            ),
        ],
    )
    incomplete = _jsonl([_scan_event("RUNNING", "SCAN:incomplete", 5)])
    payloads = {
        older_ref: older.encode(),
        newer_ref: newer.encode(),
        incomplete_ref: incomplete.encode(),
    }
    reader = MagicMock()
    reader.source_uri = "s3://example/"
    reader.list_reports.return_value = [newer_ref, incomplete_ref, older_ref]
    reader.read_bytes.side_effect = payloads.__getitem__

    # Act
    sync_bbot_from_report_reader(MagicMock(), reader, 123, {"UPDATE_TAG": 123})

    # Assert
    assert mock_sync.call_args.args[1] == json.loads(
        "[" + newer.replace("\n", ",") + "]"
    )
    assert mock_sync.call_args.args[2] == newer_ref.uri
    assert mock_sync.call_args.args[3] == 123
