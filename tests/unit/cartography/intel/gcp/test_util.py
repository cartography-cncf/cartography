import json
import logging
from unittest.mock import MagicMock

import pytest
from google.api_core.exceptions import InternalServerError
from google.api_core.exceptions import ServiceUnavailable
from google.api_core.exceptions import TooManyRequests
from googleapiclient.errors import HttpError

from cartography.intel.gcp.util import classify_gcp_http_error
from cartography.intel.gcp.util import gcp_api_giveup_handler
from cartography.intel.gcp.util import get_error_reason
from cartography.intel.gcp.util import is_api_disabled_error
from cartography.intel.gcp.util import is_billing_disabled_error
from cartography.intel.gcp.util import is_permission_denied_error
from cartography.intel.gcp.util import is_retryable_gcp_http_error
from cartography.intel.gcp.util import summarize_gcp_http_error


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

    def test_extracts_reason_from_precondition_failure_violation_type(self):
        mock_resp = MagicMock()
        mock_resp.status = 400
        error_content = json.dumps(
            {
                "error": {
                    "code": 400,
                    "message": "Billing is disabled for project 123456789",
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.PreconditionFailure",
                            "violations": [
                                {
                                    "type": "BILLING_DISABLED",
                                    "subject": "123456789",
                                }
                            ],
                        }
                    ],
                }
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert get_error_reason(error) == "BILLING_DISABLED"

    def test_prefers_detail_reason_over_violation_type(self):
        mock_resp = MagicMock()
        mock_resp.status = 400
        error_content = json.dumps(
            {
                "error": {
                    "code": 400,
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.PreconditionFailure",
                            "violations": [
                                {
                                    "type": "BILLING_DISABLED",
                                    "subject": "123456789",
                                }
                            ],
                        },
                        {
                            "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                            "reason": "RATE_LIMIT_EXCEEDED",
                            "domain": "googleapis.com",
                        },
                    ],
                }
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert get_error_reason(error) == "RATE_LIMIT_EXCEEDED"

    def test_extracts_reason_from_standard_errors_array(self):
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {"error": {"errors": [{"reason": "forbidden"}]}}
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert get_error_reason(error) == "forbidden"


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

    def test_true_for_precondition_failure_billing_disabled_payload(self):
        mock_resp = MagicMock()
        mock_resp.status = 400
        error_content = json.dumps(
            {
                "error": {
                    "code": 400,
                    "message": (
                        "Billing is disabled for project 123456789. Enable it by "
                        "visiting https://console.cloud.google.com/billing/projects "
                        "and associating your project with a billing account."
                    ),
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.PreconditionFailure",
                            "violations": [
                                {
                                    "type": "BILLING_DISABLED",
                                    "subject": "123456789",
                                }
                            ],
                        }
                    ],
                }
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_billing_disabled_error(error) is True

    def test_false_when_structured_non_billing_reason_has_billing_like_message(self):
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "code": 403,
                    "message": "Billing is disabled for project 123456789",
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                            "reason": "PERMISSION_DENIED",
                            "domain": "googleapis.com",
                        }
                    ],
                }
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)
        assert is_billing_disabled_error(error) is False

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

    @pytest.mark.parametrize(
        "reason",
        ["forbidden", "insufficientPermissions", "IAM_PERMISSION_DENIED"],
    )
    def test_true_for_supported_permission_denied_reasons(self, reason):
        assert is_permission_denied_error(self._make_error(reason)) is True

    def test_false_for_non_permission_reason(self):
        assert (
            is_permission_denied_error(self._make_error("accessNotConfigured")) is False
        )


class TestIsRetryableGcpHttpError:
    @pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
    def test_true_for_standard_retryable_status_codes(self, status):
        mock_resp = MagicMock()
        mock_resp.status = status
        error = HttpError(mock_resp, b"")
        assert is_retryable_gcp_http_error(error) is True

    @pytest.mark.parametrize(
        "reason",
        [
            "rateLimitExceeded",  # legacy REST API style
            "userRateLimitExceeded",  # legacy REST API style
            "RATE_LIMIT_EXCEEDED",  # gRPC-transcoded / ErrorInfo style
            "USER_RATE_LIMIT_EXCEEDED",  # gRPC-transcoded / ErrorInfo style
        ],
    )
    def test_true_for_quota_exceeded_403(self, reason):
        # Older GCP APIs signal quota exhaustion as 403, not 429.
        # is_retryable_gcp_http_error must agree with classify_gcp_http_error
        # (which returns "transient" for these) so the backoff decorator retries them.
        mock_resp = MagicMock()
        mock_resp.status = 403
        content = json.dumps(
            {"error": {"code": 403, "errors": [{"reason": reason}]}}
        ).encode("utf-8")
        error = HttpError(mock_resp, content)
        assert is_retryable_gcp_http_error(error) is True

    def test_true_for_quota_exceeded_403_grpc_error_info_shape(self):
        # gRPC-transcoded APIs embed the reason inside error.details[] ErrorInfo.
        mock_resp = MagicMock()
        mock_resp.status = 403
        content = json.dumps(
            {
                "error": {
                    "code": 403,
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                            "reason": "RATE_LIMIT_EXCEEDED",
                            "domain": "googleapis.com",
                        }
                    ],
                }
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, content)
        assert is_retryable_gcp_http_error(error) is True

    def test_false_for_permission_denied_403(self):
        mock_resp = MagicMock()
        mock_resp.status = 403
        content = json.dumps(
            {"error": {"code": 403, "errors": [{"reason": "forbidden"}]}}
        ).encode("utf-8")
        error = HttpError(mock_resp, content)
        assert is_retryable_gcp_http_error(error) is False

    def test_false_for_404(self):
        mock_resp = MagicMock()
        mock_resp.status = 404
        error = HttpError(mock_resp, b"")
        assert is_retryable_gcp_http_error(error) is False

    def test_false_for_non_http_error(self):
        assert is_retryable_gcp_http_error(ValueError("not an HttpError")) is False

    @pytest.mark.parametrize(
        "error_cls", [InternalServerError, ServiceUnavailable, TooManyRequests]
    )
    def test_true_for_retryable_google_api_core_errors(self, error_cls):
        assert is_retryable_gcp_http_error(error_cls("transient server error")) is True


class TestSummarizeGcpHttpError:
    def test_uses_structured_error_message(self):
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "code": 403,
                    "message": (
                        "Required 'compute.instanceGroups.get' permission for "
                        "'projects/example/zones/us-central1-a/instanceGroups/test'"
                    ),
                    "errors": [{"reason": "forbidden"}],
                }
            }
        ).encode("utf-8")

        error = HttpError(mock_resp, error_content)

        assert summarize_gcp_http_error(error) == (
            "HTTP 403 forbidden: Required 'compute.instanceGroups.get' permission for "
            "'projects/example/zones/us-central1-a/instanceGroups/test'"
        )


class TestGcpApiGiveupHandler:
    def test_suppresses_non_retryable_http_errors(self, caplog):
        mock_resp = MagicMock()
        mock_resp.status = 403
        error_content = json.dumps(
            {
                "error": {
                    "code": 403,
                    "message": "Permission denied on resource",
                    "errors": [{"reason": "forbidden"}],
                }
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)

        with caplog.at_level(logging.WARNING):
            gcp_api_giveup_handler(
                {
                    "tries": 1,
                    "target": "_gcp_execute",
                    "exception": error,
                }
            )

        assert not caplog.records

    def test_logs_retryable_http_errors_concisely(self, caplog):
        mock_resp = MagicMock()
        mock_resp.status = 503
        error_content = json.dumps(
            {
                "error": {
                    "code": 503,
                    "message": "The service is currently unavailable.",
                    "errors": [{"reason": "backendError"}],
                }
            }
        ).encode("utf-8")
        error = HttpError(mock_resp, error_content)

        with caplog.at_level(logging.WARNING):
            gcp_api_giveup_handler(
                {
                    "tries": 3,
                    "target": "_gcp_execute",
                    "exception": error,
                }
            )

        assert len(caplog.records) == 1
        assert (
            "HTTP 503 backendError: The service is currently unavailable."
            in caplog.text
        )
        assert "googleapiclient.errors.HttpError" not in caplog.text


def _make_http_error(
    status: int, body: dict | None = None, raw: bytes | None = None
) -> HttpError:
    """Helper: build an HttpError with the given HTTP status and optional JSON body."""
    mock_resp = MagicMock()
    mock_resp.status = status
    if raw is not None:
        content = raw
    elif body is not None:
        content = json.dumps(body).encode("utf-8")
    else:
        content = b""
    return HttpError(mock_resp, content)


class TestClassifyGcpHttpError:
    """Table-driven tests for classify_gcp_http_error()."""

    # ------------------------------------------------------------------
    # api_disabled
    # ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "reason",
        ["accessNotConfigured", "SERVICE_DISABLED"],
    )
    def test_api_disabled_from_reason(self, reason):
        e = _make_http_error(
            403,
            {
                "error": {
                    "code": 403,
                    "message": "API not enabled",
                    "errors": [{"reason": reason}],
                }
            },
        )
        assert classify_gcp_http_error(e) == "api_disabled"

    def test_api_disabled_from_message_pattern(self):
        e = _make_http_error(
            403,
            {
                "error": {
                    "code": 403,
                    "message": "Cloud Run API has not been used in project 123 before or it is disabled",
                }
            },
        )
        assert classify_gcp_http_error(e) == "api_disabled"

    # ------------------------------------------------------------------
    # forbidden
    # ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "reason",
        ["forbidden", "insufficientPermissions", "IAM_PERMISSION_DENIED"],
    )
    def test_forbidden_iam_reasons(self, reason):
        e = _make_http_error(
            403,
            {
                "error": {
                    "code": 403,
                    "message": "permission denied",
                    "errors": [{"reason": reason}],
                }
            },
        )
        assert classify_gcp_http_error(e) == "forbidden"

    def test_forbidden_billing_disabled(self):
        # BILLING_DISABLED is a 403 but NOT api_disabled → classifies as forbidden
        e = _make_http_error(
            403,
            {
                "error": {
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                            "reason": "BILLING_DISABLED",
                        }
                    ]
                }
            },
        )
        assert classify_gcp_http_error(e) == "forbidden"

    def test_forbidden_plain_403_no_reason(self):
        e = _make_http_error(403, {"error": {"code": 403, "message": "Forbidden"}})
        assert classify_gcp_http_error(e) == "forbidden"

    # ------------------------------------------------------------------
    # not_found
    # ------------------------------------------------------------------
    def test_not_found_404(self):
        e = _make_http_error(404, {"error": {"code": 404, "message": "Not found"}})
        assert classify_gcp_http_error(e) == "not_found"

    def test_not_found_404_no_body(self):
        e = _make_http_error(404)
        assert classify_gcp_http_error(e) == "not_found"

    # ------------------------------------------------------------------
    # invalid
    # ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "reason",
        ["invalid", "badRequest"],
    )
    def test_invalid_400_matching_reasons(self, reason):
        e = _make_http_error(
            400,
            {"error": {"code": 400, "errors": [{"reason": reason}]}},
        )
        assert classify_gcp_http_error(e) == "invalid"

    def test_invalid_400_grpc_shape(self):
        # gRPC-transcoded shape with reason in details[]
        e = _make_http_error(
            400,
            {
                "error": {
                    "code": 400,
                    "details": [{"reason": "invalid"}],
                }
            },
        )
        assert classify_gcp_http_error(e) == "invalid"

    def test_400_unrecognised_reason_is_unknown(self):
        e = _make_http_error(
            400,
            {"error": {"code": 400, "errors": [{"reason": "someOtherReason"}]}},
        )
        assert classify_gcp_http_error(e) == "unknown"

    # ------------------------------------------------------------------
    # transient
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
    def test_transient_status_codes(self, status):
        e = _make_http_error(
            status, {"error": {"code": status, "message": "transient"}}
        )
        assert classify_gcp_http_error(e) == "transient"

    @pytest.mark.parametrize(
        "reason",
        [
            "rateLimitExceeded",  # legacy REST API style
            "userRateLimitExceeded",  # legacy REST API style
            "RATE_LIMIT_EXCEEDED",  # gRPC-transcoded / ErrorInfo style
            "USER_RATE_LIMIT_EXCEEDED",  # gRPC-transcoded / ErrorInfo style
        ],
    )
    def test_transient_quota_403(self, reason):
        # Some GCP APIs return 403 (not 429) for quota/rate-limit errors.
        # These must classify as "transient", not "forbidden", so callers
        # do not silently swallow them as permission skips.
        e = _make_http_error(
            403,
            {"error": {"code": 403, "errors": [{"reason": reason}]}},
        )
        assert classify_gcp_http_error(e) == "transient"

    def test_transient_quota_403_grpc_error_info_shape(self):
        # gRPC-transcoded APIs embed the reason inside error.details[] ErrorInfo.
        e = _make_http_error(
            403,
            {
                "error": {
                    "code": 403,
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                            "reason": "RATE_LIMIT_EXCEEDED",
                            "domain": "googleapis.com",
                        }
                    ],
                }
            },
        )
        assert classify_gcp_http_error(e) == "transient"

    # ------------------------------------------------------------------
    # unknown
    # ------------------------------------------------------------------
    def test_unknown_401(self):
        e = _make_http_error(401, {"error": {"code": 401, "message": "Unauthorized"}})
        assert classify_gcp_http_error(e) == "unknown"

    def test_unknown_301(self):
        e = _make_http_error(301, {"error": {}})
        assert classify_gcp_http_error(e) == "unknown"

    # ------------------------------------------------------------------
    # Malformed / non-JSON payloads — must never raise, classify as expected
    # ------------------------------------------------------------------
    def test_non_json_body_403_classifies_as_forbidden(self):
        # Non-JSON 403: is_api_disabled_error returns False → forbidden
        e = _make_http_error(403, raw=b"not json at all")
        assert classify_gcp_http_error(e) == "forbidden"

    def test_non_json_body_404_classifies_as_not_found(self):
        e = _make_http_error(404, raw=b"not json at all")
        assert classify_gcp_http_error(e) == "not_found"

    def test_partial_json_missing_error_key(self):
        e = _make_http_error(403, {"status": "FAILED"})
        # No matching api_disabled pattern → forbidden
        assert classify_gcp_http_error(e) == "forbidden"

    def test_empty_body_403(self):
        e = _make_http_error(403)
        assert classify_gcp_http_error(e) == "forbidden"
