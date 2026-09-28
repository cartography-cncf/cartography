import pytest

from cartography.intel.vercel.deployments import transform

NO_PROTECTION: dict = {
    "sso_protection_deployment_type": None,
    "password_protection_deployment_type": None,
}


def _exposed(target="production", state="READY", url="app.vercel.app", **protection):
    deployment = {"uid": "dpl_1", "state": state, "url": url, "target": target}
    transform([deployment], {**NO_PROTECTION, **protection})
    return deployment["exposed_internet"]


def test_ready_unprotected_deployment_is_exposed():
    assert _exposed() is True
    assert _exposed(target="preview") is True


def test_deployment_not_ready_is_not_exposed():
    assert _exposed(state="BUILDING") is False
    assert _exposed(state="ERROR") is False


def test_deployment_without_url_is_not_exposed():
    assert _exposed(url=None) is False


def test_trusted_sources_does_not_hide_a_public_deployment():
    """trustedSources is an OIDC authentication path, not an access restriction.

    It lets already-protected deployments accept short-lived tokens instead of long-lived
    secrets, so a project configuring it without SSO or password protection is still public.
    Treating it as a gate would drop such a project out of the exposure inventory.
    """
    assert _exposed(trustedSources={"oidcProviders": {"acme": []}}) is True
    assert (
        _exposed(target="preview", trustedSources={"projects": {"prj_x": {}}}) is True
    )


def test_unknown_deployment_type_errs_towards_exposed():
    assert _exposed(sso_protection_deployment_type="some_future_value") is True


@pytest.mark.parametrize("method", ["sso", "password"])
def test_all_covers_production_and_preview(method):
    key = f"{'sso' if method == 'sso' else 'password'}_protection_deployment_type"
    assert _exposed(**{key: "all"}) is False
    assert _exposed(target="preview", **{key: "all"}) is False


@pytest.mark.parametrize("method", ["sso", "password"])
def test_preview_only_leaves_production_exposed(method):
    key = f"{method}_protection_deployment_type"
    assert _exposed(**{key: "preview"}) is True
    assert _exposed(target="preview", **{key: "preview"}) is False


@pytest.mark.parametrize("method", ["sso", "password"])
def test_prod_deployment_urls_covers_the_generated_url(method):
    """VercelDeployment.url is the generated deployment URL, which this setting does cover.

    A production custom domain would stay public under this setting, but that is an alias
    rather than the deployment URL modelled here.
    """
    key = f"{method}_protection_deployment_type"
    assert _exposed(**{key: "prod_deployment_urls_and_all_previews"}) is False
    assert (
        _exposed(target="preview", **{key: "prod_deployment_urls_and_all_previews"})
        is False
    )
