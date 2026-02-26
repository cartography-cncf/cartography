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

    config = SimpleNamespace(
        gitlab_token="token",
        gitlab_organization_id=3332,
        gitlab_url="https://gitlab.example.com",
        update_tag=123456,
    )

    with pytest.raises(requests.exceptions.HTTPError):
        start_gitlab_ingestion(neo4j_session=object(), config=config)
