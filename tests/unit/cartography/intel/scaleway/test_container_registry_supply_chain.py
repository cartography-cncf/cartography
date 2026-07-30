from unittest.mock import MagicMock

from cartography.intel.scaleway.container_registry import supply_chain


def test_sync_skips_oci_pull_for_complete_digest(monkeypatch):
    # Arrange
    digest = "sha256:complete"
    project_id = "project-1"
    get = MagicMock(return_value=([], False))
    refresh = MagicMock()
    monkeypatch.setattr(
        supply_chain,
        "_get_images_to_enrich",
        MagicMock(
            return_value=[
                {
                    "digest": digest,
                    "project_id": project_id,
                    "uri": "rg.fr-par.scw.cloud/ns/image:latest",
                },
            ],
        ),
    )
    monkeypatch.setattr(
        supply_chain,
        "get_complete_layer_digests",
        MagicMock(return_value={digest}),
    )
    monkeypatch.setattr(supply_chain, "get", get)
    monkeypatch.setattr(supply_chain, "transform", MagicMock(return_value=({}, {})))
    monkeypatch.setattr(supply_chain, "load_supply_chain", MagicMock())
    monkeypatch.setattr(supply_chain, "refresh_layer_closures", refresh)
    monkeypatch.setattr(supply_chain, "cleanup", MagicMock())

    # Act
    supply_chain.sync(
        neo4j_session=MagicMock(),
        secret_key="secret",
        common_job_parameters={"UPDATE_TAG": 2},
        projects_id=[project_id],
        update_tag=2,
    )

    # Assert
    assert get.call_args.kwargs["images_to_enrich"] == []
    refresh.assert_called_once_with(
        get.call_args.args[0],
        supply_chain.SCALEWAY_LAYER_GRAPH,
        {digest},
        {"id": project_id},
        2,
    )
