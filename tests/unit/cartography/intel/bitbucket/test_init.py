from types import SimpleNamespace
from unittest.mock import patch

from cartography.intel.bitbucket import start_bitbucket_ingestion


def _base_config(**overrides):
    defaults = dict(
        bitbucket_auth_method="token",
        bitbucket_token=None,
        bitbucket_oauth_client_id=None,
        bitbucket_oauth_client_secret=None,
        bitbucket_oauth_refresh_token=None,
        bitbucket_workspaces=None,
        update_tag=123456,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_start_bitbucket_ingestion_skips_when_unconfigured():
    config = _base_config()
    with patch(
        "cartography.intel.bitbucket.workspaces.sync_bitbucket_workspaces"
    ) as mock_sync:
        start_bitbucket_ingestion(neo4j_session=object(), config=config)
    mock_sync.assert_not_called()


def test_start_bitbucket_ingestion_skips_when_no_workspaces_configured():
    config = _base_config(bitbucket_token="fake-token")
    with patch(
        "cartography.intel.bitbucket.workspaces.sync_bitbucket_workspaces"
    ) as mock_sync:
        start_bitbucket_ingestion(neo4j_session=object(), config=config)
    mock_sync.assert_not_called()


def test_start_bitbucket_ingestion_runs_when_token_configured():
    config = _base_config(
        bitbucket_token="fake-token", bitbucket_workspaces="my-workspace"
    )

    with (
        patch(
            "cartography.intel.bitbucket.workspaces.sync_bitbucket_workspaces",
            return_value=[{"id": "workspace-1", "slug": "my-workspace"}],
        ) as mock_workspaces,
        patch(
            "cartography.intel.bitbucket.projects.sync_bitbucket_projects",
            return_value=[],
        ) as mock_projects,
        patch(
            "cartography.intel.bitbucket.repositories.sync_bitbucket_repositories",
            return_value=[],
        ) as mock_repos,
        patch(
            "cartography.intel.bitbucket.users.sync_bitbucket_users",
            return_value=set(),
        ) as mock_users,
        patch("cartography.intel.bitbucket.projects.cleanup_projects"),
        patch("cartography.intel.bitbucket.repositories.cleanup_repositories"),
        patch("cartography.intel.bitbucket.users.cleanup_users"),
    ):
        start_bitbucket_ingestion(neo4j_session=object(), config=config)

    mock_workspaces.assert_called_once()
    mock_projects.assert_called_once()
    mock_repos.assert_called_once()
    mock_users.assert_called_once()


def test_start_bitbucket_ingestion_ignores_empty_workspace_slugs():
    config = _base_config(
        bitbucket_token="fake-token", bitbucket_workspaces="ws-a, ,ws-b,"
    )

    with (
        patch(
            "cartography.intel.bitbucket.workspaces.sync_bitbucket_workspaces",
            return_value=[],
        ) as mock_workspaces,
        patch("cartography.intel.bitbucket.projects.sync_bitbucket_projects"),
        patch("cartography.intel.bitbucket.repositories.sync_bitbucket_repositories"),
        patch(
            "cartography.intel.bitbucket.users.sync_bitbucket_users",
            return_value=set(),
        ),
    ):
        start_bitbucket_ingestion(neo4j_session=object(), config=config)

    assert mock_workspaces.call_args.args[3] == ["ws-a", "ws-b"]


def test_start_bitbucket_ingestion_skips_all_user_cleanup_when_a_workspace_403s():
    config = _base_config(
        bitbucket_token="fake-token", bitbucket_workspaces="ws-a,ws-b"
    )

    with (
        patch(
            "cartography.intel.bitbucket.workspaces.sync_bitbucket_workspaces",
            return_value=[
                {"id": "workspace-a", "slug": "ws-a"},
                {"id": "workspace-b", "slug": "ws-b"},
            ],
        ),
        patch("cartography.intel.bitbucket.projects.sync_bitbucket_projects"),
        patch("cartography.intel.bitbucket.repositories.sync_bitbucket_repositories"),
        patch(
            "cartography.intel.bitbucket.users.sync_bitbucket_users",
            return_value={"workspace-b"},
        ),
        patch("cartography.intel.bitbucket.projects.cleanup_projects"),
        patch("cartography.intel.bitbucket.repositories.cleanup_repositories"),
        patch("cartography.intel.bitbucket.users.cleanup_users") as mock_cleanup,
    ):
        start_bitbucket_ingestion(neo4j_session=object(), config=config)

    mock_cleanup.assert_not_called()
