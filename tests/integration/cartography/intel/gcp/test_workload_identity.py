from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.policy_bindings
import cartography.intel.gcp.workload_identity
import tests.data.gcp.workload_identity as wif_data
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_ID = "project-abc"
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {
    "PROJECT_ID": TEST_PROJECT_ID,
    "UPDATE_TAG": TEST_UPDATE_TAG,
}


def _create_test_project(neo4j_session, project_id: str, update_tag: int) -> None:
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $gcp_update_tag
        """,
        ProjectId=project_id,
        gcp_update_tag=update_tag,
    )


@patch.object(
    cartography.intel.gcp.workload_identity,
    "get_workload_identity_providers",
    side_effect=wif_data.fake_get_providers,
)
@patch.object(
    cartography.intel.gcp.workload_identity,
    "get_workload_identity_pools",
    return_value=wif_data.LIST_WORKLOAD_IDENTITY_POOLS_RESPONSE[
        "workloadIdentityPools"
    ],
)
def test_sync_workload_identity_pools_and_providers(
    _mock_pools, _mock_providers, neo4j_session
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.workload_identity.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    assert check_nodes(neo4j_session, "GCPWorkloadIdentityPool", ["id"]) == {
        (
            f"projects/{wif_data.TEST_PROJECT_NUMBER}/locations/global/"
            "workloadIdentityPools/github-pool",
        ),
        (
            f"projects/{wif_data.TEST_PROJECT_NUMBER}/locations/global/"
            "workloadIdentityPools/aws-pool",
        ),
    }

    assert check_nodes(
        neo4j_session, "GCPWorkloadIdentityProvider", ["id", "protocol"]
    ) == {
        (
            f"projects/{wif_data.TEST_PROJECT_NUMBER}/locations/global/"
            "workloadIdentityPools/github-pool/providers/github-oidc",
            "OIDC",
        ),
        (
            f"projects/{wif_data.TEST_PROJECT_NUMBER}/locations/global/"
            "workloadIdentityPools/aws-pool/providers/aws-prod",
            "AWS",
        ),
    }

    # Pool ↔ Project
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPWorkloadIdentityPool",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_PROJECT_ID,
            f"projects/{wif_data.TEST_PROJECT_NUMBER}/locations/global/"
            "workloadIdentityPools/github-pool",
        ),
        (
            TEST_PROJECT_ID,
            f"projects/{wif_data.TEST_PROJECT_NUMBER}/locations/global/"
            "workloadIdentityPools/aws-pool",
        ),
    }

    # Provider ↔ Pool
    assert check_rels(
        neo4j_session,
        "GCPWorkloadIdentityProvider",
        "id",
        "GCPWorkloadIdentityPool",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (
            f"projects/{wif_data.TEST_PROJECT_NUMBER}/locations/global/"
            "workloadIdentityPools/github-pool/providers/github-oidc",
            f"projects/{wif_data.TEST_PROJECT_NUMBER}/locations/global/"
            "workloadIdentityPools/github-pool",
        ),
        (
            f"projects/{wif_data.TEST_PROJECT_NUMBER}/locations/global/"
            "workloadIdentityPools/aws-pool/providers/aws-prod",
            f"projects/{wif_data.TEST_PROJECT_NUMBER}/locations/global/"
            "workloadIdentityPools/aws-pool",
        ),
    }

    # IdentityProvider ontology label
    assert check_nodes(neo4j_session, "IdentityProvider", ["id"]) == {
        (
            f"projects/{wif_data.TEST_PROJECT_NUMBER}/locations/global/"
            "workloadIdentityPools/github-pool/providers/github-oidc",
        ),
        (
            f"projects/{wif_data.TEST_PROJECT_NUMBER}/locations/global/"
            "workloadIdentityPools/aws-pool/providers/aws-prod",
        ),
    }


def test_transform_bindings_extracts_wif_pools():
    """
    The policy binding transformer should extract the pool resource name from
    both ``principal://`` and ``principalSet://`` URIs and skip the per-subject
    detail.
    """
    raw = {
        "project_id": TEST_PROJECT_ID,
        "policy_results": [
            {
                "policies": [
                    {
                        "attached_resource": (
                            f"//cloudresourcemanager.googleapis.com/projects/{TEST_PROJECT_ID}"
                        ),
                        "policy": {
                            "bindings": [
                                {
                                    "role": "roles/iam.workloadIdentityUser",
                                    "members": [
                                        "serviceAccount:sa@example.iam.gserviceaccount.com",
                                        *wif_data.WIF_BINDING_MEMBERS,
                                    ],
                                },
                            ],
                        },
                    },
                ],
            },
        ],
    }
    bindings = cartography.intel.gcp.policy_bindings.transform_bindings(raw)
    assert len(bindings) == 1
    binding = bindings[0]
    assert binding["wif_pools"] == [wif_data.WIF_GITHUB_POOL_ID]
    assert binding["members"] == ["sa@example.iam.gserviceaccount.com"]
