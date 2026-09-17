import hashlib
import json
import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.account_usage import normalize_role_reference
from cartography.intel.snowflake.sql_values import to_bool
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.models.snowflake.inherited_grant import SnowflakeInheritedGrantSchema

logger = logging.getLogger(__name__)


def transform(rows: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    grants = []
    for row in rows:
        scope = to_text(row.get("inherited_from"))
        database = to_text(row.get("inherited_from_database"))
        schema = to_text(row.get("inherited_from_schema"))
        privilege = to_text(row.get("privilege"))
        object_type = to_text(row.get("granted_on"))
        grantee = to_text(row.get("grantee_name"))
        grantee_type = (to_text(row.get("granted_to")) or "").replace("_", " ")
        if not privilege or not object_type or not grantee or not grantee_type:
            raise ValueError(
                "Snowflake inherited grant is missing its privilege, object type, or grantee"
            )
        if scope == "ACCOUNT":
            container_id = account_id
        elif scope == "DATABASE" and database:
            container_id = sf_id(account_id, "database", sf_fqn(database))
        elif scope == "SCHEMA" and database and schema:
            container_id = sf_id(account_id, "schema", sf_fqn(database, schema))
        else:
            raise ValueError(
                "Snowflake inherited grant has an invalid or incomplete container scope"
            )
        principal_kind = {
            "ROLE": "role",
            "ACCOUNT ROLE": "role",
            "DATABASE ROLE": "database_role",
            "USER": "user",
        }.get(grantee_type)
        principal_name = normalize_role_reference(
            grantee, grantee_type == "DATABASE ROLE"
        )
        principal_id = (
            sf_id(account_id, principal_kind, principal_name)
            if principal_kind
            else None
        )
        grantor = to_text(row.get("granted_by"))
        # Keep TABLE SELECT distinct from VIEW SELECT, and from ordinary database privileges.
        identity = json.dumps(
            [
                grantee_type,
                principal_name,
                container_id,
                object_type,
                privilege,
                grantor,
            ]
        )
        grants.append(
            {
                "id": sf_id(
                    account_id,
                    "inherited_grant",
                    hashlib.sha256(identity.encode()).hexdigest(),
                ),
                "principal_id": principal_id,
                "container_id": container_id,
                "privilege": privilege,
                "object_type": object_type,
                "container_type": scope,
                "database_name": database,
                "schema_name": schema,
                "grantee_name": grantee,
                "grantee_type": grantee_type,
                "grant_option": to_bool(row.get("grant_option")),
                "granted_by": grantor,
                "created_on": iso_to_datetime(row.get("created_on")),
            }
        )
    return grants


def load_grants(
    neo4j_session: neo4j.Session,
    rows: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    grants = transform(rows, account_id)
    logger.info("Loading %d Snowflake inherited grant records.", len(grants))
    load(
        neo4j_session,
        SnowflakeInheritedGrantSchema(),
        grants,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, account_id: str, update_tag: int) -> None:
    GraphJob.from_node_schema(
        SnowflakeInheritedGrantSchema(),
        {"ACCOUNT_ID": account_id, "UPDATE_TAG": update_tag},
    ).run(neo4j_session)
