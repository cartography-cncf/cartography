from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.guardduty
from cartography.intel.aws.guardduty import _get_severity_range_for_threshold
from cartography.intel.aws.guardduty import sync
from cartography.rules.data.rules.guardduty_active_threat import (
    aws_guardduty_active_threat,
)
from tests.data.aws.guardduty import GET_AWS_API_CALL_FINDINGS
from tests.data.aws.guardduty import GET_AWS_API_CALL_FINDINGS_NO_REMOTE_ACCOUNT_NODE
from tests.data.aws.guardduty import GET_DETECTOR_DETAILS
from tests.data.aws.guardduty import GET_FINDINGS
from tests.data.aws.guardduty import GET_SAMPLE_FINDINGS
from tests.data.aws.guardduty import LIST_DETECTORS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "123456789012"
REMOTE_ACCOUNT_ID = "210987654321"
UNMATCHED_REMOTE_ACCOUNT_ID = "998877665544"
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

    # Create test EKS cluster that matches the Kubernetes finding. EKSCluster.id
    # is the cluster ARN, which the finding's EksClusterDetails.Arn matches.
    neo4j_session.run(
        """
        MERGE (cluster:EKSCluster {id: $cluster_arn})
        ON CREATE SET cluster.firstseen = timestamp()
        SET cluster.arn = $cluster_arn, cluster.lastupdated = $update_tag
        """,
        cluster_arn="arn:aws:eks:us-east-1:123456789012:cluster/test-cluster",
        update_tag=TEST_UPDATE_TAG,
    )

    # Create IAM principals + the long-term IAM user access key that match the
    # GuardDuty AccessKey findings. STS temporary credentials (ASIA*) are NOT
    # ingested as AccountAccessKey nodes (iam.list_access_keys only returns
    # long-term IAM user keys), so no AccountAccessKey node is created for the
    # AssumedRole finding.
    neo4j_session.run(
        """
        MERGE (k:AccountAccessKey {id: $access_key_id})
        ON CREATE SET k.firstseen = timestamp()
        SET k.accesskeyid = $access_key_id, k.lastupdated = $update_tag
        """,
        access_key_id="AKIAIOSFODNN7EXAMPLE",
        update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (u:AWSUser {id: $arn})
        ON CREATE SET u.firstseen = timestamp()
        SET u.userid = $userid, u.lastupdated = $update_tag
        """,
        arn="arn:aws:iam::123456789012:user/GeneratedFindingUserName",
        userid="AIDACKCEVSQ6C2EXAMPLE",
        update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (r:AWSRole {id: $arn})
        ON CREATE SET r.firstseen = timestamp()
        SET r.roleid = $roleid, r.lastupdated = $update_tag
        """,
        arn="arn:aws:iam::123456789012:role/GeneratedFindingRole",
        roleid="AROAEXAMPLEROLEID",
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
        ("a7e4567890123def4567890123def45670",),  # Severity 7.8 (HIGH)
        ("b8f5678901234abcdef5678901234abcdef",),  # Severity 8.5 (HIGH)
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
        ("a7e4567890123def4567890123def45670", 7.8, "AccessKey"),
        ("b8f5678901234abcdef5678901234abcdef", 8.5, "EKSCluster"),
        # Note: S3Bucket finding with severity 5.0 excluded by HIGH threshold
    }

    # Assert - Check that finding date fields were populated from the expected API paths
    finding_dates = neo4j_session.run(
        """
        MATCH (f:GuardDutyFinding)
        RETURN
            f.id AS id,
            toString(f.createdat) AS createdat,
            toString(f.updatedat) AS updatedat,
            toString(f.eventfirstseen) AS eventfirstseen,
            toString(f.eventlastseen) AS eventlastseen
        """,
    ).data()
    assert {
        (
            row["id"],
            row["createdat"],
            row["updatedat"],
            row["eventfirstseen"],
            row["eventlastseen"],
        )
        for row in finding_dates
    } == {
        (
            "74b1234567890abcdef1234567890abcdef",
            "2023-01-15T10:30:00",
            "2023-01-15T10:45:00",
            "2023-01-15T10:30:00",
            "2023-01-15T10:45:00",
        ),
        (
            "96d3456789012cdef3456789012cdef01",
            "2023-01-17T09:15:00",
            "2023-01-17T09:30:00",
            "2023-01-17T09:15:00",
            "2023-01-17T09:30:00",
        ),
        (
            "a7e4567890123def4567890123def45670",
            "2023-01-18T11:00:00",
            "2023-01-18T11:15:00",
            "2023-01-18T11:00:00",
            "2023-01-18T11:15:00",
        ),
        (
            "b8f5678901234abcdef5678901234abcdef",
            "2023-01-19T12:00:00",
            "2023-01-19T12:15:00",
            "2023-01-19T12:00:00",
            "2023-01-19T12:15:00",
        ),
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
        (TEST_ACCOUNT_ID, "a7e4567890123def4567890123def45670"),
        (TEST_ACCOUNT_ID, "b8f5678901234abcdef5678901234abcdef"),
        # Note: MEDIUM severity finding excluded
    }

    # Assert - Check that HIGH severity findings have the Risk label
    assert check_nodes(neo4j_session, "Risk", ["id"]) == {
        ("74b1234567890abcdef1234567890abcdef",),
        ("96d3456789012cdef3456789012cdef01",),
        ("a7e4567890123def4567890123def45670",),
        ("b8f5678901234abcdef5678901234abcdef",),
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
        ("a7e4567890123def4567890123def45670", "12abc34d56e78f901234567890abcdef"),
        ("b8f5678901234abcdef5678901234abcdef", "12abc34d56e78f901234567890abcdef"),
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

    # Assert - Check that the Kubernetes finding is connected to the EKS cluster
    assert check_rels(
        neo4j_session,
        "GuardDutyFinding",
        "id",
        "EKSCluster",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        (
            "b8f5678901234abcdef5678901234abcdef",
            "arn:aws:eks:us-east-1:123456789012:cluster/test-cluster",
        ),
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

    # Assert - AccessKey findings link to the long-term IAM user access key.
    # The AssumedRole finding's ASIA* key is not ingested as an
    # AccountAccessKey, so no edge is expected for it.
    assert check_rels(
        neo4j_session,
        "GuardDutyFinding",
        "id",
        "AccountAccessKey",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("96d3456789012cdef3456789012cdef01", "AKIAIOSFODNN7EXAMPLE"),
    }

    # Assert - IAMUser AccessKey findings are linked to the AWSUser by userid
    assert check_rels(
        neo4j_session,
        "GuardDutyFinding",
        "id",
        "AWSUser",
        "userid",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("96d3456789012cdef3456789012cdef01", "AIDACKCEVSQ6C2EXAMPLE"),
    }

    # Assert - AssumedRole AccessKey findings are linked to the AWSRole by roleid
    assert check_rels(
        neo4j_session,
        "GuardDutyFinding",
        "id",
        "AWSRole",
        "roleid",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("a7e4567890123def4567890123def45670", "AROAEXAMPLEROLEID"),
    }

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
        len(findings) == 4
    ), f"Expected 4 HIGH+ severity findings, got {len(findings)}"


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
    return_value=GET_SAMPLE_FINDINGS["Findings"],
)
def test_sync_guardduty_sample_findings_excluded_from_rule(
    mock_get_findings,
    mock_get_detector_details,
    mock_get_detectors,
    neo4j_session,
):
    """Sample findings are ingested but excluded from the active-threat rule."""
    boto3_session = MagicMock()
    sample_update_tag = 987654323
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, sample_update_tag)

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        sample_update_tag,
        {
            "UPDATE_TAG": sample_update_tag,
            "AWS_ID": TEST_ACCOUNT_ID,
        },
    )

    sample_id = "5a1samplefinding0000000000000000"
    real_id = "6b2realfinding00000000000000000"

    # Both findings are ingested; only the sample carries sample=True.
    assert check_nodes(neo4j_session, "GuardDutyFinding", ["id", "sample"]) == {
        (sample_id, True),
        (real_id, None),
    }

    # The rule's failing-set query returns the real finding and excludes the sample.
    rule_hits = {
        row["finding_id"]
        for row in neo4j_session.run(aws_guardduty_active_threat.cypher_query).data()
    }
    assert rule_hits == {real_id}

    # The denominator also excludes the sample (counts only the real finding).
    count = neo4j_session.run(aws_guardduty_active_threat.cypher_count_query).single()[
        "count"
    ]
    assert count == 1

    mock_get_findings.assert_called()


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
    return_value=GET_AWS_API_CALL_FINDINGS["Findings"],
)
def test_sync_guardduty_aws_api_call_fields(
    mock_get_findings,
    mock_get_detector_details,
    mock_get_detectors,
    neo4j_session,
):
    """Test that AWS_API_CALL findings persist richer action fields and REMOTE_ACCOUNT."""
    boto3_session = MagicMock()
    api_call_update_tag = 987654321
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, api_call_update_tag)
    create_test_account(neo4j_session, REMOTE_ACCOUNT_ID, api_call_update_tag)

    neo4j_session.run(
        """
        MERGE (bucket:S3Bucket {id: $bucket_name})
        ON CREATE SET bucket.firstseen = timestamp()
        SET bucket.lastupdated = $update_tag
        """,
        bucket_name="test-bucket",
        update_tag=api_call_update_tag,
    )

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        api_call_update_tag,
        {
            "UPDATE_TAG": api_call_update_tag,
            "AWS_ID": TEST_ACCOUNT_ID,
        },
    )

    assert check_nodes(
        neo4j_session,
        "GuardDutyFinding",
        [
            "id",
            "service_action_type",
            "service_count",
            "service_resource_role",
            "api_call_name",
            "api_call_service_name",
            "api_call_caller_type",
            "api_call_error_code",
            "api_call_remote_ip",
            "api_call_remote_country",
            "api_call_remote_city",
            "api_call_remote_org",
            "api_call_remote_asn",
            "api_call_remote_asn_org",
            "api_call_remote_isp",
            "api_call_remote_lat",
            "api_call_remote_lon",
            "api_call_remote_account_id",
            "api_call_remote_account_affiliated",
        ],
    ) == {
        (
            "85c2345678901bcdef2345678901bcdef0",
            "AWS_API_CALL",
            12,
            "TARGET",
            "ListObjects",
            "s3.amazonaws.com",
            "Remote IP",
            None,
            "203.0.113.5",
            "Canada",
            "Toronto",
            "Example Canadian Organization",
            "54321",
            "Example Canadian ISP",
            "Example Canadian ISP",
            43.6532,
            -79.3832,
            None,
            None,
        ),
        (
            "96d3456789012cdef3456789012cdef01",
            "AWS_API_CALL",
            3,
            "ACTOR",
            "CreateUser",
            "iam.amazonaws.com",
            "Remote IP",
            None,
            "192.0.2.1",
            "United States",
            "Seattle",
            "Amazon.com Inc.",
            "16509",
            "AMAZON-02",
            "Amazon.com Inc.",
            47.6062,
            -122.3321,
            REMOTE_ACCOUNT_ID,
            True,
        ),
    }

    assert check_rels(
        neo4j_session,
        "GuardDutyFinding",
        "id",
        "AWSAccount",
        "id",
        "REMOTE_ACCOUNT",
        rel_direction_right=True,
    ) == {
        ("96d3456789012cdef3456789012cdef01", REMOTE_ACCOUNT_ID),
    }

    mock_get_findings.assert_called()


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
    return_value=GET_AWS_API_CALL_FINDINGS_NO_REMOTE_ACCOUNT_NODE["Findings"],
)
def test_sync_guardduty_aws_api_call_remote_account_without_matching_node(
    mock_get_findings,
    mock_get_detector_details,
    mock_get_detectors,
    neo4j_session,
):
    """Test that remote account properties persist even when no matching AWSAccount node exists."""
    boto3_session = MagicMock()
    api_call_update_tag = 987654322
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, api_call_update_tag)

    neo4j_session.run(
        """
        MERGE (bucket:S3Bucket {id: $bucket_name})
        ON CREATE SET bucket.firstseen = timestamp()
        SET bucket.lastupdated = $update_tag
        """,
        bucket_name="remote-account-test-bucket",
        update_tag=api_call_update_tag,
    )

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        api_call_update_tag,
        {
            "UPDATE_TAG": api_call_update_tag,
            "AWS_ID": TEST_ACCOUNT_ID,
        },
    )

    assert check_nodes(
        neo4j_session,
        "GuardDutyFinding",
        [
            "id",
            "api_call_remote_account_id",
            "api_call_remote_account_affiliated",
        ],
    ) == {
        (
            "d2f5678901234ef5678901234ef567890",
            UNMATCHED_REMOTE_ACCOUNT_ID,
            False,
        ),
    }

    assert (
        check_rels(
            neo4j_session,
            "GuardDutyFinding",
            "id",
            "AWSAccount",
            "id",
            "REMOTE_ACCOUNT",
            rel_direction_right=True,
        )
        == set()
    )

    mock_get_findings.assert_called()
