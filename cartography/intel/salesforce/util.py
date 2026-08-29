import logging
import time
from datetime import datetime
from typing import Any

import jwt
import requests

logger = logging.getLogger(__name__)

# Connect and read timeouts of 60 seconds each; see
# https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)
# Salesforce REST/Tooling API version used for all data queries.
# ponytail: pinned version; bump when a newer object/field is needed.
API_VERSION = "v60.0"
_JWT_LIFETIME_SECONDS = 300


class SalesforceClient:
    """Thin wrapper around a Salesforce org: an authenticated session plus the
    resolved instance URL. All SOQL queries go through `query_all`."""

    def __init__(self, session: requests.Session, instance_url: str) -> None:
        self.session = session
        self.instance_url = instance_url.rstrip("/")

    def query_all(self, soql: str) -> list[dict[str, Any]]:
        """Run a SOQL query and follow pagination until all records are fetched.

        The Salesforce-internal ``attributes`` key (record type + self URL) that the
        REST API attaches to every record is stripped so callers get plain dicts.
        """
        records: list[dict[str, Any]] = []
        url: str | None = f"{self.instance_url}/services/data/{API_VERSION}/query"
        params: dict[str, Any] | None = {"q": soql}
        while url:
            resp = self.session.get(url, params=params, timeout=_TIMEOUT)
            resp.raise_for_status()
            body = resp.json()
            records.extend(body.get("records", []))
            # nextRecordsUrl is an absolute path on the instance host
            next_path = body.get("nextRecordsUrl")
            # Fail fast rather than silently truncate: a well-formed response is
            # either done, or not-done with a next page. Anything else means we
            # would return a partial result set that looks complete.
            if not body.get("done", True) and not next_path:
                raise ValueError(
                    f"Salesforce SOQL response is not done but has no "
                    f"nextRecordsUrl; refusing to return a truncated result "
                    f"set for query: {soql}"
                )
            url = f"{self.instance_url}{next_path}" if next_path else None
            params = None
        return [
            {key: value for key, value in record.items() if key != "attributes"}
            for record in records
        ]


def _authenticate_jwt_bearer(
    login_url: str, client_id: str, username: str, private_key: str
) -> dict[str, Any]:
    now = int(time.time())
    assertion = jwt.encode(
        {
            "iss": client_id,
            "sub": username,
            "aud": login_url,
            "exp": now + _JWT_LIFETIME_SECONDS,
        },
        private_key,
        algorithm="RS256",
    )
    resp = requests.post(
        f"{login_url}/services/oauth2/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def _authenticate_client_credentials(
    login_url: str, client_id: str, client_secret: str
) -> dict[str, Any]:
    resp = requests.post(
        f"{login_url}/services/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_salesforce_client(
    login_url: str,
    client_id: str,
    client_secret: str | None = None,
    username: str | None = None,
    private_key: str | None = None,
) -> SalesforceClient:
    """Authenticate against Salesforce and return a ready-to-use client.

    Two OAuth2 flows are supported, selected by which credentials are provided:
    - JWT bearer (server-to-server): requires `username` + `private_key`.
    - Client credentials: requires `client_secret`.

    Both hit `{login_url}/services/oauth2/token` and return an access token plus
    the org's instance URL.
    """
    login_url = login_url.rstrip("/")
    if username and private_key:
        token = _authenticate_jwt_bearer(login_url, client_id, username, private_key)
    elif client_secret:
        token = _authenticate_client_credentials(login_url, client_id, client_secret)
    else:
        raise ValueError(
            "Salesforce auth requires either (username + private key) for the JWT "
            "bearer flow or a client secret for the client credentials flow."
        )

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token['access_token']}"})
    return SalesforceClient(session, token["instance_url"])


def parse_sf_datetime(value: str | None) -> datetime | None:
    """Parse a Salesforce ISO 8601 timestamp (e.g. '2023-01-01T00:00:00.000+0000')
    into a native datetime so Neo4j stores a temporal type, not a string."""
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
