import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from googleapiclient.errors import HttpError

import cartography.intel.gcp


def _make_http_error(status: int) -> HttpError:
    mock_resp = MagicMock()
    mock_resp.status = status
    return HttpError(mock_resp, json.dumps({"error": {"code": status}}).encode())


class TestServicesEnabledOnProjectHttpErrors:
    def test_returns_empty_set_for_http_error(self):
        serviceusage = MagicMock()
        serviceusage.services().list.return_value.execute.side_effect = (
            _make_http_error(403)
        )

        with (
            patch(
                "cartography.intel.gcp.classify_gcp_http_error",
                return_value="transient",
            ) as mock_classify,
            patch(
                "cartography.intel.gcp.summarize_gcp_http_error",
                return_value="HTTP 403 forbidden: denied",
            ),
        ):
            assert (
                cartography.intel.gcp._services_enabled_on_project(
                    serviceusage,
                    "test-project",
                )
                == set()
            )
            mock_classify.assert_called_once()


class TestSyncProjectResourcesCaiFallbackHttpErrors:
    @pytest.mark.parametrize("category", ["forbidden", "api_disabled"])
    def test_skips_cai_fallback_without_cleanup(self, category):
        common_job_parameters = {"UPDATE_TAG": 123}
        credentials = MagicMock()

        with (
            patch(
                "cartography.intel.gcp._services_enabled_on_project",
                return_value=set(),
            ),
            patch("cartography.intel.gcp.build_client", return_value=MagicMock()),
            patch(
                "cartography.intel.gcp.cai.sync",
                side_effect=_make_http_error(403),
            ),
            patch(
                "cartography.intel.gcp.classify_gcp_http_error",
                return_value=category,
            ),
            patch(
                "cartography.intel.gcp.iam.cleanup_service_accounts"
            ) as mock_cleanup_sas,
            patch(
                "cartography.intel.gcp.iam.cleanup_project_roles"
            ) as mock_cleanup_roles,
        ):
            cartography.intel.gcp._sync_project_resources(
                MagicMock(),
                [{"projectId": "test-project"}],
                123,
                common_job_parameters,
                credentials,
                requested_syncs={"iam"},
            )

        mock_cleanup_sas.assert_not_called()
        mock_cleanup_roles.assert_not_called()
        assert "PROJECT_ID" not in common_job_parameters

    @pytest.mark.parametrize("category,status", [("unknown", 500), ("transient", 503)])
    def test_reraises_unexpected_cai_fallback_errors(self, category, status):
        common_job_parameters = {"UPDATE_TAG": 123}
        credentials = MagicMock()

        with (
            patch(
                "cartography.intel.gcp._services_enabled_on_project",
                return_value=set(),
            ),
            patch("cartography.intel.gcp.build_client", return_value=MagicMock()),
            patch(
                "cartography.intel.gcp.cai.sync",
                side_effect=_make_http_error(status),
            ),
            patch(
                "cartography.intel.gcp.classify_gcp_http_error",
                return_value=category,
            ),
        ):
            with pytest.raises(HttpError):
                cartography.intel.gcp._sync_project_resources(
                    MagicMock(),
                    [{"projectId": "test-project"}],
                    123,
                    common_job_parameters,
                    credentials,
                    requested_syncs={"iam"},
                )
