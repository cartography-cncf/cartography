import logging
import time
from typing import Any

import jwt
import requests

logger = logging.getLogger(__name__)

# Connect and read timeouts of 60 seconds each; see
# https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)

# Salesforce REST API version used for all data queries.
SALESFORCE_API_VERSION = "v60.0"

# Lifetime (seconds) of the signed JWT assertion used for the JWT Bearer flow.
_JWT_ASSERTION_LIFETIME = 180


def get_access_token_client_credentials(
    instance_url: str,
    client_id: str,
    client_secret: str,
) -> tuple[str, str]:
    """
    Authenticate with the Salesforce OAuth 2.0 Client Credentials flow.

    :param instance_url: The Salesforce My Domain login URL, e.g.
        "https://mydomain.my.salesforce.com".
    :param client_id: The connected app's consumer key.
    :param client_secret: The connected app's consumer secret.
    :return: A tuple of (access_token, instance_url) to use for subsequent API calls.
    """
    resp = requests.post(
        f"{instance_url}/services/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    body = resp.json()
    return body["access_token"], body["instance_url"]


def get_access_token_jwt_bearer(
    instance_url: str,
    client_id: str,
    username: str,
    private_key: str,
) -> tuple[str, str]:
    """
    Authenticate with the Salesforce OAuth 2.0 JWT Bearer flow.

    :param instance_url: The Salesforce My Domain login URL, e.g.
        "https://mydomain.my.salesforce.com".
    :param client_id: The connected app's consumer key (used as the JWT issuer).
    :param username: The Salesforce username to authenticate as (the JWT subject).
    :param private_key: The PEM-encoded private key whose certificate is registered
        on the connected app. Used to sign the JWT assertion (RS256).
    :return: A tuple of (access_token, instance_url) to use for subsequent API calls.
    """
    now = int(time.time())
    assertion = jwt.encode(
        {
            "iss": client_id,
            "sub": username,
            "aud": instance_url,
            "exp": now + _JWT_ASSERTION_LIFETIME,
        },
        private_key,
        algorithm="RS256",
    )
    resp = requests.post(
        f"{instance_url}/services/oauth2/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    body = resp.json()
    return body["access_token"], body["instance_url"]


def strip_attributes(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Drop the Salesforce-internal ``attributes`` key (record type + self URL) that the
    REST API attaches to every record, returning plain dicts ready for ingestion.
    """
    return [
        {key: value for key, value in record.items() if key != "attributes"}
        for record in records
    ]


def query_salesforce(
    api_session: requests.Session,
    instance_url: str,
    soql: str,
) -> list[dict[str, Any]]:
    """
    Run a SOQL query against the Salesforce REST API and return all records,
    transparently following pagination via ``nextRecordsUrl``.

    :param api_session: A requests session pre-authenticated with a Bearer token.
    :param instance_url: The Salesforce instance URL returned by authentication.
    :param soql: The SOQL query string to execute.
    :return: The list of record dicts across all result pages. Each record retains
        Salesforce's ``attributes`` key; callers transform out what they don't need.
    """
    records: list[dict[str, Any]] = []
    url: str | None = f"{instance_url}/services/data/{SALESFORCE_API_VERSION}/query"
    params: dict[str, str] | None = {"q": soql}
    while url:
        resp = api_session.get(url, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        body = resp.json()
        records.extend(body.get("records", []))
        next_records_url = body.get("nextRecordsUrl")
        if next_records_url:
            # nextRecordsUrl is a server-built path that already encodes the cursor.
            url = f"{instance_url}{next_records_url}"
            params = None
        else:
            url = None
    return records
