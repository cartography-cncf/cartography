from unittest.mock import MagicMock

import httpx

from cartography.intel.scaleway.container_registry import supply_chain


def test_sync_skips_config_but_rechecks_attestation_for_complete_digest(monkeypatch):
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
    assert get.call_args.kwargs["images_to_enrich"] == [
        {
            "digest": digest,
            "project_id": project_id,
            "uri": "rg.fr-par.scw.cloud/ns/image:latest",
        },
    ]
    assert get.call_args.kwargs["cached_layer_keys"] == {(project_id, digest)}
    refresh.assert_called_once_with(
        get.call_args.args[0],
        supply_chain.SCALEWAY_LAYER_GRAPH,
        {digest},
        {"id": project_id},
        2,
    )


def test_cached_layers_still_retry_failed_attestation(monkeypatch):
    manifest = {
        "manifests": [
            {
                "digest": "sha256:attestation",
                "annotations": {
                    "vnd.docker.reference.type": "attestation-manifest",
                },
            },
            {
                "digest": "sha256:platform",
                "platform": {"os": "linux", "architecture": "amd64"},
            },
        ],
    }
    monkeypatch.setattr(supply_chain, "_registry_token", MagicMock(return_value="t"))
    get_json = MagicMock(return_value=manifest)
    monkeypatch.setattr(supply_chain, "_get_json", get_json)
    monkeypatch.setattr(
        supply_chain,
        "_fetch_attestation_predicate",
        MagicMock(side_effect=httpx.HTTPError("temporary failure")),
    )
    monkeypatch.setattr(supply_chain.httpx, "Client", MagicMock())

    config, annotations, predicate, attestation_failed = (
        supply_chain.fetch_image_supply_chain(
            "rg.fr-par.scw.cloud",
            "fr-par",
            "ns/image",
            "sha256:image",
            "secret",
            fetch_config=False,
        )
    )

    assert config is None
    assert annotations == {}
    assert predicate is None
    assert attestation_failed is True
    assert get_json.call_count == 1


def test_transform_supports_attestation_only_update():
    images_by_project, layers_by_project = supply_chain.transform(
        [
            {
                "digest": "sha256:image",
                "project_id": "project-1",
                "config": None,
                "annotations": {},
                "attestation_predicate": {
                    "buildDefinition": {
                        "externalParameters": {
                            "source": "https://github.com/example/repository.git",
                        },
                    },
                },
            },
        ],
    )

    assert images_by_project == {
        "project-1": [
            {
                "digest": "sha256:image",
                "source_uri": "https://github.com/example/repository",
                "source_file": "Dockerfile",
            },
        ],
    }
    assert layers_by_project == {}
