from cartography.intel.dns_utils import normalize_hostname
from cartography.intel.dns_utils import normalize_hostname_values


def test_normalize_hostname():
    assert normalize_hostname(" WWW.Example.COM. ") == "www.example.com"
    assert normalize_hostname(".") is None
    assert normalize_hostname(None) is None


def test_normalize_hostname_values_omits_empty_values():
    assert normalize_hostname_values([" First.Example.COM. ", ".", "second.test"]) == [
        "first.example.com",
        "second.test",
    ]
