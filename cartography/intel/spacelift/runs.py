import json
import logging
import neo4j
import requests
from typing import Any

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.spacelift.util import call_spacelift_api
from cartography.models.spacelift.run import SpaceliftRunSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# GraphQL query to fetch all managed entities from all stacks
GET_ENTITIES_QUERY = """
query {
    stacks {
        entities {
            type
            creator {
                id
            }
            updater {
                id
            }
            vendor {
                __typename
                ... on EntityVendorTerraform {
                    terraform {
                        __typename
                        ... on TerraformResource {
                            values
                        }
                    }
                }
            }
        }
    }
}
"""

# GraphQL query to fetch runs nested under stacks
# Note: Runs don't have a top-level query, they're nested under stacks
GET_RUNS_QUERY = """
query {
    stacks {
        id
        runs {
            id
            type
            state
            commit {
                hash
            }
            branch
            createdAt
            finished
            triggeredBy
        }
    }
}
"""


@timeit
def get_entities(session: requests.Session, api_endpoint: str) -> list[dict[str, Any]]:
    logger.info("Fetching Spacelift entities")

    response = call_spacelift_api(session, api_endpoint, GET_ENTITIES_QUERY)
    stacks = response.get("data", {}).get("stacks", [])

    # Flatten entities from all stacks into a single list
    all_entities = []
    for stack in stacks:
        all_entities.extend(stack.get("entities", []))

    logger.info(f"Retrieved {len(all_entities)} Spacelift entities from {len(stacks)} stacks")
    return all_entities


def transform_entities_to_run_map(entities_data: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    """
    This function processes entities to extract EC2 instance IDs and maps them to
    the runs that created or updated them.
    """
    logger.info(f"Transforming {len(entities_data)} entities into run-to-instances map")

    run_to_instances: dict[str, list[dict[str, str]]] = {}

    for entity in entities_data:
        # Right now we just cover ec2 
        entity_type = entity.get("type")
        if entity_type != "aws_instance":
            continue

        #  NOTE: Right now we only cover terraform resources but we can extend this to cover other vendors in the future.
        vendor = entity.get("vendor", {})
        if vendor.get("__typename") != "EntityVendorTerraform":
            continue

        terraform_data = vendor.get("terraform", {})
        if terraform_data.get("__typename") != "TerraformResource":
            continue

        values_json = terraform_data.get("values")
        values = json.loads(values_json)
        instance_id = values["id"]

        logger.info(f"Found EC2 instance from entity: {instance_id}")

        # Map to creator run
        creator = entity.get("creator")
        if creator and creator.get("id"):
            creator_run_id = creator["id"]
            if creator_run_id not in run_to_instances:
                run_to_instances[creator_run_id] = []
            run_to_instances[creator_run_id].append({
                "instance_id": instance_id,
                "action": "create",
            })
            logger.info(f"Mapped instance {instance_id} to run {creator_run_id}")

    logger.info(f"Built run-to-instances map with {len(run_to_instances)} runs affecting EC2 instances")
    logger.info(f"Run-to-instances map: {run_to_instances}")
    return run_to_instances


@timeit
def get_runs(session: requests.Session, api_endpoint: str) -> list[dict[str, Any]]:
    logger.info("Fetching Spacelift runs")

    response = call_spacelift_api(session, api_endpoint, GET_RUNS_QUERY)
    stacks = response.get("data", {}).get("stacks", [])

    # Flatten runs from all stacks and add the stack ID to each run
    all_runs = []
    for stack in stacks:
        stack_id = stack["id"]
        for run in stack.get("runs", []):
            # Add the stack ID to each run
            run["stack"] = stack_id
            all_runs.append(run)

    logger.info(f"Retrieved {len(all_runs)} Spacelift runs from {len(stacks)} stacks")
    return all_runs


def transform_runs(
    runs_data: list[dict[str, Any]],
    run_to_instances_map: dict[str, list[dict[str, str]]],
    account_id: str,
) -> list[dict[str, Any]]:
   
    logger.info(f"Transforming {len(runs_data)} runs")

    result: list[dict[str, Any]] = []

    for run in runs_data:
        run_id = run["id"]

        # Look up affected EC2 instances for this run
        affected_instances = run_to_instances_map.get(run_id, [])
        affected_instance_ids = [inst["instance_id"] for inst in affected_instances]

        if affected_instance_ids:
            logger.info(f"Run {run_id} affects instances: {affected_instance_ids}")

        # Extract commit hash from nested commit object
        commit = run.get("commit", {})
        commit_hash = commit.get("hash") if commit else None

        transformed_run = {
            "id": run_id,
            "run_type": run.get("type"),
            "state": run.get("state"),
            "commit_sha": commit_hash,
            "branch": run.get("branch"),
            "created_at": run.get("createdAt"),
            "stack_id": run.get("stack"),
            "triggered_by_user_id": run.get("triggeredBy"),
            "affected_instance_ids": affected_instance_ids,
            "account_id": account_id,
        }

        result.append(transformed_run)

    logger.info(f"Transformed {len(result)} runs ({sum(1 for r in result if r['affected_instance_ids'])} affecting EC2 instances)")
    return result


def extract_users_from_runs(runs_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Extract unique user information from runs' triggeredBy field.
    Filters out system triggers like 'vcs/commit'.

    :param runs_data: Raw run data from API
    :return: List of user dictionaries with id, username, email, name, and user_type
    """
    logger.info("Extracting users from runs")

    user_emails = set()

    for run in runs_data:
        triggered_by = run.get("triggeredBy")
    
        if triggered_by:
            user_emails.add(triggered_by)

    # Create user dictionaries with appropriate user_type
    users = []
    for user_id in sorted(user_emails):
        is_email = "@" in user_id
        users.append({
            "id": user_id,
            "username": user_id,
            "email": user_id if is_email else None,
            "name": user_id.split("@")[0] if is_email else user_id,
            "user_type": "human" if is_email else "system",
        })


    logger.info(f"Extracted {len(users)} unique users from {len(runs_data)} runs")
    return users


def load_users(
    neo4j_session: neo4j.Session,
    users_data: list[dict[str, Any]],
    update_tag: int,
    account_id: str,
) -> None:
    """
    Load Spacelift users data into Neo4j using the data model.
    """
    from cartography.models.spacelift.user import SpaceliftUserSchema

    if not users_data:
        logger.info("No users to load")
        return

    # Add account_id to each user for the relationship
    for user in users_data:
        user["account_id"] = account_id

    load(
        neo4j_session,
        SpaceliftUserSchema(),
        users_data,
        lastupdated=update_tag,
        account_id=account_id,
    )

    logger.info(f"Loaded {len(users_data)} Spacelift users")


def load_runs(
    neo4j_session: neo4j.Session,
    runs_data: list[dict[str, Any]],
    update_tag: int,
    account_id: str,
) -> None:
    """
    Load Spacelift runs data into Neo4j using the data model.
    """
    load(
        neo4j_session,
        SpaceliftRunSchema(),
        runs_data,
        lastupdated=update_tag,
        account_id=account_id,
    )

    logger.info(f"Loaded {len(runs_data)} Spacelift runs")


@timeit
def cleanup_users(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove stale Spacelift user data from Neo4j.
    """
    from cartography.models.spacelift.user import SpaceliftUserSchema

    logger.debug("Running SpaceliftUser cleanup job")
    GraphJob.from_node_schema(SpaceliftUserSchema(), common_job_parameters).run(neo4j_session)


@timeit
def cleanup_runs(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove stale Spacelift run data from Neo4j.
    """
    logger.debug("Running SpaceliftRun cleanup job")
    GraphJob.from_node_schema(SpaceliftRunSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_runs(
    neo4j_session: neo4j.Session,
    spacelift_session: requests.Session,
    api_endpoint: str,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Spacelift runs and users to Neo4j.
    Users are extracted from runs' triggeredBy field.
    """
    # 1. GET - Fetch entities and runs data from Spacelift API
    entities_raw_data = get_entities(spacelift_session, api_endpoint)
    runs_raw_data = get_runs(spacelift_session, api_endpoint)

    # 2. TRANSFORM - Shape data for ingestion
    run_to_instances_map = transform_entities_to_run_map(entities_raw_data)
    transformed_runs = transform_runs(runs_raw_data, run_to_instances_map, account_id)

    # Extract users from runs (before loading runs so TRIGGERED_BY relationship can be created)
    extracted_users = extract_users_from_runs(runs_raw_data)

    # 3. LOAD - Ingest to Neo4j
    # Load users first so the TRIGGERED_BY relationship can be created when runs are loaded
    load_users(neo4j_session, extracted_users, common_job_parameters["UPDATE_TAG"], account_id)
    load_runs(neo4j_session, transformed_runs, common_job_parameters["UPDATE_TAG"], account_id)

    # 4. CLEANUP - Remove stale data
    cleanup_users(neo4j_session, common_job_parameters)
    cleanup_runs(neo4j_session, common_job_parameters)

    logger.info(f"Synced {len(extracted_users)} users and {len(transformed_runs)} Spacelift runs")
