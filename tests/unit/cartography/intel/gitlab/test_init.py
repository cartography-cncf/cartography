from types import SimpleNamespace

import pytest
import requests

from cartography.intel.gitlab import start_gitlab_ingestion


def test_start_gitlab_ingestion_raises_http_error_when_org_not_found(monkeypatch):
    response = SimpleNamespace(status_code=404)
    error = requests.exceptions.HTTPError("not found", response=response)

    def _raise_get_single(*args, **kwargs):
        raise error

    monkeypatch.setattr(
        "cartography.intel.gitlab.organizations.get_single",
        _raise_get_single,
    )
    # These should not run because org sync fails first.
    monkeypatch.setattr(
        "cartography.intel.gitlab.groups.sync_gitlab_groups",
        lambda *args, **kwargs: pytest.fail("groups sync should not execute"),
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.projects.sync_gitlab_projects",
        lambda *args, **kwargs: pytest.fail("projects sync should not execute"),
    )

    config = SimpleNamespace(
        gitlab_token="token",
        gitlab_organization_id=3332,
        gitlab_url="https://gitlab.example.com",
        update_tag=123456,
    )

    with pytest.raises(requests.exceptions.HTTPError):
        start_gitlab_ingestion(neo4j_session=object(), config=config)
