import logging
import os.path
import time
from typing import Any
from typing import Dict
from typing import List

import neo4j.exceptions
from marshmallow import ValidationError
from neo4j import GraphDatabase

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.driftdetect.add_shortcut import add_shortcut
from cartography.driftdetect.config import UpdateConfig
from cartography.driftdetect.model import State
from cartography.driftdetect.serializers import ShortcutSchema
from cartography.driftdetect.serializers import StateSchema
from cartography.driftdetect.storage import FileSystem
from cartography.driftdetect.util import valid_directory

logger = logging.getLogger(__name__)


def run_get_states(config: UpdateConfig) -> None:
    """
    Handles neo4j errors and then updates detectors.

    :type config: Config Object
    :param config: Config Object from CLI
    :return:
    """
    if not valid_directory(config.drift_detection_directory):
        logger.error("Invalid Drift Detection Directory")
        return
    neo4j_auth = None
    if config.neo4j_user or config.neo4j_password:
        neo4j_auth = (config.neo4j_user, config.neo4j_password)
    try:
        neo4j_driver = GraphDatabase.driver(
            config.neo4j_uri,
            auth=neo4j_auth,
        )
    except neo4j.exceptions.ServiceUnavailable as e:
        logger.debug("Error occurred during Neo4j connect.", exc_info=True)
        logger.error(
            (
                "Unable to connect to Neo4j using the provided URI '%s', an error occurred: '%s'. Make sure the "
                "Neo4j server is running and accessible from your network."
            ),
            config.neo4j_uri,
            e,
        )
        return
    except neo4j.exceptions.AuthError as e:
        logger.debug("Error occurred during Neo4j auth.", exc_info=True)
        if not neo4j_auth:
            logger.error(
                (
                    "Unable to auth to Neo4j, an error occurred: '%s'. driftdetect attempted to connect to Neo4j "
                    "without any auth. Check your Neo4j server settings to see if auth is required and, if it is, "
                    "provide driftdetect with a valid username and password."
                ),
                e,
            )
        else:
            logger.error(
                (
                    "Unable to auth to Neo4j, an error occurred: '%s'. driftdetect attempted to connect to Neo4j "
                    "with a username and password. Check your Neo4j server settings to see if the username and "
                    "password provided to driftdetect are valid credentials."
                ),
                e,
            )
        return

    with neo4j_driver.session() as session:
        filename = '.'.join([str(i) for i in time.gmtime()] + ["json"])
        state_serializer = StateSchema()
        shortcut_serializer = ShortcutSchema()
        for query_directory in FileSystem.walk(config.drift_detection_directory):
            try:
                get_query_state(session, query_directory, state_serializer, FileSystem, filename)
                add_shortcut(FileSystem, shortcut_serializer, query_directory, 'most-recent', filename)
            except ValidationError as err:
                msg = "Unable to create State for directory {}, with data \n{}".format(
                    query_directory,
                    err.messages,
                )
                logger.exception(msg)
            except KeyError as err:
                msg = f"Could not find {err} field in state template for directory {query_directory}."
                logger.exception(msg)
            except FileNotFoundError as err:
                logger.exception(err)
            except neo4j.exceptions.CypherSyntaxError as err:
                logger.exception(err)


def get_query_state(
        session: neo4j.Session,
        query_directory: str,
        state_serializer: StateSchema,
        storage,
        filename: str,
) -> State:
    """
    Gets the most recent state of a query.

    :type session: neo4j session.
    :param session: neo4j session to connect to.
    :type query_directory: String.
    :param query_directory: Path to query directory.
    :type state_serializer: Schema
    :param state_serializer: Schema to serialize and deserialize states.
    :type storage: Storage Object.
    :param storage: Storage object to supports loading, writing, and walking.
    :type filename: String.
    :param filename: Path to filename.
    :return: The created state.
    """
    state_data = storage.load(os.path.join(query_directory, "template.json"))
    state = state_serializer.load(state_data)
    get_state(session, state)
    new_state_data = state_serializer.dump(state)
    fp = os.path.join(query_directory, filename)
    storage.write(new_state_data, fp)
    return state


def get_state(session: neo4j.Session, state: State) -> None:
    """
    Connects to a neo4j session, runs the validation query, then saves the results to a state.

    :type session: neo4j session
    :param session: Graph session to pull infrastructure information from.
    :type state: State
    :param state: State to be updated.
    :return:
    """

    new_results: List[Dict[str, Any]] = session.read_transaction(
        read_list_of_dicts_tx,
        state.validation_query,
    )
    logger.debug(f"Updating results for {state.name}")

    # The keys will be the same across all items in the returned list
    state.properties = list(new_results[0].keys()) if len(new_results) > 0 else []

    results = []
    for record in new_results:
        values = []
        for field in record.values():
            if isinstance(field, list):
                s = "|".join(sorted(str(i) for i in field))
                values.append(s)
            else:
                values.append(str(field))
        results.append(values)

    state.results = sorted(results)
