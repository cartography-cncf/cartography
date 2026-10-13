import cartography.intel.netlify.deploys
import tests.data.netlify.sites

_DEPLOY_ID = "6b6b7982e9b39032db65efe0"


def test_deploys_skip_sites_with_no_published_deploy() -> None:
    """
    A site that has never had a successful production deploy carries `published_deploy: None`.
    Emitting a row for it would create a NetlifyDeploy with a null id.
    """
    # Act
    deploys = cartography.intel.netlify.deploys.transform_netlify_deploys(
        tests.data.netlify.sites.NETLIFY_SITES_WITH_GIT,
    )

    # Assert
    assert [d["id"] for d in deploys] == [_DEPLOY_ID]
