from importlib.metadata import PackageNotFoundError

from cartography.version import get_cartography_version


def test_get_cartography_version_delegates_to_release_function(monkeypatch):
    def fake_release_and_commit() -> tuple[str, str]:
        return "9.9.9", "abc123"

    monkeypatch.setattr(
        "cartography.version.get_release_version_and_commit_revision",
        fake_release_and_commit,
    )

    assert get_cartography_version() == "9.9.9"


def test_get_cartography_version_returns_dev_when_package_metadata_missing(
    monkeypatch, caplog
):
    def raise_package_not_found(_name: str) -> str:
        raise PackageNotFoundError

    monkeypatch.setattr("cartography.version.version", raise_package_not_found)

    with caplog.at_level("WARNING"):
        result = get_cartography_version()

    assert result == "dev"
    assert "cartography package not found. Returning 'dev' version." in caplog.text
