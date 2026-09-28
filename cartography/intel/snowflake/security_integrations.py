"""Snowflake security integrations.

There is no object endpoint for security integrations, so they come from
``SHOW SECURITY INTEGRATIONS`` plus one ``DESC INTEGRATION`` per integration through
the SQL API. This is the account's federated sign-in surface: which identity provider
may assert who a user is, whether an OAuth token may request any role, and which
Snowflake role a SCIM provisioner acts as.

Two values that ``DESC`` returns are deliberately not stored: the SAML signing
certificate body (only its SHA-256 fingerprint is kept, which is enough to detect a
rotation or a mismatch) and ``OAUTH_CLIENT_SECRET``.
"""

import base64
import binascii
import hashlib
import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.names import name_list
from cartography.intel.snowflake.sql_values import to_bool
from cartography.intel.snowflake.sql_values import to_int
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.security_integration import (
    SnowflakeSecurityIntegrationSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Snowflake's integration `type` is the protocol optionally suffixed with the
# provider, for example SAML2, EXTERNAL_OAUTH - OKTA or SCIM - AZURE. Matching on the
# leading token is what lets one `protocol` property answer "how does this account
# federate" across every provider suffix Snowflake has ever emitted.
_PROTOCOL_BY_TYPE_PREFIX = {
    "SAML2": "SAML",
    "EXTERNAL_OAUTH": "OIDC",
    "OAUTH": "OIDC",
    "SCIM": "SCIM",
}


def protocol_of(integration_type: str | None) -> str | None:
    """Return SAML, OIDC or SCIM for a Snowflake security integration type."""
    if not integration_type:
        return None
    prefix = integration_type.split("-", 1)[0].strip().upper()
    return _PROTOCOL_BY_TYPE_PREFIX.get(prefix)


def certificate_fingerprint(certificate: str | None) -> str | None:
    """Return the SHA-256 fingerprint of a SAML signing certificate.

    The certificate body itself is never stored: it is large, it is not a secret but
    it is not useful in the graph either, and the fingerprint is what an operator
    compares when checking whether the identity provider's key has rotated.

    The digest is taken over the certificate's DER bytes, not over its base64 text,
    so the value matches the standard X.509 fingerprint that
    ``openssl x509 -noout -fingerprint -sha256`` reports (which prints the same hex
    colon-separated and upper-cased). Hashing the base64 instead would produce a
    stable but non-comparable value, which is worse than none for an audit check.

    Returns None when the value does not decode, rather than a digest of something
    that is not a certificate.
    """
    if not certificate:
        return None
    body = "".join(line for line in certificate.splitlines() if "-----" not in line)
    body = "".join(body.split())
    if not body:
        return None
    try:
        der = base64.b64decode(body, validate=True)
    except (binascii.Error, ValueError):
        logger.debug(
            "A Snowflake security integration certificate did not decode as base64; "
            "storing no fingerprint for it.",
        )
        return None
    return hashlib.sha256(der).hexdigest()


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Return every security integration, or None when the SQL surface is unavailable."""
    try:
        return client.run_sql("SHOW SECURITY INTEGRATIONS")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            "security integrations", "SHOW SECURITY INTEGRATIONS is not permitted"
        )
        return None


@timeit
def get_details(client: SnowflakeClient, name: str) -> dict[str, str | None] | None:
    """Describe one security integration, or None when it cannot be described."""
    try:
        return client.describe(f"DESC INTEGRATION {sf_fqn(name)}")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            f"security integration {name}", "DESC INTEGRATION is not permitted"
        )
        return None


def transform(
    integrations: list[dict[str, Any]],
    details_by_name: dict[str, dict[str, str | None]],
    account_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for integration in integrations:
        name = integration["name"]
        details = details_by_name.get(name, {})
        integration_type = to_text(integration.get("type"))
        run_as_role = to_text(details.get("run_as_role"))
        network_policy = to_text(details.get("network_policy"))
        transformed.append(
            {
                "id": sf_id(account_id, "security_integration", sf_fqn(name)),
                "name": name,
                "integration_type": integration_type,
                "category": to_text(integration.get("category")),
                "protocol": protocol_of(integration_type),
                "enabled": to_bool(integration.get("enabled")),
                "saml2_issuer": to_text(details.get("saml2_issuer")),
                "saml2_sso_url": to_text(details.get("saml2_sso_url")),
                "saml2_provider": to_text(details.get("saml2_provider")),
                "saml2_x509_cert_fingerprint": certificate_fingerprint(
                    details.get("saml2_x509_cert"),
                ),
                "external_oauth_issuer": to_text(details.get("external_oauth_issuer")),
                "external_oauth_jws_keys_url": to_text(
                    details.get("external_oauth_jws_keys_url")
                ),
                "external_oauth_audience_list": name_list(
                    details.get("external_oauth_audience_list")
                ),
                "external_oauth_any_role_mode": to_text(
                    details.get("external_oauth_any_role_mode")
                ),
                "oauth_client_type": to_text(details.get("oauth_client_type")),
                "oauth_redirect_uri": to_text(details.get("oauth_redirect_uri")),
                "oauth_issue_refresh_tokens": to_bool(
                    details.get("oauth_issue_refresh_tokens")
                ),
                "oauth_refresh_token_validity": to_int(
                    details.get("oauth_refresh_token_validity")
                ),
                "scim_client": to_text(details.get("scim_client")),
                "run_as_role": run_as_role,
                # Null when the integration names no role or policy, which
                # suppresses the edge instead of pointing it at a nonexistent node.
                # Roles and network policies are keyed on the bare name, matching
                # roles.py and users.py.
                "run_as_role_id": (
                    sf_id(account_id, "role", run_as_role) if run_as_role else None
                ),
                "network_policy": network_policy,
                "network_policy_id": (
                    sf_id(account_id, "network_policy", network_policy)
                    if network_policy
                    else None
                ),
                "comment": to_text(integration.get("comment")),
                "created_on": iso_to_datetime(integration.get("created_on")),
            },
        )
    return transformed


def load_security_integrations(
    neo4j_session: neo4j.Session,
    integrations: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeSecurityIntegrationSchema(),
        integrations,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeSecurityIntegrationSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake security integrations.

    Runs after roles and network policies so RUNS_AS_ROLE and GOVERNED_BY resolve on
    the first pass, and before secrets and external access integrations, which point
    back at these nodes.

    Returns whether every integration could be listed and described.
    """
    integrations = get(client)
    if integrations is None:
        return False

    details_by_name: dict[str, dict[str, str | None]] = {}
    complete = True
    for integration in integrations:
        name = integration["name"]
        details = get_details(client, name)
        if details is None:
            complete = False
            continue
        details_by_name[name] = details

    # Only load the integrations whose DESCRIBE succeeded. An integration listed by
    # SHOW but not describable has none of its interesting properties, and loading it
    # anyway would overwrite the values a previous run collected with nulls. Skipping
    # cleanup is not enough on its own, because load() still rewrites the node.
    describable = [
        integration
        for integration in integrations
        if integration["name"] in details_by_name
    ]
    transformed = transform(describable, details_by_name, client.account_id)
    logger.info(
        "Loading %d Snowflake security integrations for account %s.",
        len(transformed),
        client.account_id,
    )
    load_security_integrations(
        neo4j_session,
        transformed,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return complete
