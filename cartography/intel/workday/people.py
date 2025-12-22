import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests
from requests.auth import HTTPBasicAuth

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.workday.human import WorkdayHumanSchema
from cartography.models.workday.organization import WorkdayOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Timeout for API requests (connect timeout, read timeout) in seconds
_TIMEOUT = (60, 60)


@timeit
def get_workday_directory(
    workday_api_url: str, workday_login: str, workday_password: str
) -> Dict[str, Any]:
    """
    Fetches data from the Workday API.

    :param workday_api_url: The Workday API URL
    :param workday_login: The Workday API login
    :param workday_password: The Workday API password
    :return: a dictionary representing the JSON response from the API
    :raises Exception: if the API returns a non-200 status code, or if the response can't be parsed as JSON
    """
    http_auth = HTTPBasicAuth(workday_login, workday_password)
    response = requests.get(workday_api_url, auth=http_auth, timeout=_TIMEOUT)

    if response.status_code != 200:
        raise Exception(
            f"Workday API returned HTTP {response.status_code}. Check credentials and API endpoint."
        )

    try:
        directory = response.json()
    except ValueError as e:
        raise Exception(f"Unable to parse Workday API response as JSON: {e}")

    if not directory:
        raise Exception(
            "Workday API returned empty response (HTTP 200). Check API configuration."
        )

    return directory


@timeit
def _transform_people_data(
    directory_data: Dict[str, Any],
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Transform Workday directory data into separate lists for people and manager relationships.

    :param directory_data: Raw data from Workday API
    :return: Tuple of (people_list, manager_relationships_list)
    """
    people = directory_data.get("Report_Entry", [])
    logger.info(f"Transforming {len(people)} people from Workday")

    people_transformed = []
    manager_relationships = []

    for person in people:
        # Extract manager ID from nested structure for the schema
        manager_id = None
        manager_group = person.get("Worker_s_Manager_group", [])
        if manager_group and len(manager_group) > 0:
            manager_id = manager_group[0].get("Manager_ID")

        # Transform Workday API fields to clean property names
        # Don't spread person to avoid duplicate fields with hyphens
        person_data = {
            # Core identification (keep original field names)
            "Employee_ID": person.get("Employee_ID"),
            "Name": person.get("Name"),
            "businessTitle": person.get("businessTitle"),
            "Worker_Type": person.get("Worker_Type"),
            "location": person.get("location"),
            "Team": person.get("Team"),
            "Sub_Team": person.get("Sub_Team"),
            "Company": person.get("Company"),
            "Supervisory_Organization": person.get("Supervisory_Organization"),
            "Manager_ID": manager_id,  # Flat field for schema relationship
            # Map API fields with hyphens to clean property names
            "email": person.get("Email_-_Work"),
            "country": person.get("Location_Address_-_Country"),
            "cost_center": person.get("Cost_Center"),
            "function": person.get("GBL-Custom-Function"),
            "sub_function": person.get("Sub-Function"),
            "source": "WORKDAY",
        }
        people_transformed.append(person_data)

        # Track manager relationships for validation/debugging
        employee_id = person.get("Employee_ID")
        if manager_id and employee_id and manager_id != employee_id:
            manager_relationships.append(
                {
                    "Employee_ID": employee_id,
                    "Manager_ID": manager_id,
                }
            )

    return people_transformed, manager_relationships


@timeit
def _load_organizations(
    neo4j_session: neo4j.Session,
    people_data: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load organization nodes into Neo4j.

    :param neo4j_session: Neo4j session
    :param people_data: List of people data containing organization information
    :param update_tag: Update tag for tracking data freshness
    """
    # Extract unique organizations from people data
    organizations = []
    seen_orgs = set()
    for person in people_data:
        org_name = person.get("Supervisory_Organization")
        if org_name and org_name not in seen_orgs:
            organizations.append({"Supervisory_Organization": org_name})
            seen_orgs.add(org_name)

    logger.info(f"Loading {len(organizations)} Workday organizations")
    load(
        neo4j_session,
        WorkdayOrganizationSchema(),
        organizations,
        lastupdated=update_tag,
    )


@timeit
def _load_people(
    neo4j_session: neo4j.Session,
    people_data: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load people nodes and their organization relationships into Neo4j.

    :param neo4j_session: Neo4j session
    :param people_data: List of transformed people data
    :param update_tag: Update tag for tracking data freshness
    """
    logger.info(f"Loading {len(people_data)} Workday people")
    load(
        neo4j_session,
        WorkdayHumanSchema(),
        people_data,
        lastupdated=update_tag,
    )


@timeit
def _load_manager_relationships(
    neo4j_session: neo4j.Session,
    manager_relationships: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load manager (REPORTS_TO) relationships into Neo4j.

    NOTE: This function is now a no-op. Manager relationships are created automatically
    when _load_people() is called, via the WorkdayHumanToManagerRel relationship defined
    in the WorkdayHumanSchema. The Manager_ID field in the people_data is used to create
    the REPORTS_TO relationships.

    This function is kept for backward compatibility and logging purposes.

    :param neo4j_session: Neo4j session
    :param manager_relationships: List of manager relationship data (used only for logging)
    :param update_tag: Update tag for tracking data freshness
    """
    logger.info(
        f"Manager relationships ({len(manager_relationships)}) are created automatically "
        "via WorkdayHumanSchema when loading people"
    )


@timeit
def _cleanup_workday_data(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Remove stale Workday data from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters including UPDATE_TAG
    """
    # Cleanup humans
    GraphJob.from_node_schema(WorkdayHumanSchema(), common_job_parameters).run(
        neo4j_session
    )
    # Cleanup organizations
    GraphJob.from_node_schema(WorkdayOrganizationSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_workday_people(
    neo4j_session: neo4j.Session,
    workday_api_url: str,
    workday_login: str,
    workday_password: str,
    update_tag: int,
) -> None:
    """
    Synchronizes Workday people data with Neo4j.

    :param neo4j_session: Neo4j session
    :param workday_api_url: The Workday API URL
    :param workday_login: The Workday API login
    :param workday_password: The Workday API password
    :param update_tag: Update tag for tracking data freshness
    """
    common_job_parameters = {
        "UPDATE_TAG": update_tag,
    }

    logger.info("Syncing Workday people data")

    # Fetch data from Workday API
    workday_data = get_workday_directory(
        workday_api_url, workday_login, workday_password
    )

    # Transform data
    people_data, manager_relationships = _transform_people_data(workday_data)

    # Load organizations first (as they're referenced by people)
    _load_organizations(neo4j_session, people_data, update_tag)

    # Load people and their organization relationships
    _load_people(neo4j_session, people_data, update_tag)

    # Load manager relationships
    _load_manager_relationships(neo4j_session, manager_relationships, update_tag)

    # Cleanup stale data
    _cleanup_workday_data(neo4j_session, common_job_parameters)
