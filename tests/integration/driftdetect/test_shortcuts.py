import os
import pytest

from cartography.driftdetect.storage import FileSystem
from cartography.driftdetect.serializers import ShortcutSchema
from cartography.driftdetect.cli import CLI


def test_basic_add_shortcuts():
    """
    Tests that the CLI can add shortcuts.
    """
    cli = CLI(prog="cartography-detectdrift")
    directory = "tests/data/test_cli_detectors/detector"
    alias = "test_shortcut"
    file = "1.json"
    shortcut_path = directory + '/shortcut.json'
    cli.main(["add-shortcut",
              "--query-directory",
              directory,
              "--shortcut",
              alias,
              "--file",
              file])
    shortcut_data = FileSystem.load(shortcut_path)
    shortcut = ShortcutSchema().load(shortcut_data)
    assert shortcut.shortcuts[alias] == file
    shortcut.shortcuts.pop(alias)
    shortcut_data = ShortcutSchema().dump(shortcut)
    FileSystem.write(shortcut_data, shortcut_path)


def test_nonexistent_shortcuts():
    cli = CLI(prog="cartography-detectdrift")
    directory = "tests/data/test_cli_detectors/detector"
    alias = "test_shortcut"
    file = "3.json"
    shortcut_path = os.path.join(directory, "shortcut.json")
    cli.main(["add-shortcut",
              "--query-directory",
              directory,
              "--shortcut",
              alias,
              "--file",
              file])
    shortcut_data = FileSystem.load(shortcut_path)
    shortcut = ShortcutSchema().load(shortcut_data)
    with pytest.raises(KeyError):
        shortcut.shortcuts[alias]


def test_bad_shortcut():
    cli = CLI(prog="cartography-detectdrift")
    directory = "tests/data/test_cli_detectors/bad_shortcut"
    start_state = "1.json"
    end_state = "invalid-shortcut"
    with pytest.raises(FileNotFoundError):
        cli.main(["get-drift",
                  "--query-directory",
                  directory,
                  "--start-state",
                  start_state,
                  "--end-state",
                  end_state])
