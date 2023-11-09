import logging
import os
from typing import List
from typing import Union

from marshmallow import ValidationError

from cartography.driftdetect.config import GetDriftConfig
from cartography.driftdetect.model import State
from cartography.driftdetect.reporter import report_drift
from cartography.driftdetect.serializers import ShortcutSchema
from cartography.driftdetect.serializers import StateSchema
from cartography.driftdetect.storage import FileSystem
from cartography.driftdetect.util import valid_directory

logger = logging.getLogger(__name__)


def run_drift_detection(config: GetDriftConfig) -> None:
    try:
        if not valid_directory(config.query_directory):
            logger.error("Invalid Drift Detection Directory")
            return
        state_serializer = StateSchema()
        shortcut_serializer = ShortcutSchema()
        shortcut_data = FileSystem.load(os.path.join(config.query_directory, "shortcut.json"))
        shortcut = shortcut_serializer.load(shortcut_data)
        start_state_data = FileSystem.load(
            os.path.join(
                config.query_directory, shortcut.shortcuts.get(
                    config.start_state,
                    config.start_state,
                ),
            ),
        )
        start_state = state_serializer.load(start_state_data)
        end_state_data = FileSystem.load(
            os.path.join(
                config.query_directory, shortcut.shortcuts.get(
                    config.end_state,
                    config.end_state,
                ),
            ),
        )
        end_state = state_serializer.load(end_state_data)
        new_results, missing_results = perform_drift_detection(start_state, end_state)
        report_drift(new_results, missing_results, end_state.name, end_state.properties)
    except ValidationError as err:
        msg = "Unable to create DriftStates from files {},{} for \n{} in directory {}.".format(
            config.start_state,
            config.end_state,
            err.messages,
            config.query_directory,
        )
        logger.exception(msg)
    except ValueError as err:
        msg = "Unable to create DriftStates from files {},{} for \n{} in directory {}.".format(
            config.start_state,
            config.end_state,
            err,
            config.query_directory,
        )
        logger.exception(msg)


def perform_drift_detection(start_state: State, end_state: State):
    """
    Returns differences (additions and missing results) between two States.

    :type start_state: State
    :param start_state: The earlier state chronologically to be compared to.
    :type end_state: State
    :param end_state: The later state chronologically to be compared to.
    :return: tuple of additions and subtractions between the end and start detector in the form of drift_info_detector
    pairs
    """
    if start_state.name != end_state.name:
        raise ValueError("State names do not match.")
    if start_state.validation_query != end_state.validation_query:
        raise ValueError("State queries do not match.")
    if start_state.properties != end_state.properties:
        raise ValueError("State properties do not match.")
    new_results = compare_states(start_state, end_state)
    missing_results = compare_states(end_state, start_state)
    return new_results, missing_results


def compare_states(start_state: State, end_state: State):
    """
    Helper function for comparing differences between two States.

    :type start_state: State
    :param start_state: The earlier state chronologically to be compared to.
    :type end_state: State
    :param end_state: The later state chronologically to be compared to.
    :return: list of tuples of differences between states in the form (dictionary, State object)
    """
    differences = []
    # Use set for faster membership check
    start_state_results = {tuple(res) for res in start_state.results}
    for result in end_state.results:
        if tuple(result) in start_state_results:
            continue
        drift: List[Union[str, List[str]]] = []
        for field in result:
            value = field.split("|")
            if len(value) > 1:
                drift.append(value)
            else:
                drift.append(field)
        differences.append(drift)
    return differences
