from unittest.mock import MagicMock

import pytest
from googleapiclient.errors import HttpError

from cartography.intel.gsuite.groups import get_members_for_groups


def _http_error(status: int) -> HttpError:
    resp = MagicMock()
    resp.status = status
    return HttpError(resp=resp, content=b'{"error": "Invalid Input"}')


def _admin_with_member_errors(error_by_group: dict[str, HttpError]) -> MagicMock:
    admin = MagicMock()

    def list_side_effect(groupKey: str, maxResults: int) -> MagicMock:
        # members.list documents 200 as the maximum; never send more.
        assert maxResults <= 200
        request = MagicMock()
        if groupKey in error_by_group:
            request.execute.side_effect = error_by_group[groupKey]
        else:
            request.execute.return_value = {"members": [{"id": "1", "type": "USER"}]}
        return request

    admin.members.return_value.list.side_effect = list_side_effect
    admin.members.return_value.list_next.return_value = None
    return admin


def test_get_members_uses_group_id_as_key():
    admin = _admin_with_member_errors({})

    results = get_members_for_groups(admin, ["grp-id-1", "grp-id-2"])

    admin.members.return_value.list.assert_any_call(groupKey="grp-id-1", maxResults=200)
    assert set(results) == {"grp-id-1", "grp-id-2"}


def test_get_members_skips_group_with_400():
    admin = _admin_with_member_errors({"grp-bad": _http_error(400)})

    results = get_members_for_groups(admin, ["grp-good", "grp-bad"])

    assert results["grp-bad"] == []
    assert len(results["grp-good"]) == 1


def test_get_members_reraises_non_400():
    admin = _admin_with_member_errors({"grp-bad": _http_error(403)})

    with pytest.raises(HttpError):
        get_members_for_groups(admin, ["grp-bad"])
