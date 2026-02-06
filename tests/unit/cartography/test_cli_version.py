import unittest.mock

import cartography.cli


def test_cli_version_flag(capsys):
    """Test that --version prints version info and exits cleanly."""
    cli = cartography.cli.CLI(unittest.mock.MagicMock(), "cartography")
    with unittest.mock.patch(
        'cartography.version.get_version_string',
        return_value='cartography, version 1.2.3 (commit: abc1234)',
    ):
        exit_code = cli.main(["--version"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "cartography, version 1.2.3 (commit: abc1234)" in captured.out


def test_cli_version_flag_does_not_run_sync():
    """Test that --version exits without running sync."""
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "cartography")
    with unittest.mock.patch(
        'cartography.version.get_version_string',
        return_value='cartography, version 1.2.3',
    ):
        cli.main(["--version"])
    sync.run.assert_not_called()
