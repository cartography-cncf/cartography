import json
from unittest.mock import MagicMock

from googleapiclient.errors import HttpError

from cartography.intel.gcp.util import get_error_reason
from cartography.intel.gcp.util import is_api_disabled_error
from cartography.intel.gcp.util import is_billing_disabled_error
from cartography.intel.gcp.util import is_permission_denied_error


class TestIsApiDisabledError:
    """Tests for is_api_disabled_error() function."""

    def test_api_not_used_with_reason_field(self):
        """Test detection via reason='accessNotConfigured'."""
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "code": 403,
                    "message": "Cloud Functions API has not been used in project 123",
                    "errors": [{"reason": "accessNotConfigured", "domain": "global"}],
                },
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_api_disabled_error(error) is True

    def test_service_disabled_reason(self):
        """Test detection via reason='SERVICE_DISABLED'."""
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "code": 403,
                    "message": "Bigtable Admin API is disabled",
                    "errors": [{"reason": "SERVICE_DISABLED", "domain": "global"}],
                },
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_api_disabled_error(error) is True

    def test_permission_denied_with_forbidden_reason(self):
        """Test that reason='forbidden' returns False (IAM issue, not API disabled)."""
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "code": 403,
                    "message": "Permission denied on resource",
                    "errors": [{"reason": "forbidden", "domain": "global"}],
                },
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_api_disabled_error(error) is False


class TestGetErrorReason:
    def test_extracts_reason_from_error_details_error_info(self):
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "code": 403,
                    "message": "Billing disabled",
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                            "reason": "BILLING_DISABLED",
                            "domain": "googleapis.com",
                        }
                    ],
                }
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert get_error_reason(error) == "BILLING_DISABLED"

    def test_extracts_reason_from_standard_errors_array(self):
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {"error": {"errors": [{"reason": "forbidden"}]}}
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert get_error_reason(error) == "forbidden"

    def test_returns_empty_string_when_no_reason_present(self):
        mock_resp = MagicMock()
        mock_resp.status = 500
        error = HttpError(mock_resp, b'{"error": {"message": "oops"}}')
        assert get_error_reason(error) == ""


class TestIsBillingDisabledError:
    def test_true_when_reason_is_billing_disabled(self):
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                            "reason": "BILLING_DISABLED",
                        }
                    ],
                }
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_billing_disabled_error(error) is True

    def test_true_when_message_contains_billing_disabled_text(self):
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {"error": {"message": "This API method requires billing to be enabled."}}
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_billing_disabled_error(error) is True

    def test_false_when_unrelated_403(self):
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "message": "Permission denied",
                    "errors": [{"reason": "forbidden"}],
                }
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_billing_disabled_error(error) is False

    def test_insufficient_permissions_reason(self):
        """Test that reason='insufficientPermissions' returns False."""
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "code": 403,
                    "message": "User lacks required permissions",
                    "errors": [
                        {
                            "reason": "insufficientPermissions",
                            "domain": "iam.googleapis.com",
                        }
                    ],
                },
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_api_disabled_error(error) is False

    def test_iam_permission_denied_reason(self):
        """Test that reason='IAM_PERMISSION_DENIED' returns False."""
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "code": 403,
                    "message": "IAM permission denied",
                    "errors": [
                        {
                            "reason": "IAM_PERMISSION_DENIED",
                            "domain": "iam.googleapis.com",
                        }
                    ],
                },
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_api_disabled_error(error) is False

    def test_fallback_to_message_pattern_api_not_used(self):
        """Test fallback to message pattern when no errors array."""
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "code": 403,
                    "message": "Cloud Run API has not been used in project 123 before or it is disabled",
                },
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_api_disabled_error(error) is True

    def test_fallback_to_message_pattern_is_not_enabled(self):
        """Test fallback for 'is not enabled' message pattern."""
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "message": "Bigtable Admin API is not enabled",
                },
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_api_disabled_error(error) is True

    def test_fallback_to_message_pattern_it_is_disabled(self):
        """Test fallback for 'it is disabled' message pattern."""
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "message": "Cloud SQL Admin API has not been used before or it is disabled",
                },
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_api_disabled_error(error) is True

    def test_generic_permission_denied_no_api_keywords(self):
        """Test that generic permission denied without API keywords returns False."""
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "message": "user@example.com does not have storage.buckets.list access",
                },
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_api_disabled_error(error) is False

    def test_malformed_json_response(self):
        """Test handling of non-JSON response content."""
        mock_resp = MagicMock()
        mock_resp.status = 403
        error = HttpError(mock_resp, b"Invalid JSON response")
        assert is_api_disabled_error(error) is False

    def test_empty_error_object(self):
        """Test handling of empty error object."""
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps({"error": {}}).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_api_disabled_error(error) is False

    def test_missing_error_key(self):
        """Test handling of response without 'error' key."""
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps({"status": "FAILED"}).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_api_disabled_error(error) is False

    def test_empty_errors_array_with_message(self):
        """Test fallback to message when errors array is empty."""
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "code": 403,
                    "message": "Cloud Run API is not enabled",
                    "errors": [],
                },
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_api_disabled_error(error) is True

    def test_unknown_reason_falls_back_to_message(self):
        """Test that unknown reason falls back to message pattern check."""
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "code": 403,
                    "message": "Some API is not enabled",
                    "errors": [{"reason": "unknownReason", "domain": "global"}],
                },
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_api_disabled_error(error) is True

    def test_unknown_reason_no_matching_message(self):
        """Test that unknown reason with non-matching message returns False."""
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "code": 403,
                    "message": "Some other error occurred",
                    "errors": [{"reason": "unknownReason", "domain": "global"}],
                },
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_api_disabled_error(error) is False


class TestIsPermissionDeniedError:
    @staticmethod
    def _make_error(reason: str) -> HttpError:
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "code": 403,
                    "message": "permission denied",
                    "errors": [{"reason": reason}],
                }
            }
        ).encode("utf-8")
        return HttpError(mock_resp, error_content)

    def test_forbidden(self):
        assert is_permission_denied_error(self._make_error("forbidden")) is True

    def test_insufficient_permissions(self):
        assert (
            is_permission_denied_error(self._make_error("insufficientPermissions"))
            is True
        )

    def test_iam_permission_denied(self):
        assert (
            is_permission_denied_error(self._make_error("IAM_PERMISSION_DENIED"))
            is True
        )

    def test_non_permission_reason(self):
        assert (
            is_permission_denied_error(self._make_error("accessNotConfigured")) is False
        )
