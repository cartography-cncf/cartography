from copy import deepcopy
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.cloudflare import dnsrecords
from tests.data.cloudflare.access import DNS_RECORDS


def test_sync_returns_slim_proxied_inventory_after_loading_each_zone():
    # Arrange
    records = deepcopy(DNS_RECORDS)
    # A proxied non-hostname record must still be excluded by type.
    records.append(
        {
            "id": "proxied-txt",
            "name": "txt.example.com",
            "type": "TXT",
            "proxied": True,
            "zone_id": "zone",
        }
    )
    zones = [
        {"id": "zone"},
        {"id": "child-zone"},
        {"id": "net-zone"},
        {"id": "empty-zone"},
    ]
    records_by_zone = {
        zone["id"]: [record for record in records if record["zone_id"] == zone["id"]]
        for zone in zones
    }
    client = MagicMock()
    session = MagicMock()
    parameters = {"UPDATE_TAG": 1, "account_id": "account"}
    with (
        patch.object(
            dnsrecords,
            "get",
            side_effect=lambda _client, zone_id: records_by_zone[zone_id],
        ) as get,
        patch.object(dnsrecords, "load_dnsrecords") as load,
        patch.object(dnsrecords, "cleanup") as cleanup,
    ):
        # Act
        result = dnsrecords.sync(session, client, parameters, "account", zones)

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
    assert get.call_args_list == [
        call(client, "zone"),
        call(client, "child-zone"),
        call(client, "net-zone"),
        call(client, "empty-zone"),
    ]
    assert load.call_args_list == [
        call(session, records_by_zone["zone"], "account", "zone", 1),
        call(session, records_by_zone["child-zone"], "account", "child-zone", 1),
        call(session, records_by_zone["net-zone"], "account", "net-zone", 1),
        call(session, [], "account", "empty-zone", 1),
    ]
    cleanup.assert_called_once_with(session, parameters)
    assert records[:-1] == DNS_RECORDS
