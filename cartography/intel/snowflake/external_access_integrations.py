"""Snowflake external access integrations.

There is no object endpoint for external access integrations, so they come from
``SHOW EXTERNAL ACCESS INTEGRATIONS`` through the SQL API. This is the object that
decides whether Python or Java handler code running inside Snowflake may reach the
internet at all, and which secrets it may read while doing so, so its allow-lists are
resolved into real edges toward the network rule, secret and security integration
nodes.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.names import name_list
from cartography.intel.snowflake.names import split_qualified_name
from cartography.intel.snowflake.sql_values import to_bool
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.external_access_integration import (
    SnowflakeExternalAccessIntegrationSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


def referenced_id(account_id: str, object_type: str, reference: str) -> str:
    """Build the node id of an object the integration references by qualified name.

    ``SHOW`` reports the allow-lists as already-qualified names, so the components are
    split back out and re-joined through ``sf_fqn`` to guarantee the id is quoted
    exactly the way the referenced object's own id was built.
    """
    return sf_id(account_id, object_type, sf_fqn(*split_qualified_name(reference)))


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Return every external access integration, or None when unavailable."""
    try:
        return client.run_sql("SHOW EXTERNAL ACCESS INTEGRATIONS")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            "external access integrations",
            "SHOW EXTERNAL ACCESS INTEGRATIONS is not permitted",
        )
        return None


def transform(
    integrations: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for integration in integrations:
        name = integration["name"]
        # SHOW renders these as a bracketed "[A, B]" string rather than a JSON
        # array, which name_list normalises.
        network_rules = name_list(integration.get("allowed_network_rules"))
        secrets = name_list(integration.get("allowed_authentication_secrets"))
        auth_integrations = name_list(
            integration.get("allowed_api_authentication_integrations"),
        )
        transformed.append(
            {
                # Keyed on the bare name, matching
                # names.external_access_integration_ids, which the function,
                # procedure and service syncs use to point at these nodes.
                "id": sf_id(account_id, "external_access_integration", name),
                "name": name,
                "enabled": to_bool(integration.get("enabled")),
                "allowed_network_rules": network_rules,
                "allowed_authentication_secrets": secrets,
                "allowed_api_authentication_integrations": auth_integrations,
                "allowed_network_rule_ids": [
                    referenced_id(account_id, "network_rule", rule)
                    for rule in network_rules
                ],
                "allowed_secret_ids": [
                    referenced_id(account_id, "secret", secret) for secret in secrets
                ],
                "allowed_auth_integration_ids": [
                    referenced_id(account_id, "security_integration", integration_name)
                    for integration_name in auth_integrations
                ],
                "comment": to_text(integration.get("comment")),
                "created_on": iso_to_datetime(integration.get("created_on")),
            },
        )
    return transformed


def load_external_access_integrations(
    neo4j_session: neo4j.Session,
    integrations: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeExternalAccessIntegrationSchema(),
        integrations,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeExternalAccessIntegrationSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake external access integrations.

    Runs after network rules, secrets and security integrations so every allow-list
    edge resolves on the first pass, and before services, which point back at these
    nodes.
    """
    integrations = get(client)
    if integrations is None:
        return False

    transformed = transform(integrations, client.account_id)
    logger.info(
        "Loading %d Snowflake external access integrations for account %s.",
        len(transformed),
        client.account_id,
    )
    load_external_access_integrations(
        neo4j_session,
        transformed,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return True
