import os

import pytest

from cartography.driftdetect.cli import CLI
from cartography.driftdetect.serializers import ShortcutSchema
from cartography.driftdetect.storage import FileSystem


def test_basic_add_shortcuts():
    """
    Tests that the CLI can add shortcuts.
    """
    cli = CLI(prog="cartography-detectdrift")
    directory = "tests/data/test_cli_detectors/detector"
    alias = "test_shortcut"
    filename = "1.json"
    shortcut_path = directory + "/shortcut.json"
    cli.main(
        [
            "add-shortcut",
            "--query-directory",
            directory,
            "--shortcut",
            alias,
            "--file",
            filename,
        ],
    )
    shortcut_data = FileSystem.load(shortcut_path)
    shortcut = ShortcutSchema().load(shortcut_data)
    assert shortcut.shortcuts[alias] == filename
    shortcut.shortcuts.pop(alias)
    shortcut_data = ShortcutSchema().dump(shortcut)
    FileSystem.write(shortcut_data, shortcut_path)


def test_use_shortcuts_for_shortcuts():
    """
    Tests add_shortcut can parse shortcuts.
    """
    cli = CLI(prog="cartography-detectdrift")
    directory = "tests/data/test_cli_detectors/detector"
    alias = "test_shortcut"
    alias_2 = "test_shortcut_2"
    filename = "1.json"
    shortcut_path = directory + "/shortcut.json"
    cli.main(
        [
            "add-shortcut",
            "--query-directory",
            directory,
            "--shortcut",
            alias,
            "--file",
            filename,
        ],
    )
    cli.main(
        [
            "add-shortcut",
            "--query-directory",
            directory,
            "--shortcut",
            alias_2,
            "--file",
            alias,
        ],
    )
    shortcut_data = FileSystem.load(shortcut_path)
    shortcut = ShortcutSchema().load(shortcut_data)
    assert shortcut.shortcuts[alias] == filename
    assert shortcut.shortcuts[alias_2] == filename

    # Return shortcut back to its original state.
    shortcut.shortcuts.pop(alias)
    shortcut.shortcuts.pop(alias_2)
    shortcut_data = ShortcutSchema().dump(shortcut)
    FileSystem.write(shortcut_data, shortcut_path)


def test_shortcut_fails_when_shortcut_exists():
    """
    Tests add_shortcut fails when shortcuts exist.
    """
    cli = CLI(prog="cartography-detectdrift")
    directory = "tests/data/test_cli_detectors/detector"
    alias = "2.json"
    filename = "1.json"
    cli.main(
        [
            "add-shortcut",
            "--query-directory",
            directory,
            "--shortcut",
            alias,
            "--file",
            filename,
        ],
    )
    shortcut_path = directory + "/shortcut.json"
    shortcut_data = FileSystem.load(shortcut_path)
    shortcut = ShortcutSchema().load(shortcut_data)
    with pytest.raises(KeyError):
        shortcut.shortcuts[alias]


def test_nonexistent_shortcuts():
    cli = CLI(prog="cartography-detectdrift")
    directory = "tests/data/test_cli_detectors/detector"
    alias = "test_shortcut"
    filename = "3.json"
    shortcut_path = os.path.join(directory, "shortcut.json")
    cli.main(
        [
            "add-shortcut",
            "--query-directory",
            directory,
            "--shortcut",
            alias,
            "--file",
            filename,
        ],
    )
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
        cli.main(
            [
                "get-drift",
                "--query-directory",
                directory,
                "--start-state",
                start_state,
                "--end-state",
                end_state,
            ],
        )
