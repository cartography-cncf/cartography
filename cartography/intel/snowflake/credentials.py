"""Snowflake credentials.

``SNOWFLAKE.ACCOUNT_USAGE.CREDENTIALS`` is the only enumeration of every
authentication factor in an account, which makes it the source of truth for MFA,
passkey, TOTP and key-pair posture. It needs ``IMPORTED PRIVILEGES ON DATABASE
SNOWFLAKE`` and lags reality by up to two hours.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.credential import SnowflakeCredentialSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_CREDENTIALS_STATEMENT = """
SELECT CREDENTIAL_ID, NAME, USER_NAME, TYPE, DOMAIN, COMMENT, STATUS,
       ADDITIONAL_DETAILS, CREATED_BY, LAST_ALTERED_BY, CREATED_ON, LAST_USED_ON,
       LAST_ALTERED, EXPIRATION_DATE
FROM SNOWFLAKE.ACCOUNT_USAGE.CREDENTIALS
"""


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Every credential in the account, or None when ACCOUNT_USAGE is unreadable."""
    try:
        return client.run_sql(_CREDENTIALS_STATEMENT)
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            "credentials",
            "ACCOUNT_USAGE.CREDENTIALS needs IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE",
        )
        return None


def transform(
    credentials: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    """Shape credential rows into nodes.

    The node key includes the credential type as well as the user and the credential
    name, because Snowflake names some factors after their type: a user can hold both
    a ``PASSWORD`` and a ``TOTP`` entry whose names collide otherwise, and merging
    them would hide a factor.

    The owning user's id is recomputed from the user name using the same key the user
    sync builds, since ``ACCOUNT_USAGE`` reports the name rather than an id.
    """
    transformed: list[dict[str, Any]] = []

    for credential in credentials:
        name = credential["name"]
        user_name = credential["user_name"]
        credential_type = credential["type"]
        transformed.append(
            {
                "id": sf_id(
                    account_id,
                    "credential",
                    sf_fqn(user_name, credential_type, name),
                ),
                "name": name,
                "credential_id": to_text(credential.get("credential_id")),
                "credential_type": credential_type,
                "user_name": user_name,
                "user_id": sf_id(account_id, "user", user_name),
                "domain": to_text(credential.get("domain")),
                "status": to_text(credential.get("status")),
                "additional_details": to_text(credential.get("additional_details")),
                "comment": to_text(credential.get("comment")),
                "created_by": to_text(credential.get("created_by")),
                "last_altered_by": to_text(credential.get("last_altered_by")),
                "created_on": iso_to_datetime(credential.get("created_on")),
                "last_used_on": iso_to_datetime(credential.get("last_used_on")),
                "last_altered": iso_to_datetime(credential.get("last_altered")),
                "expiration_date": iso_to_datetime(credential.get("expiration_date")),
            },
        )

    return transformed


def load_credentials(
    neo4j_session: neo4j.Session,
    credentials: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeCredentialSchema(),
        credentials,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeCredentialSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync credentials.

    Runs after users so every ownership edge resolves on the first pass.

    Returns whether ``ACCOUNT_USAGE`` could be read. When it could not, the caller
    skips credential cleanup so previously collected credentials are not deleted.
    """
    credentials = get(client)
    if credentials is None:
        return False

    transformed = transform(credentials, client.account_id)
    logger.info(
        "Loading %d Snowflake credentials for account %s.",
        len(transformed),
        client.account_id,
    )
    load_credentials(
        neo4j_session,
        transformed,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return True
