from unittest.mock import MagicMock
from unittest.mock import patch

from googleapiclient.errors import HttpError

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


@patch.object(
    cartography.intel.gcp.workload_identity,
    "get_workload_identity_pools",
    return_value=wif_data.LIST_WORKLOAD_IDENTITY_POOLS_RESPONSE[
        "workloadIdentityPools"
    ],
)
def test_sync_skips_provider_cleanup_on_partial_failure(_mock_pools, neo4j_session):
    """
    When listing providers fails for at least one pool, the provider cleanup
    job must be skipped so providers we did not re-ingest are not deleted.
    Pool cleanup remains safe because the pool list call succeeded.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    stale_provider_id = (
        f"projects/{wif_data.TEST_PROJECT_NUMBER}/locations/global/"
        "workloadIdentityPools/aws-pool/providers/stale-aws"
    )
    aws_pool_id = (
        f"projects/{wif_data.TEST_PROJECT_NUMBER}/locations/global/"
        "workloadIdentityPools/aws-pool"
    )
    # Seed a stale provider that would be deleted by a full cleanup pass.
    neo4j_session.run(
        """
        MERGE (p:GCPWorkloadIdentityProvider:IdentityProvider{id:$pid})
        SET p.lastupdated = $stale_tag, p.name = $pid, p.pool_name = $pool
        """,
        pid=stale_provider_id,
        pool=aws_pool_id,
        stale_tag=TEST_UPDATE_TAG - 1,
    )

    def fail_on_aws_pool(_iam_client, pool_name):
        if pool_name.endswith("/aws-pool"):
            raise HttpError(
                resp=MagicMock(status=500, reason="Internal"),
                content=b"boom",
            )
        return wif_data.fake_get_providers(_iam_client, pool_name)

    with patch.object(
        cartography.intel.gcp.workload_identity,
        "get_workload_identity_providers",
        side_effect=fail_on_aws_pool,
    ):
        cartography.intel.gcp.workload_identity.sync(
            neo4j_session,
            MagicMock(),
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            COMMON_JOB_PARAMS,
        )

    # Stale provider must still exist because provider cleanup was skipped.
    assert check_nodes(neo4j_session, "GCPWorkloadIdentityProvider", ["id"]) == {
        (
            f"projects/{wif_data.TEST_PROJECT_NUMBER}/locations/global/"
            "workloadIdentityPools/github-pool/providers/github-oidc",
        ),
        (stale_provider_id,),
    }


def test_transform_providers_marks_disabled_as_not_enabled():
    """
    An ACTIVE-but-disabled provider must report enabled=false so cross-
    provider IdentityProvider queries do not see it as active.
    """
    pool = {
        "name": "projects/p/locations/global/workloadIdentityPools/x",
        "state": "ACTIVE",
        "disabled": False,
    }
    raw = [
        {
            "name": "providers/active-enabled",
            "state": "ACTIVE",
            "disabled": False,
            "oidc": {"issuerUri": "https://example"},
        },
        {
            "name": "providers/active-disabled",
            "state": "ACTIVE",
            "disabled": True,
            "oidc": {"issuerUri": "https://example"},
        },
        {
            "name": "providers/deleted",
            "state": "DELETED",
            "disabled": False,
            "oidc": {"issuerUri": "https://example"},
        },
    ]
    transformed = cartography.intel.gcp.workload_identity.transform_providers(
        raw, pool, "p"
    )
    by_id = {p["id"]: p for p in transformed}
    assert by_id["providers/active-enabled"]["enabled"] is True
    assert by_id["providers/active-disabled"]["enabled"] is False
    assert by_id["providers/deleted"]["enabled"] is False


def test_transform_providers_disabled_pool_disables_all_providers():
    """
    A disabled pool blocks federation entirely. Even an ACTIVE+enabled
    provider under a disabled pool must report enabled=false.
    """
    disabled_pool = {
        "name": "projects/p/locations/global/workloadIdentityPools/x",
        "state": "ACTIVE",
        "disabled": True,
    }
    deleted_pool = {
        "name": "projects/p/locations/global/workloadIdentityPools/y",
        "state": "DELETED",
        "disabled": False,
    }
    raw = [
        {
            "name": "providers/active-enabled",
            "state": "ACTIVE",
            "disabled": False,
            "oidc": {"issuerUri": "https://example"},
        },
    ]
    for pool in (disabled_pool, deleted_pool):
        transformed = cartography.intel.gcp.workload_identity.transform_providers(
            raw, pool, "p"
        )
        assert transformed[0]["enabled"] is False


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
