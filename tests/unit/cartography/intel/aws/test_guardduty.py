from cartography.intel.aws.guardduty import transform_findings
from tests.data.aws.guardduty import EXPECTED_TRANSFORM_RESULTS
from tests.data.aws.guardduty import GET_FINDINGS

TEST_UPDATE_TAG = 123456789


def test_transform_findings():
    """Test transform_findings function with mock API response data."""
    # Use the full mock API response data
    findings_data = GET_FINDINGS["Findings"]
    transformed = transform_findings(findings_data)

    # Should transform 3 findings
    assert len(transformed) == 3

    # Expected EC2 Instance finding
    expected_ec2_finding = EXPECTED_TRANSFORM_RESULTS[0]
    assert transformed[0] == expected_ec2_finding

    # Expected S3 Bucket finding
    expected_s3_finding = EXPECTED_TRANSFORM_RESULTS[1]
    assert transformed[1] == expected_s3_finding

    # Expected IAM AccessKey finding
    expected_iam_finding = EXPECTED_TRANSFORM_RESULTS[2]
    assert transformed[2] == expected_iam_finding
