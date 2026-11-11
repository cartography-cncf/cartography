import time
from dataclasses import dataclass
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

TOKEN_URL = "https://api.anthropic.com/v1/oauth/token"
JWT_BEARER_GRANT = "urn:ietf:params:oauth:grant-type:jwt-bearer"

_TIMEOUT = (60, 60)
# Exchange once this share of the access token's lifetime has passed, so a
# request in flight never carries a token that expires on the way. A fixed margin
# would refresh a 60-second token at once and replay the identity token, which
# Anthropic refuses when the token is single-use.
_REFRESH_AT_LIFETIME_FRACTION = 0.8


@dataclass(frozen=True)
class WorkloadIdentityFederation:
    identity_token_file: str
    federation_rule_id: str
    organization_id: str
    service_account_id: str
    workspace_id: str | None = None


class WorkloadIdentityAuth(requests.auth.AuthBase):
    """Exchanges a workload's OIDC token for a short-lived Anthropic access token.

    The token file is read on every exchange because projected Kubernetes tokens
    and similar sources rotate the file in place.
    """

    def __init__(self, federation: WorkloadIdentityFederation) -> None:
        self._federation = federation
        self._session = requests.Session()
        self._session.mount(
            "https://",
            HTTPAdapter(
                max_retries=Retry(
                    total=5,
                    backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["POST"],
                ),
            ),
        )
        self._access_token: str | None = None
        self._refresh_at = 0.0

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        if time.monotonic() >= self._refresh_at:
            self._exchange()
        request.headers["Authorization"] = f"Bearer {self._access_token}"
        return request

    def _exchange(self) -> None:
        body = {
            "grant_type": JWT_BEARER_GRANT,
            "assertion": Path(self._federation.identity_token_file).read_text().strip(),
            "federation_rule_id": self._federation.federation_rule_id,
            "organization_id": self._federation.organization_id,
            "service_account_id": self._federation.service_account_id,
        }
        if self._federation.workspace_id:
            body["workspace_id"] = self._federation.workspace_id
        response = self._session.post(TOKEN_URL, json=body, timeout=_TIMEOUT)
        response.raise_for_status()
        token = response.json()
        self._access_token = token["access_token"]
        self._refresh_at = (
            time.monotonic() + token["expires_in"] * _REFRESH_AT_LIFETIME_FRACTION
        )
