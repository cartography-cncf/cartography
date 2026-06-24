from datetime import datetime

from cartography.intel.aws.guardduty import transform_findings
from tests.data.aws.guardduty import EXPECTED_TRANSFORM_RESULTS
from tests.data.aws.guardduty import GET_FINDINGS

TEST_UPDATE_TAG = 123456789


def test_transform_findings():
    """Test transform_findings function with mock API response data."""
    # Use the full mock API response data
    findings_data = GET_FINDINGS["Findings"]
    transformed = transform_findings(findings_data)

    # Should transform 5 findings
    assert len(transformed) == 5

    # Expected EC2 Instance finding
    expected_ec2_finding = EXPECTED_TRANSFORM_RESULTS[0]
    assert transformed[0] == expected_ec2_finding

    # Expected S3 Bucket finding
    expected_s3_finding = EXPECTED_TRANSFORM_RESULTS[1]
    assert transformed[1] == expected_s3_finding

    # Expected IAM AccessKey finding (UserType=IAMUser)
    expected_iam_user_finding = EXPECTED_TRANSFORM_RESULTS[2]
    assert transformed[2] == expected_iam_user_finding

    # Expected IAM AccessKey finding (UserType=AssumedRole)
    expected_iam_role_finding = EXPECTED_TRANSFORM_RESULTS[3]
    assert transformed[3] == expected_iam_role_finding

    # Expected EKS Cluster (Kubernetes) finding
    expected_eks_finding = EXPECTED_TRANSFORM_RESULTS[4]
    assert transformed[4] == expected_eks_finding


def test_transform_findings_extracts_sample_flag():
    """sample flag is parsed from the JSON-encoded service.additionalInfo.value."""
    findings = [
        {
            "Id": "sample",
            "Resource": {"ResourceType": "Instance"},
            "Service": {
                "AdditionalInfo": {
                    "Value": '{"threatListName":"GeneratedFindingThreatListName","sample":true}',
                    "Type": "default",
                },
            },
        },
        {
            "Id": "real-with-additional-info",
            "Resource": {"ResourceType": "Instance"},
            "Service": {
                "AdditionalInfo": {
                    "Value": '{"threatListName":"GeneratedFindingThreatListName"}',
                    "Type": "default",
                },
            },
        },
        {
            "Id": "no-additional-info",
            "Resource": {"ResourceType": "Instance"},
            "Service": {},
        },
        {
            "Id": "non-json-value",
            "Resource": {"ResourceType": "Instance"},
            "Service": {"AdditionalInfo": {"Value": "not-json", "Type": "default"}},
        },
    ]

    samples = {f["id"]: f["sample"] for f in transform_findings(findings)}

    assert samples == {
        "sample": True,
        "real-with-additional-info": None,
        "no-additional-info": None,
        "non-json-value": None,
    }


def test_transform_findings_prefers_service_event_fields():
    findings = [
        {
            "Id": "finding-prefers-service",
            "CreatedAt": datetime(2024, 1, 1, 0, 0, 0),
            "UpdatedAt": datetime(2024, 1, 1, 1, 0, 0),
            "EventFirstSeen": datetime(2024, 1, 1, 2, 0, 0),
            "EventLastSeen": datetime(2024, 1, 1, 3, 0, 0),
            "Service": {
                "EventFirstSeen": datetime(2024, 1, 1, 4, 0, 0),
                "EventLastSeen": datetime(2024, 1, 1, 5, 0, 0),
            },
            "Resource": {"ResourceType": "AccessKey"},
        }
    ]

    transformed = transform_findings(findings)

    assert transformed[0]["eventfirstseen"] == datetime(2024, 1, 1, 4, 0, 0)
    assert transformed[0]["eventlastseen"] == datetime(2024, 1, 1, 5, 0, 0)


def test_transform_findings_falls_back_to_top_level_event_fields():
    findings = [
        {
            "Id": "finding-fallback-top-level",
            "CreatedAt": datetime(2024, 2, 1, 0, 0, 0),
            "UpdatedAt": datetime(2024, 2, 1, 1, 0, 0),
            "EventFirstSeen": datetime(2024, 2, 1, 2, 0, 0),
            "EventLastSeen": datetime(2024, 2, 1, 3, 0, 0),
            "Resource": {"ResourceType": "AccessKey"},
        }
    ]

    transformed = transform_findings(findings)

    assert transformed[0]["eventfirstseen"] == datetime(2024, 2, 1, 2, 0, 0)
    assert transformed[0]["eventlastseen"] == datetime(2024, 2, 1, 3, 0, 0)
