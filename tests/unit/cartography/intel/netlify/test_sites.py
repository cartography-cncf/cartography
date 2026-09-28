from cartography.intel.netlify.sites import transform_netlify_sites

_BASE = {
    "id": "site-1",
    "name": "site-1",
    "ssl_url": "https://site-1.netlify.app",
    "url": "http://site-1.netlify.app",
}


def _exposure(**overrides):
    site = {**_BASE, **overrides}
    transformed = transform_netlify_sites([site])[0]
    return transformed["exposed_internet"], transformed["exposed_internet_type"]


def test_served_site_with_no_gate_is_exposed():
    assert _exposure() == (True, ["direct"])


def test_site_with_no_url_is_not_exposed():
    assert _exposure(ssl_url=None, url=None) == (False, None)


def test_disabled_site_is_not_exposed():
    assert _exposure(disabled=True) == (False, None)


def test_unconditional_password_gates_the_site():
    assert _exposure(has_password=True, password_context="all") == (False, None)


def test_unconditional_sso_gates_the_site():
    assert _exposure(sso_login=True, sso_login_context="all") == (False, None)


def test_account_level_sso_gates_the_site():
    assert _exposure(account_sso_login=True, account_sso_login_context="all") == (
        False,
        None,
    )


def test_context_scoped_account_sso_leaves_production_exposed():
    """The team-level gate is read like the other two rather than assumed unconditional.

    Treating any account_sso_login as covering the whole site hid the public production URL
    of a team that only required SSO on previews.
    """
    assert _exposure(
        account_sso_login=True, account_sso_login_context="deploy-preview"
    ) == (True, ["direct"])
    # No context at all does not count either, for the same reason.
    assert _exposure(account_sso_login=True) == (True, ["direct"])


def test_context_scoped_gate_leaves_production_exposed():
    """A password on deploy previews only does not protect the production URL.

    Reporting such a site as not exposed would hide a real attack surface, so a gate is only
    honoured when its context is `all`.
    """
    assert _exposure(has_password=True, password_context="deploy-preview") == (
        True,
        ["direct"],
    )
    assert _exposure(sso_login=True, sso_login_context="branch-deploy") == (
        True,
        ["direct"],
    )
