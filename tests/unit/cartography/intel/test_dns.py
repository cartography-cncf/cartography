from unittest.mock import patch

import pytest

import cartography.intel.dns
from tests.data.dns import RESOLVED_IPS


@patch.object(cartography.intel.dns, "get_dns_record_type", return_value="A")
@patch.object(
    cartography.intel.dns, "get_dns_resolution_by_fqdn", return_value=RESOLVED_IPS
)
def test_resolve_a_record_returns_addresses(mock_resolve, mock_type):
    assert cartography.intel.dns.resolve_a_record("search.example.com") == RESOLVED_IPS


@patch.object(cartography.intel.dns, "get_dns_record_type", return_value="AAAA")
@patch.object(
    cartography.intel.dns, "get_dns_resolution_by_fqdn", return_value=RESOLVED_IPS
)
def test_resolve_a_record_rejects_other_record_types(mock_resolve, mock_type):
    with pytest.raises(NotImplementedError):
        cartography.intel.dns.resolve_a_record("search.example.com")
