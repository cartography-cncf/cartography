from cartography.intel.activedirectory import groups as groups_mod
from tests.data.activedirectory.sample_ldap_payloads import MOCK_GROUPS


def test_transform_groups_basic():
    out = groups_mod.transform(MOCK_GROUPS)
    assert len(out) == 1
    g = out[0]
    assert g["samaccountname"] == "Domain Admins"
    assert g["distinguishedname"].lower().startswith("cn=domain admins,")
    assert isinstance(g["member_dns"], list) and len(g["member_dns"]) == 1

