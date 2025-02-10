import logging
import os

from marshmallow import ValidationError

from cartography.driftdetect.serializers import ShortcutSchema
from cartography.driftdetect.storage import FileSystem
from cartography.driftdetect.util import valid_directory

logger = logging.getLogger(__name__)


def run_add_shortcut(config):
    """
    Runs add_shortcut from the command line. Does error handling.

    :type config: Config Object
    :param config: Config of adding shortcut
    :return:
    """
    if not valid_directory(config.query_directory):
        logger.error("Invalid Drift Detection Directory")
        return
    try:
        add_shortcut(
            FileSystem,
            ShortcutSchema(),
            config.query_directory,
            config.shortcut,
            config.filename,
        )
    except ValidationError as err:
        msg = "Could not load shortcut file from json file {} in query directory {}.".format(
            err.messages,
            config.query_directory,
        )
        logger.exception(msg)


def add_shortcut(storage, shortcut_serializer, query_directory, alias, filename):
    """
    Adds a shortcut to the Report_Info File. If a shortcut already exists for an alias, it replaces that shortcut.

    :type storage: Storage Object.
    :param storage: Type of Storage System.
    :type shortcut_serializer: Shortcut Schema.
    :param shortcut_serializer: Shortcut Serializer. Should serialize and deserialize between JSON and Shortcut Object
    :type query_directory: String.
    :param query_directory: Path to Query Directory.
    :type alias: String.
    :param alias: Alias for the file.
    :type filename: String.
    :param filename: Name of file or shortcut to that file.
    :return:
    """
    if storage.has_file(os.path.join(query_directory, alias)):
        logger.error(
            f"Shortcut {alias} is the name of another File in directory {query_directory}.",
        )
        return
    shortcut_path = os.path.join(query_directory, "shortcut.json")
    shortcut_data = storage.load(shortcut_path)
    shortcut = shortcut_serializer.load(shortcut_data)
    fp = shortcut.shortcuts.get(filename, filename)
    if not storage.has_file(os.path.join(query_directory, fp)):
        logger.error(f"File {fp} not found in directory {query_directory}.")
        return
    shortcut.shortcuts[alias] = fp
    new_shortcut_data = shortcut_serializer.dump(shortcut)
    storage.write(new_shortcut_data, shortcut_path)
