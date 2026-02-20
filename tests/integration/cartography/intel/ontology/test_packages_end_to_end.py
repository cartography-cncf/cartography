import json
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ecr
import cartography.intel.ontology.packages
import tests.data.aws.ecr
from cartography.intel.syft import sync_single_syft
from cartography.intel.trivy import sync_trivy_from_dir
from tests.data.trivy.trivy_sample import TRIVY_SAMPLE
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789
TEST_REGION = "us-east-1"
TEST_IMAGE_DIGEST = (
    "sha256:0000000000000000000000000000000000000000000000000000000000000000"
)


# Minimal Syft payload overlapping Trivy packages in TRIVY_SAMPLE:
# - h11@0.14.0 (vulnerable in trivy_sample)
# - urllib3@2.0.7 (non-vulnerable in trivy_sample)
# plus a dependency edge: h11 depends on urllib3.
SYFT_TRIVY_OVERLAP_SAMPLE = {
    "artifacts": [
        {
            "id": "pkg:pypi/h11@0.14.0",
            "name": "h11",
            "version": "0.14.0",
            "type": "pypi",
            "foundBy": "python-package-cataloger",
            "language": "python",
            "purl": "pkg:pypi/h11@0.14.0",
        },
        {
            "id": "pkg:pypi/urllib3@2.0.7",
            "name": "urllib3",
            "version": "2.0.7",
            "type": "pypi",
            "foundBy": "python-package-cataloger",
            "language": "python",
            "purl": "pkg:pypi/urllib3@2.0.7",
        },
    ],
    "artifactRelationships": [
        {
            "parent": "pkg:pypi/urllib3@2.0.7",
            "child": "pkg:pypi/h11@0.14.0",
            "type": "dependency-of",
        },
    ],
    "source": {
        "type": "image",
        "target": {"digest": TEST_IMAGE_DIGEST},
    },
}


@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repositories",
    return_value=tests.data.aws.ecr.DESCRIBE_REPOSITORIES["repositories"][2:],
)
@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repository_images",
    return_value=tests.data.aws.ecr.LIST_REPOSITORY_IMAGES[
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository"
    ][:1],
)
def test_packages_end_to_end_from_trivy_syft_to_ontology(
    _mock_get_images,
    _mock_get_repos,
    tmp_path,
    neo4j_session,
):
    """
    Full integration path:
    ECR + Trivy + Syft -> ontology Package graph with DEPLOYED, AFFECTS,
    DEPENDS_ON, and fix-path connectivity via TrivyPackage.
    """
    # Ensure clean state for labels used by this test.
    neo4j_session.run(
        """
        MATCH (n)
        WHERE n:Package OR n:TrivyPackage OR n:SyftPackage OR n:TrivyFix
           OR n:TrivyImageFinding OR n:ECRImage OR n:ECRRepositoryImage OR n:ECRRepository
        DETACH DELETE n
        """,
    )

    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # 1) Seed ECR image graph used by Trivy DEPLOYED/AFFECTS matching.
    boto3_session = MagicMock()
    cartography.intel.aws.ecr.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # 2) Ingest Trivy scan data from sample.
    scan_path = tmp_path / "scan.json"
    scan_path.write_text(json.dumps(TRIVY_SAMPLE))
    sync_trivy_from_dir(
        neo4j_session,
        str(tmp_path),
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # 3) Ingest Syft data with overlapping package IDs (h11/urllib3).
    sync_single_syft(
        neo4j_session,
        SYFT_TRIVY_OVERLAP_SAMPLE,
        TEST_UPDATE_TAG,
    )

    # 4) Build canonical Package ontology nodes and propagated relationships.
    cartography.intel.ontology.packages.sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert canonical package is linked to both Trivy and Syft source nodes.
    assert check_rels(
        neo4j_session,
        "Package",
        "id",
        "TrivyPackage",
        "normalized_id",
        "DETECTED_AS",
        rel_direction_right=True,
    ) >= {("pypi|h11|0.14.0", "pypi|h11|0.14.0")}
    assert check_rels(
        neo4j_session,
        "Package",
        "id",
        "SyftPackage",
        "normalized_id",
        "DETECTED_AS",
        rel_direction_right=True,
    ) >= {("pypi|h11|0.14.0", "pypi|h11|0.14.0")}

    # Assert package-to-image deployment propagation.
    assert check_rels(
        neo4j_session,
        "Package",
        "id",
        "ECRImage",
        "id",
        "DEPLOYED",
        rel_direction_right=True,
    ) >= {("pypi|h11|0.14.0", TEST_IMAGE_DIGEST)}

    # Assert vulnerability propagation to canonical Package.
    assert check_rels(
        neo4j_session,
        "TrivyImageFinding",
        "id",
        "Package",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) >= {("TIF|CVE-2025-43859", "pypi|h11|0.14.0")}

    # Assert canonical dependency tree propagation from SyftPackage graph.
    assert check_rels(
        neo4j_session,
        "Package",
        "id",
        "Package",
        "id",
        "DEPENDS_ON",
        rel_direction_right=True,
    ) >= {("pypi|h11|0.14.0", "pypi|urllib3|2.0.7")}

    # Assert fix connectivity exists for canonical package via TrivyPackage bridge.
    fix_row = neo4j_session.run(
        """
        MATCH (p:Package {id: 'pypi|h11|0.14.0'})
              -[:DETECTED_AS]->(:TrivyPackage)
              -[:SHOULD_UPDATE_TO]->(fix:TrivyFix)
        RETURN collect(DISTINCT fix.id) AS fix_ids
        """,
    ).single()
    assert "0.16.0|h11" in fix_row["fix_ids"]
