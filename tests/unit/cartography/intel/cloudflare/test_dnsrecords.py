from copy import deepcopy
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.cloudflare import dnsrecords
from tests.data.cloudflare.access import DNS_RECORDS


def test_sync_returns_slim_proxied_inventory_after_loading_each_zone():
    # Arrange
    records = deepcopy(DNS_RECORDS)
    # A proxied non-hostname record must still be excluded by type.
    records.append(
        {"id": "proxied-txt", "name": "txt.example.com", "type": "TXT", "proxied": True}
    )
    zones = [{"id": "zone"}, {"id": "empty-zone"}]
    session = MagicMock()
    parameters = {"UPDATE_TAG": 1, "account_id": "account"}
    with (
        patch.object(dnsrecords, "get", side_effect=[records, []]) as get,
        patch.object(dnsrecords, "load_dnsrecords") as load,
        patch.object(dnsrecords, "cleanup") as cleanup,
    ):
        # Act
        result = dnsrecords.sync(session, MagicMock(), parameters, "account", zones)

    # Assert
    assert result == [
        {"id": "dashboard", "name": "dashboard.example.com"},
        {"id": "ipv6", "name": "ipv6.example.com"},
        {"id": "alias", "name": "alias.example.com"},
        {"id": "apex", "name": "example.com"},
        {"id": "deep", "name": "two.deep.example.com"},
        {"id": "wildcard", "name": "*.example.com"},
        {"id": "child", "name": "a.child.example.com"},
        {"id": "net", "name": "a.example.net"},
    ]
    assert len(get.call_args_list) == 2
    assert load.call_args_list[0].args == (session, records, "account", "zone", 1)
    assert load.call_args_list[1].args == (session, [], "account", "empty-zone", 1)
    cleanup.assert_called_once_with(session, parameters)
    assert records[:-1] == DNS_RECORDS
