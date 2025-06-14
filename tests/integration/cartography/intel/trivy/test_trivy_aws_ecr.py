from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ecr
import cartography.intel.trivy
import tests.data.aws.ecr
from cartography.intel.trivy import sync_trivy_aws_ecr_from_s3
from tests.data.trivy.trivy_sample import TRIVY_SAMPLE
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789
TEST_REGION = "us-east-1"


@patch.object(
    cartography.intel.trivy,
    "get_json_files_in_s3",
    return_value={
        "trivy-scans/000000000000.dkr.ecr.us-east-1/test-repository:1234567890.json"
    },
)
@patch.object(
    cartography.intel.trivy.scanner,
    "read_scan_results_from_s3",
    return_value=(
        TRIVY_SAMPLE["Results"],
        "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    ),
)
@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repositories",
    return_value=tests.data.aws.ecr.DESCRIBE_REPOSITORIES["repositories"][
        2:
    ],  # just the test-repository,
)
@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repository_images",
    return_value=tests.data.aws.ecr.LIST_REPOSITORY_IMAGES[
        "000000000000.dkr.ecr.us-east-1/test-repository"
    ][
        :1
    ],  # just one image
)
def test_sync_trivy_aws_ecr(
    mock_get_images,
    mock_get_repos,
    mock_get_scan_results,
    mock_list_s3_scan_results,
    neo4j_session,
):
    """
    Ensure that Trivy scan results are properly loaded into Neo4j
    """
    # Arrange
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # First sync ECR data
    boto3_session = MagicMock()
    cartography.intel.aws.ecr.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Act
    sync_trivy_aws_ecr_from_s3(
        neo4j_session,
        "test-bucket",
        "trivy-scans/",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        boto3_session,
    )

    # Assert TrivyImageFinding nodes exist
    assert check_nodes(
        neo4j_session, "TrivyImageFinding", ["id", "name", "severity"]
    ) == {
        ("TIF|CVE-2023-29383", "CVE-2023-29383", "LOW"),
        ("TIF|CVE-2023-4039", "CVE-2023-4039", "LOW"),
        ("TIF|CVE-2023-4641", "CVE-2023-4641", "MEDIUM"),
        ("TIF|CVE-2024-12133", "CVE-2024-12133", "MEDIUM"),
        ("TIF|CVE-2024-13176", "CVE-2024-13176", "MEDIUM"),
        ("TIF|CVE-2024-26462", "CVE-2024-26462", "MEDIUM"),
        ("TIF|CVE-2024-56406", "CVE-2024-56406", "HIGH"),
        ("TIF|CVE-2025-24528", "CVE-2025-24528", "MEDIUM"),
        ("TIF|CVE-2025-31115", "CVE-2025-31115", "HIGH"),
        ("TIF|CVE-2025-43859", "CVE-2025-43859", "CRITICAL"),
    }

    # Assert Package nodes exist
    assert check_nodes(neo4j_session, "Package", ["id", "name", "version"]) == {
        ("0.14.0|h11", "h11", "0.14.0"),
        ("1.20.1-2+deb12u2|krb5-locales", "krb5-locales", "1.20.1-2+deb12u2"),
        ("1.20.1-2+deb12u2|libk5crypto3", "libk5crypto3", "1.20.1-2+deb12u2"),
        ("1.20.1-2+deb12u2|libkrb5-3", "libkrb5-3", "1.20.1-2+deb12u2"),
        ("1.20.1-2+deb12u2|libkrb5support0", "libkrb5support0", "1.20.1-2+deb12u2"),
        ("12.2.0-14|gcc-12-base", "gcc-12-base", "12.2.0-14"),
        ("12.2.0-14|libstdc++6", "libstdc++6", "12.2.0-14"),
        ("1:4.13+dfsg1-1+b1|login", "login", "1:4.13+dfsg1-1+b1"),
        ("1:4.13+dfsg1-1+b1|passwd", "passwd", "1:4.13+dfsg1-1+b1"),
        ("3.0.15-1~deb12u1|libssl3", "libssl3", "3.0.15-1~deb12u1"),
        ("3.0.15-1~deb12u1|openssl", "openssl", "3.0.15-1~deb12u1"),
        ("4.19.0-2|libtasn1-6", "libtasn1-6", "4.19.0-2"),
        ("5.36.0-7+deb12u1|perl-base", "perl-base", "5.36.0-7+deb12u1"),
        ("5.4.1-0.2|liblzma5", "liblzma5", "5.4.1-0.2"),
    }

    # Assert Package to ECRImage relationships
    assert check_rels(
        neo4j_session,
        "Package",
        "id",
        "ECRImage",
        "id",
        "DEPLOYED",
        rel_direction_right=True,
    ) == {
        (
            "0.14.0|h11",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "1.20.1-2+deb12u2|krb5-locales",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "1.20.1-2+deb12u2|libk5crypto3",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "1.20.1-2+deb12u2|libkrb5-3",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "1.20.1-2+deb12u2|libkrb5support0",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "12.2.0-14|gcc-12-base",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "12.2.0-14|libstdc++6",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "1:4.13+dfsg1-1+b1|login",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "1:4.13+dfsg1-1+b1|passwd",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "3.0.15-1~deb12u1|libssl3",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "3.0.15-1~deb12u1|openssl",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "4.19.0-2|libtasn1-6",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "5.36.0-7+deb12u1|perl-base",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "5.4.1-0.2|liblzma5",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
    }

    # Assert Package to TrivyFix relationships
    assert check_rels(
        neo4j_session,
        "Package",
        "id",
        "TrivyFix",
        "id",
        "SHOULD_UPDATE_TO",
        rel_direction_right=True,
    ) == {
        ("0.14.0|h11", "0.16.0|h11"),
        ("1.20.1-2+deb12u2|krb5-locales", "1.20.1-2+deb12u3|krb5-locales"),
        ("1.20.1-2+deb12u2|libk5crypto3", "1.20.1-2+deb12u3|libk5crypto3"),
        ("1.20.1-2+deb12u2|libkrb5-3", "1.20.1-2+deb12u3|libkrb5-3"),
        ("1.20.1-2+deb12u2|libkrb5support0", "1.20.1-2+deb12u3|libkrb5support0"),
        ("12.2.0-14|gcc-12-base", "12.2.0-14+deb12u1|gcc-12-base"),
        ("12.2.0-14|libstdc++6", "12.2.0-14+deb12u1|libstdc++6"),
        ("1:4.13+dfsg1-1+b1|login", "1:4.13+dfsg1-1+deb12u1|login"),
        ("1:4.13+dfsg1-1+b1|passwd", "1:4.13+dfsg1-1+deb12u1|passwd"),
        ("3.0.15-1~deb12u1|libssl3", "3.0.16-1~deb12u1|libssl3"),
        ("3.0.15-1~deb12u1|openssl", "3.0.16-1~deb12u1|openssl"),
        ("4.19.0-2|libtasn1-6", "4.19.0-2+deb12u1|libtasn1-6"),
        ("5.36.0-7+deb12u1|perl-base", "5.36.0-7+deb12u2|perl-base"),
        ("5.4.1-0.2|liblzma5", "5.4.1-1|liblzma5"),
    }

    # Assert TrivyFix to TrivyImageFinding relationships
    assert check_rels(
        neo4j_session,
        "TrivyFix",
        "id",
        "TrivyImageFinding",
        "id",
        "APPLIES_TO",
        rel_direction_right=True,
    ) == {
        ("0.16.0|h11", "TIF|CVE-2025-43859"),
        ("1.20.1-2+deb12u3|krb5-locales", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u3|krb5-locales", "TIF|CVE-2025-24528"),
        ("1.20.1-2+deb12u3|libk5crypto3", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u3|libk5crypto3", "TIF|CVE-2025-24528"),
        ("1.20.1-2+deb12u3|libkrb5-3", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u3|libkrb5-3", "TIF|CVE-2025-24528"),
        ("1.20.1-2+deb12u3|libkrb5support0", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u3|libkrb5support0", "TIF|CVE-2025-24528"),
        ("12.2.0-14+deb12u1|gcc-12-base", "TIF|CVE-2023-4039"),
        ("12.2.0-14+deb12u1|libstdc++6", "TIF|CVE-2023-4039"),
        ("1:4.13+dfsg1-1+deb12u1|login", "TIF|CVE-2023-29383"),
        ("1:4.13+dfsg1-1+deb12u1|login", "TIF|CVE-2023-4641"),
        ("1:4.13+dfsg1-1+deb12u1|passwd", "TIF|CVE-2023-29383"),
        ("1:4.13+dfsg1-1+deb12u1|passwd", "TIF|CVE-2023-4641"),
        ("3.0.16-1~deb12u1|libssl3", "TIF|CVE-2024-13176"),
        ("3.0.16-1~deb12u1|openssl", "TIF|CVE-2024-13176"),
        ("4.19.0-2+deb12u1|libtasn1-6", "TIF|CVE-2024-12133"),
        ("5.36.0-7+deb12u2|perl-base", "TIF|CVE-2024-56406"),
        ("5.4.1-1|liblzma5", "TIF|CVE-2025-31115"),
    }

    # Assert Package to TrivyImageFinding relationships
    assert check_rels(
        neo4j_session,
        "Package",
        "id",
        "TrivyImageFinding",
        "id",
        "AFFECTS",
        rel_direction_right=False,
    ) == {
        ("0.14.0|h11", "TIF|CVE-2025-43859"),
        ("1.20.1-2+deb12u2|krb5-locales", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u2|krb5-locales", "TIF|CVE-2025-24528"),
        ("1.20.1-2+deb12u2|libk5crypto3", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u2|libk5crypto3", "TIF|CVE-2025-24528"),
        ("1.20.1-2+deb12u2|libkrb5-3", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u2|libkrb5-3", "TIF|CVE-2025-24528"),
        ("1.20.1-2+deb12u2|libkrb5support0", "TIF|CVE-2024-26462"),
        ("1.20.1-2+deb12u2|libkrb5support0", "TIF|CVE-2025-24528"),
        ("12.2.0-14|gcc-12-base", "TIF|CVE-2023-4039"),
        ("12.2.0-14|libstdc++6", "TIF|CVE-2023-4039"),
        ("1:4.13+dfsg1-1+b1|login", "TIF|CVE-2023-29383"),
        ("1:4.13+dfsg1-1+b1|login", "TIF|CVE-2023-4641"),
        ("1:4.13+dfsg1-1+b1|passwd", "TIF|CVE-2023-29383"),
        ("1:4.13+dfsg1-1+b1|passwd", "TIF|CVE-2023-4641"),
        ("3.0.15-1~deb12u1|libssl3", "TIF|CVE-2024-13176"),
        ("3.0.15-1~deb12u1|openssl", "TIF|CVE-2024-13176"),
        ("4.19.0-2|libtasn1-6", "TIF|CVE-2024-12133"),
        ("5.36.0-7+deb12u1|perl-base", "TIF|CVE-2024-56406"),
        ("5.4.1-0.2|liblzma5", "TIF|CVE-2025-31115"),
    }

    # Assert TrivyImageFinding to ECRImage relationships
    assert check_rels(
        neo4j_session,
        "TrivyImageFinding",
        "id",
        "ECRImage",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        (
            "TIF|CVE-2023-29383",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2023-4039",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2023-4641",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2024-12133",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2024-13176",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2024-26462",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2024-56406",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2025-24528",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2025-31115",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "TIF|CVE-2025-43859",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
    }
