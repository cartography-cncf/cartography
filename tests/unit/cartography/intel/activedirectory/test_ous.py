from cartography.intel.activedirectory import ous as ous_mod
from tests.data.activedirectory.sample_ldap_payloads import MOCK_OUS


def test_transform_ous_basic():
    out = ous_mod.transform(MOCK_OUS)
    assert len(out) == 1
    ou = out[0]
    assert ou["name"] == "Engineering"
    assert ou["distinguishedname"].lower().startswith("ou=engineering,")
    assert ou["parent_dn"].lower().endswith("dc=example,dc=com")

