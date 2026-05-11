import json
from unittest.mock import mock_open
from unittest.mock import patch

from cartography.config import Config
from cartography.intel.terraform import start_terraform_ingestion
from tests.data.terraform.state import LINEAGE
from tests.data.terraform.state import SAMPLE_STATE_FILE
from tests.data.terraform.state import TEST_EKS_CLUSTER_ARN
from tests.data.terraform.state import TEST_EKS_CLUSTER_NAME
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _make_config(source: str = "/tmp/states/") -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        terraform_state_source=source,
    )


def _create_test_s3_bucket(neo4j_session) -> None:
    neo4j_session.run(
        """
        MERGE (b:S3Bucket {id: $id})
        SET b.name = $name, b.lastupdated = $update_tag
        """,
        id="my-test-logs-bucket",
        name="my-test-logs-bucket",
        update_tag=TEST_UPDATE_TAG,
    )


@patch(
    "cartography.intel.common.object_store.LocalReportReader.list_reports",
    return_value=[],
)
def test_terraform_no_state_files(mock_list, neo4j_session):
    config = _make_config()
    start_terraform_ingestion(neo4j_session, config)


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(SAMPLE_STATE_FILE).encode("utf-8"),
)
@patch("cartography.intel.common.object_store.LocalReportReader.list_reports")
def test_terraform_workspace_loaded(mock_list, mock_file, neo4j_session):
    from cartography.intel.common.object_store import ReportRef

    mock_list.return_value = [
        ReportRef(uri="/tmp/states/test.tfstate", name="test.tfstate")
    ]
    config = _make_config()
    start_terraform_ingestion(neo4j_session, config)

    result = check_nodes(
        neo4j_session, "TerraformWorkspace", ["id", "terraform_version", "serial"]
    )
    assert (LINEAGE, "1.14.2", 100) in result


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(SAMPLE_STATE_FILE).encode("utf-8"),
)
@patch("cartography.intel.common.object_store.LocalReportReader.list_reports")
def test_terraform_resources_loaded(mock_list, mock_file, neo4j_session):
    from cartography.intel.common.object_store import ReportRef

    mock_list.return_value = [
        ReportRef(uri="/tmp/states/test.tfstate", name="test.tfstate")
    ]
    config = _make_config()
    start_terraform_ingestion(neo4j_session, config)

    result = check_nodes(
        neo4j_session, "TerraformResource", ["id", "resource_type", "mode"]
    )
    assert (
        f"{LINEAGE}/aws_caller_identity.current",
        "aws_caller_identity",
        "data",
    ) in result
    assert (f"{LINEAGE}/aws_iam_policy.sops", "aws_iam_policy", "managed") in result
    assert (f"{LINEAGE}/aws_s3_bucket.logs", "aws_s3_bucket", "managed") in result


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(SAMPLE_STATE_FILE).encode("utf-8"),
)
@patch("cartography.intel.common.object_store.LocalReportReader.list_reports")
def test_workspace_contains_resources(mock_list, mock_file, neo4j_session):
    from cartography.intel.common.object_store import ReportRef

    mock_list.return_value = [
        ReportRef(uri="/tmp/states/test.tfstate", name="test.tfstate")
    ]
    config = _make_config()
    start_terraform_ingestion(neo4j_session, config)

    result = check_rels(
        neo4j_session,
        "TerraformWorkspace",
        "id",
        "TerraformResource",
        "resource_type",
        "CONTAINS",
        rel_direction_right=True,
    )
    assert (LINEAGE, "aws_s3_bucket") in result
    assert (LINEAGE, "aws_iam_policy") in result


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(SAMPLE_STATE_FILE).encode("utf-8"),
)
@patch("cartography.intel.common.object_store.LocalReportReader.list_reports")
def test_outputs_sensitive_value_redacted(mock_list, mock_file, neo4j_session):
    from cartography.intel.common.object_store import ReportRef

    mock_list.return_value = [
        ReportRef(uri="/tmp/states/test.tfstate", name="test.tfstate")
    ]
    config = _make_config()
    start_terraform_ingestion(neo4j_session, config)

    result = check_nodes(
        neo4j_session, "TerraformOutput", ["output_name", "sensitive", "value_json"]
    )
    assert ("cluster_name", False, '"enbuild_eks_dev"') in result
    sensitive_rows = {r for r in result if r[0] == "kms_key_id"}
    assert len(sensitive_rows) == 1
    assert sensitive_rows.pop()[2] is None


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(SAMPLE_STATE_FILE).encode("utf-8"),
)
@patch("cartography.intel.common.object_store.LocalReportReader.list_reports")
def test_manages_edge_to_s3_bucket(mock_list, mock_file, neo4j_session):
    from cartography.intel.common.object_store import ReportRef

    mock_list.return_value = [
        ReportRef(uri="/tmp/states/test.tfstate", name="test.tfstate")
    ]
    _create_test_s3_bucket(neo4j_session)
    config = _make_config()
    start_terraform_ingestion(neo4j_session, config)

    result = check_rels(
        neo4j_session,
        "TerraformResourceInstance",
        "id",
        "S3Bucket",
        "id",
        "MANAGES",
        rel_direction_right=True,
    )
    assert (f"{LINEAGE}/aws_s3_bucket.logs", "my-test-logs-bucket") in result


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(SAMPLE_STATE_FILE).encode("utf-8"),
)
@patch("cartography.intel.common.object_store.LocalReportReader.list_reports")
def test_manages_edge_to_eks_cluster_uses_arn(mock_list, mock_file, neo4j_session):
    from cartography.intel.common.object_store import ReportRef

    # Arrange: seed an EKSCluster node whose id is the ARN (as AWS discovery stores it)
    neo4j_session.run(
        "MERGE (c:EKSCluster {id: $arn}) SET c.name = $name, c.lastupdated = $tag",
        arn=TEST_EKS_CLUSTER_ARN,
        name=TEST_EKS_CLUSTER_NAME,
        tag=TEST_UPDATE_TAG,
    )
    mock_list.return_value = [
        ReportRef(uri="/tmp/states/test.tfstate", name="test.tfstate")
    ]
    config = _make_config()

    # Act
    start_terraform_ingestion(neo4j_session, config)

    # Assert: MANAGES edge connects to the node via ARN, not cluster name
    result = check_rels(
        neo4j_session,
        "TerraformResourceInstance",
        "id",
        "EKSCluster",
        "id",
        "MANAGES",
        rel_direction_right=True,
    )
    assert (f"{LINEAGE}/aws_eks_cluster.main", TEST_EKS_CLUSTER_ARN) in result


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(SAMPLE_STATE_FILE).encode("utf-8"),
)
@patch("cartography.intel.common.object_store.LocalReportReader.list_reports")
def test_no_manages_edge_when_target_absent(mock_list, mock_file, neo4j_session):
    from cartography.intel.common.object_store import ReportRef

    # Arrange: ensure no S3Bucket nodes exist so MANAGES edge cannot be created
    neo4j_session.run("MATCH (b:S3Bucket) DETACH DELETE b")

    mock_list.return_value = [
        ReportRef(uri="/tmp/states/test.tfstate", name="test.tfstate")
    ]
    config = _make_config()
    # Act
    start_terraform_ingestion(neo4j_session, config)

    result = check_rels(
        neo4j_session,
        "TerraformResourceInstance",
        "id",
        "S3Bucket",
        "id",
        "MANAGES",
    )
    assert len(result) == 0
