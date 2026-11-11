import time
from dataclasses import dataclass
from pathlib import Path

import requests

TOKEN_URL = "https://api.anthropic.com/v1/oauth/token"
JWT_BEARER_GRANT = "urn:ietf:params:oauth:grant-type:jwt-bearer"

_TIMEOUT = (60, 60)
# Exchange before the access token lapses so a request in flight never carries
# a token that expires on the way.
_REFRESH_MARGIN_SECONDS = 60


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
        self._access_token: str | None = None
        self._expires_at = 0.0

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        if time.monotonic() >= self._expires_at - _REFRESH_MARGIN_SECONDS:
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
        response = requests.post(TOKEN_URL, json=body, timeout=_TIMEOUT)
        response.raise_for_status()
        token = response.json()
        self._access_token = token["access_token"]
        self._expires_at = time.monotonic() + token["expires_in"]
