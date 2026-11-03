from unittest.mock import ANY
from unittest.mock import Mock
from unittest.mock import patch

from requests import Response
from scaleway.mnq.v1beta1 import SqsInfo
from scaleway.mnq.v1beta1 import SqsInfoStatus
from scaleway_core.api import ScalewayException

import cartography.intel.scaleway.mnq.sqs
from cartography.intel.scaleway.mnq.sqs import transform_credentials
from cartography.intel.scaleway.mnq.sqs import transform_namespaces
from tests.data.scaleway.mnq import SCALEWAY_MNQ_SQS_CREDENTIALS
from tests.data.scaleway.mnq import SCALEWAY_MNQ_SQS_INFO
from tests.data.scaleway.mnq import TEST_CREDENTIAL_ID
from tests.data.scaleway.mnq import TEST_PROJECT_ID


def test_transform_namespaces_uses_project_and_region_as_id():
    rows = transform_namespaces(SCALEWAY_MNQ_SQS_INFO)

    assert rows[TEST_PROJECT_ID][0]["id"] == f"{TEST_PROJECT_ID}/fr-par"
    assert rows[TEST_PROJECT_ID][0]["status"] == "enabled"


def test_transform_credentials_discards_the_secret_key_and_checksum():
    """
    Scaleway's list API returns each credential's full secret_key alongside its
    metadata - that value must never reach the graph.
    """
    rows = transform_credentials(SCALEWAY_MNQ_SQS_CREDENTIALS)

    row = rows[TEST_PROJECT_ID][0]
    assert row["id"] == TEST_CREDENTIAL_ID
    assert "secret_key" not in row
    assert "secret_checksum" not in row


def test_transform_credentials_flattens_permissions():
    rows = transform_credentials(SCALEWAY_MNQ_SQS_CREDENTIALS)

    row = rows[TEST_PROJECT_ID][0]
    assert row["can_publish"] is True
    assert row["can_receive"] is True
    assert row["can_manage"] is False
    assert "permissions" not in row


def test_transform_credentials_links_to_the_namespace_by_project_and_region():
    rows = transform_credentials(SCALEWAY_MNQ_SQS_CREDENTIALS)

    assert rows[TEST_PROJECT_ID][0]["namespace_id"] == f"{TEST_PROJECT_ID}/fr-par"


def _scaleway_exception(status_code: int, message: str) -> ScalewayException:
    response = Response()
    response.status_code = status_code
    response._content = message.encode("utf-8")
    return ScalewayException(response)


@patch.object(cartography.intel.scaleway.mnq.sqs, "DEFAULT_REGIONS", ("fr-par",))
@patch.object(cartography.intel.scaleway.mnq.sqs, "MnqV1Beta1SqsAPI")
def test_get_skips_unreadable_project_and_continues(mock_api_class):
    readable_project_id = "readable-project"
    api = Mock()
    api.get_sqs_info.side_effect = [
        _scaleway_exception(403, "permission denied"),
        SqsInfo(
            project_id=readable_project_id,
            region="fr-par",
            status=SqsInfoStatus.DISABLED,
            sqs_endpoint_url=None,
            created_at=None,
            updated_at=None,
        ),
    ]
    mock_api_class.return_value = api

    sqs_info, credentials, readable_projects_id = (
        cartography.intel.scaleway.mnq.sqs.get(
            Mock(),
            ["unreadable-project", readable_project_id],
        )
    )

    assert [info.project_id for info in sqs_info] == [readable_project_id]
    assert credentials == []
    assert readable_projects_id == [readable_project_id]


@patch.object(cartography.intel.scaleway.mnq.sqs, "cleanup")
@patch.object(cartography.intel.scaleway.mnq.sqs, "load_sqs")
@patch.object(
    cartography.intel.scaleway.mnq.sqs,
    "get",
    return_value=([], [], ["readable-project"]),
)
def test_sync_skips_cleanup_for_unreadable_projects(
    mock_get,
    mock_load_sqs,
    mock_cleanup,
):
    common_job_parameters = {"UPDATE_TAG": 123456789, "ORG_ID": "test-org"}

    cartography.intel.scaleway.mnq.sqs.sync(
        Mock(),
        Mock(),
        common_job_parameters,
        org_id="test-org",
        projects_id=["unreadable-project", "readable-project"],
        update_tag=123456789,
    )

    mock_get.assert_called_once_with(
        ANY,
        ["unreadable-project", "readable-project"],
    )
    mock_load_sqs.assert_called_once_with(ANY, {}, {}, 123456789)
    mock_cleanup.assert_called_once_with(
        ANY,
        ["readable-project"],
        common_job_parameters,
    )
