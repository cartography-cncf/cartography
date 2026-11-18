from copy import deepcopy
from typing import Any

import pytest

import cartography.intel.sentra
from cartography.config import Config
from cartography.intel.sentra import api
from tests.data.sentra import ALERTS
from tests.data.sentra import API_KEY
from tests.data.sentra import API_URL
from tests.data.sentra import CURRENT_USER
from tests.data.sentra import DATA_CLASS_AWS_KEY_ID
from tests.data.sentra import DATA_CLASS_EMAIL_ID
from tests.data.sentra import DATA_CLASSES
from tests.data.sentra import DATA_STORES
from tests.data.sentra import DISABLED_POLICY_ID
from tests.data.sentra import POLICIES
from tests.data.sentra import RDS_INSTANCE_ARN
from tests.data.sentra import RDS_STORE_ID
from tests.data.sentra import ROLE_ALERT_ID
from tests.data.sentra import ROLE_ARN
from tests.data.sentra import ROLE_POLICY_ID
from tests.data.sentra import S3_BUCKET_NAME
from tests.data.sentra import S3_STORE_ID
from tests.data.sentra import SNOWFLAKE_STORE_ID
from tests.data.sentra import STORE_ALERT_ID
from tests.data.sentra import STORE_POLICY_ID
from tests.data.sentra import TENANT_ID
from tests.data.sentra import VIOLATED_OBJECTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
SECOND_UPDATE_TAG = 123456790


@pytest.fixture(autouse=True)
def reset_graph(neo4j_session):
    def _reset():
        neo4j_session.run(
            """
            MATCH (n)
            WHERE n:SentraTenant OR n:SentraDataClass OR n:SentraDataStore
               OR n:SentraPolicy OR n:SentraAlert
            DETACH DELETE n
            """,
        )
        neo4j_session.run(
            "MATCH (n:AWSS3Bucket {id: $bucket}) DETACH DELETE n",
            bucket=S3_BUCKET_NAME,
        )
        neo4j_session.run(
            "MATCH (n:AWSRDSInstance {id: $arn}) DETACH DELETE n",
            arn=RDS_INSTANCE_ARN,
        )
        neo4j_session.run("MATCH (n:AWSRole {id: $arn}) DETACH DELETE n", arn=ROLE_ARN)
        neo4j_session.run(
            "MATCH (n:ModuleSyncMetadata {id: $id}) DETACH DELETE n",
            id=f"SentraTenant_{TENANT_ID}_SentraData",
        )

    _reset()
    yield
    _reset()


def _config(update_tag: int) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        sentra_api_key=API_KEY,
        sentra_api_url=API_URL,
    )


def _patch_sentra_api(
    mocker,
    *,
    data_stores: list[dict[str, Any]] = DATA_STORES,
    policies: list[dict[str, Any]] = POLICIES,
    alerts: list[dict[str, Any]] = ALERTS,
    violated_objects: dict[str, list[dict[str, Any]]] = VIOLATED_OBJECTS,
) -> None:
    rows_by_path = {
        api.DATA_CLASSES_SEARCH_PATH: DATA_CLASSES,
        api.DATA_STORES_SEARCH_PATH: data_stores,
        api.POLICIES_SEARCH_PATH: policies,
        api.ALERTS_SEARCH_PATH: alerts,
    }

    def post_search(_session, _api_url, path, body):
        # Mirrors Sentra's keyset pagination: rows ordered by ID, after the cursor.
        rows = sorted(rows_by_path[path], key=lambda row: row["id"])
        cursor = body.get("start_from_id")
        if cursor is not None:
            rows = [row for row in rows if row["id"] > cursor]
        return {"items": deepcopy(rows[: body["limit"]]), "all_matches_count": None}

    def get_violated_objects_page(_session, _api_url, alert_id, offset, limit):
        objects = violated_objects.get(alert_id, [])
        return {"items": deepcopy(objects[offset : offset + limit])}

    mocker.patch.object(api, "get_current_user", return_value=deepcopy(CURRENT_USER))
    mocker.patch.object(api, "post_search", side_effect=post_search)
    mocker.patch.object(
        api,
        "get_violated_objects_page",
        side_effect=get_violated_objects_page,
    )


def _seed_aws_resources(neo4j_session) -> None:
    neo4j_session.run(
        "MERGE (b:AWSS3Bucket {id: $bucket}) SET b.name = $bucket",
        bucket=S3_BUCKET_NAME,
    )
    neo4j_session.run(
        "MERGE (i:AWSRDSInstance {id: $arn}) SET i.arn = $arn",
        arn=RDS_INSTANCE_ARN,
    )
    neo4j_session.run("MERGE (r:AWSRole {id: $arn}) SET r.arn = $arn", arn=ROLE_ARN)


def test_sync_loads_sentra_data_and_links_aws_resources(neo4j_session, mocker):
    # Arrange
    _seed_aws_resources(neo4j_session)
    _patch_sentra_api(mocker)

    # Act
    cartography.intel.sentra.start_sentra_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )

    # Assert
    assert check_nodes(neo4j_session, "SentraTenant", ["id", "name"]) == {
        (TENANT_ID, "Example Org"),
    }
    assert check_nodes(neo4j_session, "SentraDataClass", ["id", "category"]) == {
        (DATA_CLASS_EMAIL_ID, "Personal"),
        (DATA_CLASS_AWS_KEY_ID, "Credentials"),
    }
    assert check_nodes(
        neo4j_session,
        "SentraDataStore",
        ["id", "hosting_service", "sensitivity_level"],
    ) == {
        (S3_STORE_ID, "s3", 3),
        (RDS_STORE_ID, "rds", 2),
        (SNOWFLAKE_STORE_ID, "snowflake", 0),
    }
    assert check_nodes(
        neo4j_session,
        "SentraPolicy",
        ["id", "status", "risk_type"],
    ) == {
        (STORE_POLICY_ID, "enabled", "exposed_data"),
        (ROLE_POLICY_ID, "enabled", "excessive_access"),
        (DISABLED_POLICY_ID, "disabled", "shadow_data"),
    }
    assert neo4j_session.run(
        "MATCH (p:SentraPolicy {id: $id}) RETURN p.frameworks AS frameworks",
        id=STORE_POLICY_ID,
    ).single()["frameworks"] == ["SOC2", "PCI"]
    assert check_nodes(
        neo4j_session,
        "SentraAlert",
        ["id", "severity", "status", "entity_type"],
    ) == {
        (STORE_ALERT_ID, "critical", "opened", "STORE"),
        (ROLE_ALERT_ID, "high", "in_progress", "IAM_ROLE"),
    }

    tenant_resources = set()
    for label in ("SentraDataClass", "SentraDataStore", "SentraPolicy", "SentraAlert"):
        tenant_resources |= check_rels(
            neo4j_session,
            "SentraTenant",
            "id",
            label,
            "id",
            "RESOURCE",
        )
    assert tenant_resources == {
        (TENANT_ID, DATA_CLASS_EMAIL_ID),
        (TENANT_ID, DATA_CLASS_AWS_KEY_ID),
        (TENANT_ID, S3_STORE_ID),
        (TENANT_ID, RDS_STORE_ID),
        (TENANT_ID, SNOWFLAKE_STORE_ID),
        (TENANT_ID, STORE_POLICY_ID),
        (TENANT_ID, ROLE_POLICY_ID),
        (TENANT_ID, DISABLED_POLICY_ID),
        (TENANT_ID, STORE_ALERT_ID),
        (TENANT_ID, ROLE_ALERT_ID),
    }

    assert check_rels(
        neo4j_session,
        "SentraDataStore",
        "id",
        "SentraDataClass",
        "id",
        "CONTAINS",
    ) == {
        (S3_STORE_ID, DATA_CLASS_EMAIL_ID),
        (S3_STORE_ID, DATA_CLASS_AWS_KEY_ID),
        (RDS_STORE_ID, DATA_CLASS_EMAIL_ID),
    }

    assert check_rels(
        neo4j_session,
        "SentraDataStore",
        "id",
        "AWSS3Bucket",
        "id",
        "MONITORS",
    ) == {(S3_STORE_ID, S3_BUCKET_NAME)}
    assert check_rels(
        neo4j_session,
        "SentraDataStore",
        "id",
        "AWSRDSInstance",
        "id",
        "MONITORS",
    ) == {(RDS_STORE_ID, RDS_INSTANCE_ARN)}

    assert check_rels(
        neo4j_session,
        "SentraAlert",
        "id",
        "SentraDataStore",
        "id",
        "AFFECTS",
    ) == {(STORE_ALERT_ID, S3_STORE_ID)}
    # The store alert also links directly to the S3 bucket that its store represents.
    assert check_rels(
        neo4j_session,
        "SentraAlert",
        "id",
        "AWSS3Bucket",
        "id",
        "AFFECTS",
    ) == {(STORE_ALERT_ID, S3_BUCKET_NAME)}
    assert (
        check_rels(
            neo4j_session,
            "SentraAlert",
            "id",
            "AWSRDSInstance",
            "id",
            "AFFECTS",
        )
        == set()
    )
    assert check_rels(
        neo4j_session,
        "SentraAlert",
        "id",
        "SentraDataClass",
        "id",
        "INVOLVES",
    ) == {
        (STORE_ALERT_ID, DATA_CLASS_AWS_KEY_ID),
        (STORE_ALERT_ID, DATA_CLASS_EMAIL_ID),
    }
    assert check_rels(
        neo4j_session,
        "SentraAlert",
        "id",
        "SentraPolicy",
        "id",
        "GOVERNED_BY",
    ) == {
        (STORE_ALERT_ID, STORE_POLICY_ID),
        (ROLE_ALERT_ID, ROLE_POLICY_ID),
    }
    assert check_rels(
        neo4j_session,
        "SentraPolicy",
        "id",
        "SentraDataClass",
        "id",
        "CLASSIFICATION",
    ) == {
        (STORE_POLICY_ID, DATA_CLASS_AWS_KEY_ID),
        (DISABLED_POLICY_ID, DATA_CLASS_EMAIL_ID),
    }
    assert check_rels(
        neo4j_session,
        "SentraAlert",
        "id",
        "AWSRole",
        "arn",
        "AFFECTS",
    ) == {(ROLE_ALERT_ID, ROLE_ARN)}


def test_sync_applies_ontology_labels(neo4j_session, mocker):
    # Arrange
    _patch_sentra_api(mocker)

    # Act
    cartography.intel.sentra.start_sentra_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )

    # Assert
    assert check_nodes(neo4j_session, "Tenant", ["id", "_ont_name"]) >= {
        (TENANT_ID, "Example Org"),
    }
    assert (
        {
            (record["id"], record["severity"], record["status"])
            for record in neo4j_session.run(
                """
            MATCH (a:SentraAlert:SecurityIssue)
            RETURN a.id AS id, a._ont_severity AS severity, a._ont_status AS status
            """,
            )
        }
        == {
            (STORE_ALERT_ID, "critical", "open"),
            (ROLE_ALERT_ID, "high", "open"),
        }
    )


def test_sync_removes_resolved_alerts_and_deleted_stores(neo4j_session, mocker):
    # Arrange
    _patch_sentra_api(mocker)
    cartography.intel.sentra.start_sentra_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )
    # Sentra resolved the role alert, the Snowflake store and the disabled policy
    # were deleted, and the object that held email addresses no longer violates
    # the store alert's policy.
    _patch_sentra_api(
        mocker,
        data_stores=[s for s in DATA_STORES if s["id"] != SNOWFLAKE_STORE_ID],
        policies=[p for p in POLICIES if p["id"] != DISABLED_POLICY_ID],
        alerts=[a for a in ALERTS if a["id"] != ROLE_ALERT_ID],
        violated_objects={STORE_ALERT_ID: VIOLATED_OBJECTS[STORE_ALERT_ID][:1]},
    )

    # Act
    cartography.intel.sentra.start_sentra_ingestion(
        neo4j_session,
        _config(SECOND_UPDATE_TAG),
    )

    # Assert
    assert check_nodes(neo4j_session, "SentraAlert", ["id"]) == {(STORE_ALERT_ID,)}
    assert check_nodes(neo4j_session, "SentraDataStore", ["id"]) == {
        (S3_STORE_ID,),
        (RDS_STORE_ID,),
    }
    assert check_nodes(neo4j_session, "SentraPolicy", ["id"]) == {
        (STORE_POLICY_ID,),
        (ROLE_POLICY_ID,),
    }
    assert check_nodes(neo4j_session, "SentraTenant", ["id"]) == {(TENANT_ID,)}
    assert check_rels(
        neo4j_session,
        "SentraAlert",
        "id",
        "SentraDataClass",
        "id",
        "INVOLVES",
    ) == {(STORE_ALERT_ID, DATA_CLASS_AWS_KEY_ID)}


def test_sync_links_alert_to_aws_resources_of_violated_object_stores(
    neo4j_session,
    mocker,
):
    # Arrange
    _seed_aws_resources(neo4j_session)
    rds_object = {
        "id": "object-orders-export",
        "asset_id": "asset-orders-exports",
        "asset_name": "orders_export",
        "asset_type": "TABLE",
        "store_id": RDS_STORE_ID,
        "store_name": "orders",
        "data_classes": [
            {
                "id": DATA_CLASS_EMAIL_ID,
                "name": "Email Address",
                "category": "Personal",
            },
        ],
    }
    _patch_sentra_api(
        mocker,
        violated_objects={
            STORE_ALERT_ID: [*VIOLATED_OBJECTS[STORE_ALERT_ID], rds_object],
        },
    )
    cartography.intel.sentra.start_sentra_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )
    assert check_rels(
        neo4j_session,
        "SentraAlert",
        "id",
        "AWSRDSInstance",
        "id",
        "AFFECTS",
    ) == {(STORE_ALERT_ID, RDS_INSTANCE_ARN)}
    # The object in the RDS store no longer violates the policy.
    _patch_sentra_api(mocker)

    # Act
    cartography.intel.sentra.start_sentra_ingestion(
        neo4j_session,
        _config(SECOND_UPDATE_TAG),
    )

    # Assert
    assert (
        check_rels(
            neo4j_session,
            "SentraAlert",
            "id",
            "AWSRDSInstance",
            "id",
            "AFFECTS",
        )
        == set()
    )
    assert check_rels(
        neo4j_session,
        "SentraAlert",
        "id",
        "AWSS3Bucket",
        "id",
        "AFFECTS",
    ) == {(STORE_ALERT_ID, S3_BUCKET_NAME)}
