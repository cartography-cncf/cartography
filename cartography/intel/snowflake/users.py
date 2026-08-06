import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.user import SnowflakeServiceUserSchema
from cartography.models.snowflake.user import SnowflakeUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Snowflake reports a machine identity with one of these `type` values. A null
# type is a plain human user: Snowflake leaves the field unset for users created
# before it existed and for users created without an explicit TYPE.
_SERVICE_USER_TYPES = ("SERVICE", "LEGACY_SERVICE")


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]]:
    return client.list_all("/api/v2/users")


@timeit
def get_mfa_enrollment(client: SnowflakeClient) -> dict[str, bool]:
    """Return ``{user name: has_mfa}``, empty when it cannot be read.

    MFA enrollment is the one materially security-relevant user field the REST
    API does not expose, so it has to come from ``SHOW USERS``. That needs a role
    that can see other users, so an unprivileged collector gets an empty mapping
    and ``has_mfa`` stays null rather than being wrongly reported as false.
    """
    try:
        rows = client.run_sql("SHOW USERS")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable("user MFA enrollment", "SHOW USERS is not permitted")
        return {}

    enrollment: dict[str, bool] = {}
    for row in rows:
        name = row.get("name")
        if name:
            enrollment[str(name)] = str(row.get("has_mfa", "")).lower() == "true"
    return enrollment


def transform(
    users: list[dict[str, Any]],
    mfa_enrollment: dict[str, bool],
    account_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split the user listing into human users and service users.

    Returns ``(human users, service users)``. The two go to different labels
    because ontology mappings are keyed by node label, so a single label would
    project both user-account and service-account fields onto every user.

    Note that the payload contains a redacted ``password`` field. It is
    deliberately not carried onto the node: a masked value is not information, and
    ``has_password`` already records what matters.
    """
    humans: list[dict[str, Any]] = []
    services: list[dict[str, Any]] = []

    for user in users:
        name = user["name"]
        user_type = user.get("type")
        network_policy_name = user.get("network_policy")
        transformed = {
            "id": sf_id(account_id, "user", name),
            "name": name,
            "login_name": user.get("login_name"),
            "email": user.get("email"),
            "display_name": user.get("display_name"),
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "user_type": user_type,
            "disabled": user.get("disabled"),
            "has_password": user.get("has_password"),
            "has_mfa": mfa_enrollment.get(name),
            "has_rsa_public_key": user.get("has_rsa_public_key"),
            "rsa_public_key_fp": user.get("rsa_public_key_fp"),
            "rsa_public_key_2_fp": user.get("rsa_public_key_2_fp"),
            "must_change_password": user.get("must_change_password"),
            "days_to_expiry": user.get("days_to_expiry"),
            "mins_to_unlock": user.get("mins_to_unlock"),
            "mins_to_bypass_mfa": user.get("mins_to_bypass_mfa"),
            "mins_to_bypass_network_policy": user.get("mins_to_bypass_network_policy"),
            "network_policy_name": network_policy_name,
            # Null when the user has no policy of its own, which suppresses the
            # GOVERNED_BY edge instead of pointing it at a nonexistent node.
            "network_policy_id": (
                sf_id(account_id, "network_policy", network_policy_name)
                if network_policy_name
                else None
            ),
            "default_role": user.get("default_role"),
            "default_secondary_roles": user.get("default_secondary_roles"),
            "default_warehouse": user.get("default_warehouse"),
            "default_namespace": user.get("default_namespace"),
            "ext_authn_duo": user.get("ext_authn_duo"),
            "snowflake_lock": user.get("snowflake_lock"),
            "snowflake_support": user.get("snowflake_support"),
            "comment": user.get("comment"),
            "owner": user.get("owner"),
            "password_last_set": iso_to_datetime(user.get("password_last_set")),
            "last_successful_login": iso_to_datetime(user.get("last_successful_login")),
            "locked_until": iso_to_datetime(user.get("locked_until")),
            "expires_at": iso_to_datetime(user.get("expires_at")),
            "created_on": iso_to_datetime(user.get("created_on")),
        }
        if user_type in _SERVICE_USER_TYPES:
            services.append(transformed)
        else:
            humans.append(transformed)

    return humans, services


def load_users(
    neo4j_session: neo4j.Session,
    humans: list[dict[str, Any]],
    services: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeUserSchema(),
        humans,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    load(
        neo4j_session,
        SnowflakeServiceUserSchema(),
        services,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeUserSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(SnowflakeServiceUserSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Sync Snowflake users and return ``(human users, service users)``.

    Runs after network policies so a user's GOVERNED_BY edge resolves against a
    policy node already in the graph.

    The two lists are returned because later syncs need them: the access-token
    sync attaches tokens to their owning user, and the grant sync needs the set of
    service-user names to route a role assignment to the right label.
    """
    users = get(client)
    mfa_enrollment = get_mfa_enrollment(client)
    humans, services = transform(users, mfa_enrollment, client.account_id)
    logger.info(
        "Loading %d Snowflake human users and %d service users for account %s.",
        len(humans),
        len(services),
        client.account_id,
    )
    load_users(
        neo4j_session,
        humans,
        services,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return humans, services
