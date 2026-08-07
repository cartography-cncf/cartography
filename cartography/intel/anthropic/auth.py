"""
Anthropic authentication support for Admin API keys and Workload Identity Federation.

Workload Identity Federation flow:
1. The platform running cartography (Kubernetes, EKS, GKE, GitHub Actions) issues an
   OIDC JWT that proves the workload's identity, as a file on disk or an environment
   variable.
2. That JWT is POSTed to /v1/oauth/token using the RFC 7523 jwt-bearer grant, along
   with the federation rule, organization and service account it should act as.
3. Anthropic returns a short-lived bearer token, used for API calls and transparently
   refreshed when it nears expiry.

The two credential types use different headers: an Admin API key goes in `X-Api-Key`,
a federated token in `Authorization: Bearer`.
"""

import logging
import os
import random
import time
from typing import Any

import requests
from requests.auth import AuthBase

logger = logging.getLogger(__name__)

# Federated tokens live for the federation rule's token_lifetime_seconds (3600 by
# default). Refresh well before expiry so a long sync never presents a stale token.
_TOKEN_REFRESH_BUFFER_SECONDS = 300
_TIMEOUT = (60, 60)
_JWT_BEARER_GRANT = "urn:ietf:params:oauth:grant-type:jwt-bearer"

# The token endpoint publishes no rate limit, and enumerating a large organization
# means one exchange per workspace. Back off with jitter rather than assume a budget.
_EXCHANGE_MAX_ATTEMPTS = 4
_EXCHANGE_BACKOFF_SECONDS = 2

# Retried because a later attempt can plausibly succeed: throttling and the gateway
# family. A 4xx other than 429 means the federation configuration itself is wrong, so
# retrying only delays the error.
_RETRYABLE_EXCHANGE_STATUSES = frozenset({429, 500, 502, 503, 504})


class AssertionSource:
    """Base class for reading the OIDC JWT that proves the workload's identity."""

    def read(self) -> str:
        """Return the current OIDC JWT."""
        raise NotImplementedError


class FileAssertionSource(AssertionSource):
    """
    Reads the OIDC JWT from a file, e.g. a Kubernetes projected service account token.

    The file is re-read on every call: Kubernetes rotates projected tokens on disk
    before they expire, so a value cached at startup goes stale mid-sync.
    """

    def __init__(self, path: str) -> None:
        self._path = path

    def read(self) -> str:
        with open(self._path) as f:
            return f.read().strip()


class EnvVarAssertionSource(AssertionSource):
    """Reads the OIDC JWT from an environment variable."""

    def __init__(self, env_var: str) -> None:
        self._env_var = env_var

    def read(self) -> str:
        token = os.environ.get(self._env_var)
        if not token:
            raise ValueError(
                f"Environment variable {self._env_var} does not contain an identity token.",
            )
        return token.strip()


class AnthropicCredential:
    """Base class for Anthropic authentication credentials."""

    def get_headers(self) -> dict[str, str]:
        """Return the authentication headers to attach to a request."""
        raise NotImplementedError


class ApiKeyCredential(AnthropicCredential):
    """Admin API key credential - a static key sent in the X-Api-Key header."""

    def __init__(self, apikey: str) -> None:
        self._apikey = apikey

    def get_headers(self) -> dict[str, str]:
        return {"X-Api-Key": self._apikey}


class WorkloadIdentityCredential(AnthropicCredential):
    """
    Workload Identity Federation credential with automatic token refresh.

    Exchanges the workload's OIDC JWT for a short-lived Anthropic bearer token and
    transparently re-exchanges when the token nears expiry.

    The scope of the minted token is fixed by the federation rule, not chosen here:
    a rule carrying `org:admin` yields an Admin API token, a rule carrying
    `workspace:developer` yields a token for a single workspace. Anthropic exposes no
    way to downscope one token into another, so reaching a different scope or a
    different workspace means constructing another credential against another rule.
    """

    def __init__(
        self,
        assertion_source: AssertionSource,
        federation_rule_id: str,
        organization_id: str,
        service_account_id: str,
        workspace_id: str | None = None,
        base_url: str = "https://api.anthropic.com/v1",
    ) -> None:
        self._assertion_source = assertion_source
        self._federation_rule_id = federation_rule_id
        self._organization_id = organization_id
        self._service_account_id = service_account_id
        self._workspace_id = workspace_id
        self._base_url = base_url
        self._token: str | None = None
        self._token_expires_at: float = 0

    def get_headers(self) -> dict[str, str]:
        if self._token is None or self._is_near_expiry():
            self._refresh_token()
        assert self._token is not None
        return {"Authorization": f"Bearer {self._token}"}

    def _is_near_expiry(self) -> bool:
        return time.time() >= (self._token_expires_at - _TOKEN_REFRESH_BUFFER_SECONDS)

    def _refresh_token(self) -> None:
        logger.debug(
            "Exchanging identity token for an Anthropic access token (rule %s, workspace %s)",
            self._federation_rule_id,
            self._workspace_id or "default",
        )
        body: dict[str, Any] = {
            "grant_type": _JWT_BEARER_GRANT,
            "assertion": self._assertion_source.read(),
            "federation_rule_id": self._federation_rule_id,
            "organization_id": self._organization_id,
            "service_account_id": self._service_account_id,
        }
        # Required when the federation rule is enabled for more than one workspace;
        # rejected as unnecessary otherwise, so only send it when we have one.
        if self._workspace_id:
            body["workspace_id"] = self._workspace_id

        data = self._exchange(body)
        self._token = data["access_token"]
        self._token_expires_at = time.time() + data["expires_in"]
        logger.debug("Anthropic access token minted with scope %s", data.get("scope"))

    def _exchange(self, body: dict[str, Any]) -> dict[str, Any]:
        """POST the assertion to the token endpoint, retrying only what can succeed later.

        Throttling, gateway errors and connection failures are retried: they say
        nothing about whether the federation setup is valid. Every other 4xx is
        raised on the first attempt, so a wrong rule id, an expired assertion or a
        service account that is not a member of the workspace fails fast instead of
        being buried under a minute of backoff.
        """
        for attempt in range(_EXCHANGE_MAX_ATTEMPTS):
            last_attempt = attempt == _EXCHANGE_MAX_ATTEMPTS - 1
            try:
                response = requests.post(
                    f"{self._base_url}/oauth/token",
                    json=body,
                    timeout=_TIMEOUT,
                )
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ) as exc:
                if last_attempt:
                    raise
                reason: str = f"failed to reach the token endpoint ({exc})"
            else:
                if response.status_code not in _RETRYABLE_EXCHANGE_STATUSES:
                    response.raise_for_status()
                    result: dict[str, Any] = response.json()
                    return result
                if last_attempt:
                    response.raise_for_status()
                reason = f"returned HTTP {response.status_code}"
            delay = (_EXCHANGE_BACKOFF_SECONDS**attempt) + random.uniform(0, 1)
            logger.warning(
                "Anthropic token exchange %s, retrying in %.1fs", reason, delay
            )
            time.sleep(delay)
        raise AssertionError("unreachable: the loop returns or raises on every path")


class AnthropicAuth(AuthBase):
    """
    Applies an AnthropicCredential to every request on a session.

    Attached as `session.auth` rather than baked into `session.headers` so that a
    federated token refreshes itself mid-sync without the callers knowing.
    """

    def __init__(self, credential: AnthropicCredential) -> None:
        self.credential = credential

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        request.headers.update(self.credential.get_headers())
        return request


def make_credential(
    apikey: str | None = None,
    identity_token_file: str | None = None,
    identity_token_env_var: str | None = None,
    federation_rule_id: str | None = None,
    organization_id: str | None = None,
    service_account_id: str | None = None,
    workspace_id: str | None = None,
) -> AnthropicCredential:
    """
    Build the credential implied by the supplied configuration.

    Workload Identity Federation wins when both it and an Admin API key are
    configured: it reaches strictly more endpoints (service accounts and federation
    resources reject Admin API keys) and involves no long-lived secret.
    """
    assertion_source = make_assertion_source(
        identity_token_file,
        identity_token_env_var,
    )
    if assertion_source is not None:
        missing = [
            name
            for name, value in (
                ("--anthropic-federation-rule-id", federation_rule_id),
                ("--anthropic-organization-id", organization_id),
                ("--anthropic-service-account-id", service_account_id),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                "Anthropic Workload Identity Federation is partially configured: "
                f"missing {', '.join(missing)}.",
            )
        # The guard above proves these are set; mypy cannot see through the list.
        assert federation_rule_id and organization_id and service_account_id
        if apikey:
            logger.warning(
                "Both an Anthropic API key and Workload Identity Federation are "
                "configured; using Workload Identity Federation.",
            )
        return WorkloadIdentityCredential(
            assertion_source=assertion_source,
            federation_rule_id=federation_rule_id,
            organization_id=organization_id,
            service_account_id=service_account_id,
            workspace_id=workspace_id,
        )

    # The inverse of the check above: the federation ids are set but the identity token
    # source is not. Silently falling back to the API key (or skipping the module) would
    # hide the very operator mistake this is most likely to be, an unset token variable.
    configured_federation_ids = [
        name
        for name, value in (
            ("--anthropic-federation-rule-id", federation_rule_id),
            ("--anthropic-organization-id", organization_id),
            ("--anthropic-service-account-id", service_account_id),
        )
        if value
    ]
    if configured_federation_ids:
        raise ValueError(
            "Anthropic Workload Identity Federation is partially configured: "
            f"{', '.join(configured_federation_ids)} set without an identity token "
            "source. Set --anthropic-identity-token-file or "
            "--anthropic-identity-token-env-var, and check that the token file exists "
            "and the environment variable is populated.",
        )

    if apikey:
        return ApiKeyCredential(apikey)

    raise ValueError(
        "Anthropic authentication is not configured. Set either "
        "--anthropic-apikey-env-var or --anthropic-identity-token-file / "
        "--anthropic-identity-token-env-var plus --anthropic-federation-rule-id, "
        "--anthropic-organization-id and --anthropic-service-account-id.",
    )


def make_assertion_source(
    identity_token_file: str | None,
    identity_token_env_var: str | None,
) -> AssertionSource | None:
    """Return the configured identity token source, or None if there is none."""
    if identity_token_file and identity_token_env_var:
        raise ValueError(
            "--anthropic-identity-token-file and --anthropic-identity-token-env-var "
            "are mutually exclusive; set only one.",
        )
    if identity_token_file:
        return FileAssertionSource(identity_token_file)
    if identity_token_env_var:
        return EnvVarAssertionSource(identity_token_env_var)
    return None


def is_federated(credential: AnthropicCredential) -> bool:
    """
    Whether this credential can reach the endpoints that reject Admin API keys.

    Service accounts, federation issuers and federation rules are only readable with
    an org:admin OAuth token.
    """
    return isinstance(credential, WorkloadIdentityCredential)
