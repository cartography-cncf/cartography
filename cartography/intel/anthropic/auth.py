import time
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import requests

from cartography.intel.anthropic.util import TIMEOUT

TOKEN_URL = "https://api.anthropic.com/v1/oauth/token"
JWT_BEARER_GRANT = "urn:ietf:params:oauth:grant-type:jwt-bearer"

_EXCHANGE_ATTEMPTS = 4
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
_MAX_RETRY_DELAY_SECONDS = 60.0


@dataclass(frozen=True)
class WorkloadIdentityFederation:
    identity_token_file: str
    federation_rule_id: str
    organization_id: str
    service_account_id: str
    workspace_id: str | None = None


class WorkloadIdentityAuth(requests.auth.AuthBase):
    """Exchanges a workload's OIDC token for a short-lived Anthropic access token.

    Anthropic refuses an identity token it has already exchanged, so the auth
    only exchanges again once the token file holds a new one (projected
    Kubernetes tokens rotate in place). When Anthropic rejects the access token
    and the file has rotated, the request is resent once with a new access
    token, which also covers a retry that waited past the token's expiry.
    """

    def __init__(self, federation: WorkloadIdentityFederation) -> None:
        self._federation = federation
        self._access_token: str | None = None
        self._assertion: str | None = None
        self._refresh_at = 0.0

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        if self._access_token is None or (
            time.monotonic() >= self._refresh_at
            and self._read_assertion() != self._assertion
        ):
            self._exchange()
        request.headers["Authorization"] = f"Bearer {self._access_token}"
        request.hooks["response"].append(self._resend_once_on_unauthorized)
        return request

    def _resend_once_on_unauthorized(
        self,
        response: requests.Response,
        **kwargs: Any,
    ) -> requests.Response:
        if response.status_code != 401 or self._read_assertion() == self._assertion:
            return response
        self._exchange()
        # Drain the rejected response so its connection can carry the resend.
        response.content
        response.close()
        resend = response.request.copy()
        resend.hooks["response"] = []
        resend.headers["Authorization"] = f"Bearer {self._access_token}"
        retried = response.connection.send(resend, **kwargs)
        retried.history.append(response)
        retried.request = resend
        return retried

    def _read_assertion(self) -> str:
        return Path(self._federation.identity_token_file).read_text().strip()

    def _exchange(self) -> None:
        server_errors: dict[str, requests.Response] = {}
        for attempt in range(_EXCHANGE_ATTEMPTS):
            assertion = self._read_assertion()
            body = {
                "grant_type": JWT_BEARER_GRANT,
                "assertion": assertion,
                "federation_rule_id": self._federation.federation_rule_id,
                "organization_id": self._federation.organization_id,
                "service_account_id": self._federation.service_account_id,
            }
            if self._federation.workspace_id:
                body["workspace_id"] = self._federation.workspace_id
            response = requests.post(TOKEN_URL, json=body, timeout=TIMEOUT)
            if response.status_code >= 500:
                server_errors[assertion] = response
            if (
                response.status_code not in _RETRYABLE_STATUS
                or attempt == _EXCHANGE_ATTEMPTS - 1
            ):
                break
            time.sleep(_retry_delay(response, attempt))
        if (
            400 <= response.status_code < 500
            and response.status_code not in _RETRYABLE_STATUS
            and assertion in server_errors
        ):
            # A server error can land after Anthropic consumed the identity
            # token, so refusing its replay says nothing about the federation
            # rule. Report the server error instead.
            server_errors[assertion].raise_for_status()
        response.raise_for_status()
        token = response.json()
        self._access_token = token["access_token"]
        self._assertion = assertion
        # Refresh at half the lifetime so a rotated identity token is picked up
        # well before the access token lapses.
        self._refresh_at = time.monotonic() + token["expires_in"] / 2


def _retry_delay(response: requests.Response, attempt: int) -> float:
    retry_after = response.headers.get("retry-after", "")
    try:
        delay = float(retry_after)
    except ValueError:
        try:
            delay = (
                parsedate_to_datetime(retry_after) - datetime.now(timezone.utc)
            ).total_seconds()
        except (TypeError, ValueError):
            delay = 2.0**attempt
    return min(max(delay, 0.0), _MAX_RETRY_DELAY_SECONDS)
