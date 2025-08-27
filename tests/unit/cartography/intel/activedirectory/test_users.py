from cartography.intel.activedirectory import users as users_mod
from tests.data.activedirectory.sample_ldap_payloads import MOCK_USERS


def test_transform_users_basic():
    out = users_mod.transform(MOCK_USERS)
    assert len(out) == 1
    u = out[0]
    assert u["samaccountname"] == "alice"
    assert u["userprincipalname"] == "alice@example.com"
    assert u["distinguishedname"].lower().startswith("cn=alice,")
    assert isinstance(u["memberof_dns"], list) and len(u["memberof_dns"]) == 1

