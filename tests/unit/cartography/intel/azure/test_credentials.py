from cartography.intel.azure.util.credentials import Credentials


class DummyWithToken:
    token = {"tenant_id": "token-tenant"}


class DummyNoToken:
    pass


def test_get_tenant_id_from_token():
    cred = Credentials(DummyWithToken(), DummyWithToken())
    assert cred.get_tenant_id() == "token-tenant"


def test_get_tenant_id_without_token():
    cred = Credentials(DummyNoToken(), DummyNoToken(), tenant_id="fallback-tenant")
    assert cred.get_tenant_id() == "fallback-tenant"
