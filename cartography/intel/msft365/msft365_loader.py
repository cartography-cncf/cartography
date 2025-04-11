import logging
from typing import List, Dict
import neo4j
from cartography.models.msft365 import (
    Msft365UserSchema,
    Msft365GroupSchema,
    Msft365DeviceSchema,
    Msft365OrganizationalUnitSchema,
    Msft365UserToDeviceRelSchema,
    Msft365UserToGroupRelSchema,
)

logger = logging.getLogger(__name__)


def msft365_load_users(neo4j_session: neo4j.Session, users: List[Dict], update_tag: str) -> None:
    user_data = [{**u, "lastupdated": update_tag} for u in users]
    schema = Msft365UserSchema()
    for record in user_data:
        cypher, params = schema.create_node_merge_statement(record, update_tag)
        neo4j_session.run(cypher, params)
    logger.info(f"Loaded {len(user_data)} users")


def msft365_load_groups(neo4j_session: neo4j.Session, groups: List[Dict], update_tag: str) -> None:
    group_data = [{**g, "lastupdated": update_tag} for g in groups]
    schema = Msft365GroupSchema()
    for record in group_data:
        cypher, params = schema.create_node_merge_statement(record, update_tag)
        neo4j_session.run(cypher, params)
    logger.info(f"Loaded {len(group_data)} groups")


def msft365_load_devices(neo4j_session: neo4j.Session, devices: List[Dict], update_tag: str) -> None:
    device_data = [{**d, "lastupdated": update_tag} for d in devices]
    schema = Msft365DeviceSchema()
    for record in device_data:
        cypher, params = schema.create_node_merge_statement(record, update_tag)
        neo4j_session.run(cypher, params)
    logger.info(f"Loaded {len(device_data)} devices")


def msft365_load_organizational_units(neo4j_session: neo4j.Session, ous: List[Dict], update_tag: str) -> None:
    if not ous:
        return
    ou_data = [{**ou, "lastupdated": update_tag} for ou in ous]
    schema = Msft365OrganizationalUnitSchema()
    for record in ou_data:
        cypher, params = schema.create_node_merge_statement(record, update_tag)
        neo4j_session.run(cypher, params)
    logger.info(f"Loaded {len(ou_data)} organizational units")


def msft365_run_cleanup_jobs(neo4j_session, common_job_parameters: Dict) -> None:
    """Run schema-based cleanup for Microsoft 365 integration."""
    logger.info("Running Microsoft 365 cleanup jobs")

    schemas = [
        Msft365UserSchema(),
        Msft365GroupSchema(),
        Msft365OrganizationalUnitSchema(),
        Msft365DeviceSchema(),
    ]

    for schema in schemas:
        logger.debug(f"Running cleanup job for {schema.label}")
        cleanup_query, params = schema.create_cleanup_job(common_job_parameters)
        neo4j_session.run(cleanup_query, params)

def msft365_load_device_ownership(neo4j_session, relationships: List[Dict], update_tag: str) -> None:
    """Load user-to-device ownership relationships."""
    if not relationships:
        return
    schema = Msft365UserToDeviceRelSchema()
    for rel in relationships:
        cypher, params = schema.create_relationship_statement(rel, update_tag)
        neo4j_session.run(cypher, params)
    logger.info(f"Loaded {len(relationships)} user-to-device relationships")


def msft365_load_group_membership(neo4j_session, relationships: List[Dict], update_tag: str) -> None:
    """Load user-to-group membership relationships."""
    if not relationships:
        return
    schema = Msft365UserToGroupRelSchema()
    for rel in relationships:
        cypher, params = schema.create_relationship_statement(rel, update_tag)
        neo4j_session.run(cypher, params)
    logger.info(f"Loaded {len(relationships)} user-to-group membership relationships")