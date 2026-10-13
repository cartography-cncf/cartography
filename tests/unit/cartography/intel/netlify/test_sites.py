import pytest

import tests.data.netlify.sites
from cartography.intel.netlify.sites import transform_netlify_sites

TEST_SITE_ID = "11111111-2222-3333-4444-555555555555"
TEST_GIT_SITE_ID = "99999999-8888-7777-6666-555555555555"

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


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        pytest.param({}, (True, ["direct"]), id="no_gate"),
        pytest.param({"ssl_url": None, "url": None}, (False, None), id="no_url"),
        pytest.param({"disabled": True}, (False, None), id="disabled"),
        pytest.param(
            {"has_password": True, "password_context": "all"},
            (False, None),
            id="password_all",
        ),
        pytest.param(
            {"sso_login": True, "sso_login_context": "all"},
            (False, None),
            id="sso_all",
        ),
        pytest.param(
            {"account_sso_login": True, "account_sso_login_context": "all"},
            (False, None),
            id="account_sso_all",
        ),
        # The team-level gate is read like the other two rather than assumed
        # unconditional. Treating any account_sso_login as covering the whole site
        # hid the public production URL of a team that only required SSO on previews.
        pytest.param(
            {
                "account_sso_login": True,
                "account_sso_login_context": "deploy-preview",
            },
            (True, ["direct"]),
            id="account_sso_deploy_preview",
        ),
        # No context at all does not count either, for the same reason.
        pytest.param(
            {"account_sso_login": True},
            (True, ["direct"]),
            id="account_sso_no_context",
        ),
        # A password on deploy previews only does not protect the production URL.
        # Reporting such a site as not exposed would hide a real attack surface, so
        # a gate is only honoured when its context is `all`.
        pytest.param(
            {"has_password": True, "password_context": "deploy-preview"},
            (True, ["direct"]),
            id="password_deploy_preview",
        ),
        pytest.param(
            {"sso_login": True, "sso_login_context": "branch-deploy"},
            (True, ["direct"]),
            id="sso_branch_deploy",
        ),
    ],
)
def test_site_exposure(overrides, expected):
    # Act
    actual = _exposure(**overrides)

    # Assert
    assert actual == expected


def test_transform_netlify_sites_drops_the_jwt_secret() -> None:
    """
    `jwt_secret` signs Netlify Identity tokens, so only its presence may be ingested.
    """
    # Act
    transformed = transform_netlify_sites(
        tests.data.netlify.sites.NETLIFY_SITES_WITH_GIT,
    )
    by_id = {site["id"]: site for site in transformed}

    # Assert
    assert by_id[TEST_GIT_SITE_ID]["has_jwt_secret"] is True
    assert by_id[TEST_SITE_ID]["has_jwt_secret"] is False
