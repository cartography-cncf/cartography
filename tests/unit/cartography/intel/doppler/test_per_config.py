from unittest.mock import Mock

import requests

import cartography.intel.doppler.secrets as secrets

CONFIGS = [
    {"project": "backend", "config": "dev", "config_id": "backend/dev"},
    {"project": "backend", "config": "prd", "config_id": "backend/prd"},
]


def _ok(body):
    resp = Mock()
    resp.raise_for_status = Mock()
    resp.json = Mock(return_value=body)
    return resp


def _fail():
    resp = Mock()
    resp.raise_for_status = Mock(side_effect=requests.exceptions.HTTPError("404"))
    return resp


def test_get_complete_when_a_config_succeeds():
    session = Mock()
    session.get = Mock(side_effect=[_ok({"names": ["DB_URL"]}), _fail()])
    items, complete = secrets.get(session, "http://x", CONFIGS)
    # One config succeeded -> trustworthy enough to clean up stale secrets.
    assert complete is True
    assert items == [
        {
            "id": "backend/dev/DB_URL",
            "name": "DB_URL",
            "project": "backend",
            "config": "dev",
            "config_id": "backend/dev",
        }
    ]


def test_get_incomplete_when_all_configs_fail():
    session = Mock()
    session.get = Mock(side_effect=[_fail(), _fail()])
    items, complete = secrets.get(session, "http://x", CONFIGS)
    # Every config failed -> [] is "couldn't see them", cleanup must be skipped.
    assert items == []
    assert complete is False


def test_get_complete_when_no_configs():
    # No configs at all is a legitimate empty result; cleanup should still run.
    items, complete = secrets.get(Mock(), "http://x", [])
    assert items == []
    assert complete is True
