from unittest.mock import MagicMock

from cartography.intel.github import container_images


def test_get_container_images_records_cached_package_link(monkeypatch):
    digest = "sha256:cached"
    monkeypatch.setattr(
        container_images,
        "get_package_versions",
        MagicMock(
            return_value=[
                {
                    "name": digest,
                    "metadata": {"container": {"tags": []}},
                },
            ],
        ),
    )
    manifest_fetch = MagicMock()
    monkeypatch.setattr(container_images, "fetch_ghcr_manifest", manifest_fetch)

    manifests, manifest_lists, tags, skipped, links = (
        container_images.get_container_images(
            token="token",
            api_url="https://api.github.com",
            organization="example",
            packages=[
                {
                    "name": "package",
                    "html_url": "https://github.com/orgs/example/packages/container/package",
                    "uri": "ghcr.io/example/package",
                },
            ],
            skip_digests={digest},
        )
    )

    assert manifests == []
    assert manifest_lists == []
    assert tags == []
    assert skipped == {digest}
    assert links == [
        {
            "package_id": "https://github.com/orgs/example/packages/container/package",
            "digest": digest,
        },
    ]
    manifest_fetch.assert_not_called()


def test_refresh_skipped_package_links_scopes_observed_pairs(monkeypatch):
    run_write_query = MagicMock()
    monkeypatch.setattr(container_images, "run_write_query", run_write_query)
    links = [{"package_id": "package-1", "digest": "sha256:cached"}]

    container_images.refresh_skipped_package_image_links(
        MagicMock(),
        "https://github.com/example",
        links,
        123,
    )

    query = run_write_query.call_args.args[1]
    assert "MERGE (package)-[relationship:HAS_IMAGE]->(image)" in query
    assert run_write_query.call_args.kwargs == {
        "links": links,
        "org_url": "https://github.com/example",
        "update_tag": 123,
    }
