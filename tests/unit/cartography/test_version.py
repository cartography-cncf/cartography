from unittest.mock import patch

from cartography.version import get_commit_hash
from cartography.version import get_version
from cartography.version import get_version_string


class TestGetVersion:
    def test_get_version_returns_package_version(self):
        with patch('cartography.version.version', return_value='1.2.3'):
            assert get_version() == '1.2.3'

    def test_get_version_returns_dev_when_not_installed(self):
        from importlib.metadata import PackageNotFoundError
        with patch('cartography.version.version', side_effect=PackageNotFoundError):
            assert get_version() == 'dev'


class TestGetCommitHash:
    def test_get_commit_hash_returns_hash(self):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = 'abc1234\n'
            assert get_commit_hash() == 'abc1234'

    def test_get_commit_hash_returns_none_when_git_unavailable(self):
        with patch('subprocess.run', side_effect=FileNotFoundError):
            assert get_commit_hash() is None

    def test_get_commit_hash_returns_none_on_non_zero_exit(self):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 128
            assert get_commit_hash() is None


class TestGetVersionString:
    def test_version_string_with_commit(self):
        with (
            patch('cartography.version.get_version', return_value='1.2.3'),
            patch('cartography.version.get_commit_hash', return_value='abc1234'),
        ):
            assert get_version_string() == 'cartography, version 1.2.3 (commit: abc1234)'

    def test_version_string_without_commit(self):
        with (
            patch('cartography.version.get_version', return_value='1.2.3'),
            patch('cartography.version.get_commit_hash', return_value=None),
        ):
            assert get_version_string() == 'cartography, version 1.2.3'
