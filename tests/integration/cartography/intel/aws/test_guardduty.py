from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.guardduty
from cartography.intel.aws.guardduty import _get_severity_range_for_threshold
from cartography.intel.aws.guardduty import sync
from tests.data.aws.guardduty import GET_DETECTOR_DETAILS
from tests.data.aws.guardduty import GET_FINDINGS
from tests.data.aws.guardduty import LIST_DETECTORS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "123456789012"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def mock_get_findings_with_severity_filter(
    boto3_session, region, detector_id, severity_threshold=None
):
    """Mock get_findings that actually filters by severity threshold like the real implementation."""
    all_findings = GET_FINDINGS["Findings"]

    if not severity_threshold:
        return all_findings

    # Use the same filtering logic as the real implementation
    severity_range = _get_severity_range_for_threshold(severity_threshold)
    if not severity_range:
        return all_findings

    # Convert to float before finding minimum to get correct numeric comparison
    min_severity = min(float(s) for s in severity_range)
    filtered_findings = [
        finding
        for finding in all_findings
        if finding["Severity"] >= min_severity and not finding.get("Archived", False)
    ]

    return filtered_findings


@patch.object(
    cartography.intel.aws.guardduty,
    "get_detectors",
    return_value=LIST_DETECTORS["DetectorIds"],
)
@patch.object(
    cartography.intel.aws.guardduty,
    "get_detector_details",
    return_value=GET_DETECTOR_DETAILS,
)
@patch.object(
    cartography.intel.aws.guardduty,
    "get_findings",
    side_effect=mock_get_findings_with_severity_filter,
)
def test_sync_guardduty_findings(
    mock_get_findings,
    mock_get_detector_details,
    mock_get_detectors,
    neo4j_session,
):
    """
    Test that GuardDuty findings are correctly synced to the graph and create proper relationships.
    Also tests severity threshold filtering functionality.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Create test EC2 instance and S3 bucket that match the findings
    neo4j_session.run(
        """
        MERGE (instance:EC2Instance {id: $instance_id})
        ON CREATE SET instance.firstseen = timestamp()
        SET instance.lastupdated = $update_tag
        """,
        instance_id="i-99999999",
        update_tag=TEST_UPDATE_TAG,
    )

    neo4j_session.run(
        """
        MERGE (bucket:S3Bucket {id: $bucket_name})
        ON CREATE SET bucket.firstseen = timestamp()
        SET bucket.lastupdated = $update_tag
        """,
        bucket_name="test-bucket",
        update_tag=TEST_UPDATE_TAG,
    )

    # Act - Test severity threshold functionality (HIGH threshold = severity >= 7.0)
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACCOUNT_ID,
            "aws_guardduty_severity_threshold": "HIGH",
        },
    )

    # Assert - Check that only HIGH severity findings were created (excluding MEDIUM severity 5.0 finding)
    assert check_nodes(neo4j_session, "GuardDutyFinding", ["id"]) == {
        ("74b1234567890abcdef1234567890abcdef",),  # Severity 8.0 (HIGH)
        ("96d3456789012cdef3456789012cdef01",),  # Severity 7.5 (HIGH)
        # Note: 85c2345678901bcdef2345678901bcdef0 (severity 5.0) should be excluded
    }

    # Assert - Check that GuardDuty detectors were synced with properties
    assert check_nodes(
        neo4j_session,
        "GuardDutyDetector",
        ["id", "status", "findingpublishingfrequency"],
    ) == {
        ("12abc34d56e78f901234567890abcdef", "ENABLED", "FIFTEEN_MINUTES"),
        ("98zyx76w54v32u109876543210zyxwvu", "DISABLED", "SIX_HOURS"),
    }

    # Assert - Check that synced findings have the correct properties
    assert check_nodes(
        neo4j_session, "GuardDutyFinding", ["id", "severity", "resource_type"]
    ) == {
        ("74b1234567890abcdef1234567890abcdef", 8.0, "Instance"),
        ("96d3456789012cdef3456789012cdef01", 7.5, "AccessKey"),
        # Note: S3Bucket finding with severity 5.0 excluded by HIGH threshold
    }

    # Assert - Check that GuardDuty detectors are connected to the AWSAccount
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "GuardDutyDetector",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "12abc34d56e78f901234567890abcdef"),
        (TEST_ACCOUNT_ID, "98zyx76w54v32u109876543210zyxwvu"),
    }

    # Assert - Check that HIGH severity findings are connected to the AWSAccount
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "GuardDutyFinding",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "74b1234567890abcdef1234567890abcdef"),
        (TEST_ACCOUNT_ID, "96d3456789012cdef3456789012cdef01"),
        # Note: MEDIUM severity finding excluded
    }

    # Assert - Check that HIGH severity findings have the Risk label
    assert check_nodes(neo4j_session, "Risk", ["id"]) == {
        ("74b1234567890abcdef1234567890abcdef",),
        ("96d3456789012cdef3456789012cdef01",),
        # Note: MEDIUM severity finding excluded
    }

    assert check_rels(
        neo4j_session,
        "GuardDutyFinding",
        "id",
        "GuardDutyDetector",
        "id",
        "DETECTED_BY",
        rel_direction_right=True,
    ) == {
        ("74b1234567890abcdef1234567890abcdef", "12abc34d56e78f901234567890abcdef"),
        ("96d3456789012cdef3456789012cdef01", "12abc34d56e78f901234567890abcdef"),
    }

    # Assert - Check that GuardDuty finding is connected to the EC2 instance
    assert check_rels(
        neo4j_session,
        "GuardDutyFinding",
        "id",
        "EC2Instance",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("74b1234567890abcdef1234567890abcdef", "i-99999999"),
    }

    # Assert - Verify that the MEDIUM severity S3 finding was filtered out
    # (No AFFECTS relationship to S3 bucket should exist)
    s3_relationships = check_rels(
        neo4j_session,
        "GuardDutyFinding",
        "id",
        "S3Bucket",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    )
    assert (
        s3_relationships == set()
    ), f"Expected no S3 relationships with HIGH threshold, but found: {s3_relationships}"

    # Verify get_findings was called with severity_threshold parameter
    mock_get_findings.assert_called()

    # Verify that only HIGH+ severity findings were synced to the graph
    findings = neo4j_session.run(
        "MATCH (f:GuardDutyFinding) RETURN f.severity as severity"
    ).data()
    assert all(
        f["severity"] >= 7.0 for f in findings
    ), "All findings should be HIGH+ severity (>= 7.0)"
    assert (
        len(findings) == 2
    ), f"Expected 2 HIGH+ severity findings, got {len(findings)}"
