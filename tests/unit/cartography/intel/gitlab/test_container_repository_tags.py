from unittest.mock import Mock

from cartography.intel.gitlab.container_repository_tags import group_tags_by_repository
from cartography.intel.gitlab.container_repository_tags import (
    sync_container_repository_tags,
)


def test_group_tags_by_repository_groups_and_drops_unattributed_tags():
    # Arrange
    tags = [
        {"name": "latest", "_repository_location": "reg.example.com/group/app"},
        {"name": "v1.0.0", "_repository_location": "reg.example.com/group/app"},
        {"name": "v0.9.0", "_repository_location": "reg.example.com/group/worker"},
        {"name": "orphan"},
    ]

    # Act
    grouped = group_tags_by_repository(tags)

    # Assert
    assert grouped == {
        "reg.example.com/group/app": [tags[0], tags[1]],
        "reg.example.com/group/worker": [tags[2]],
    }


def test_sync_container_repository_tags_reuses_prefetched_tags(monkeypatch):
    # Arrange: the caller already paid for the per-tag detail requests, so the
    # tag sync must not fetch them a second time.
    fetch_tags = Mock()
    transform = Mock(return_value=[])
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_repository_tags.get_all_container_repository_tags",
        fetch_tags,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_repository_tags.transform_container_repository_tags",
        transform,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_repository_tags.load_container_repository_tags",
        Mock(),
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_repository_tags.cleanup_container_repository_tags",
        Mock(),
    )
    raw_tags = [{"name": "latest", "_repository_location": "reg.example.com/group/app"}]

    # Act
    returned = sync_container_repository_tags(
        neo4j_session=Mock(),
        gitlab_url="https://gitlab.example.com",
        token="token",
        org_id=123,
        repositories=[{"id": 1, "project_id": 2}],
        update_tag=1,
        common_job_parameters={},
        raw_tags=raw_tags,
    )

    # Assert
    fetch_tags.assert_not_called()
    transform.assert_called_once_with(raw_tags)
    assert returned is raw_tags


def test_sync_container_repository_tags_fetches_when_not_prefetched(monkeypatch):
    # Arrange
    raw_tags = [{"name": "latest", "_repository_location": "reg.example.com/group/app"}]
    fetch_tags = Mock(return_value=raw_tags)
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_repository_tags.get_all_container_repository_tags",
        fetch_tags,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_repository_tags.transform_container_repository_tags",
        Mock(return_value=[]),
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_repository_tags.load_container_repository_tags",
        Mock(),
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_repository_tags.cleanup_container_repository_tags",
        Mock(),
    )

    # Act
    returned = sync_container_repository_tags(
        neo4j_session=Mock(),
        gitlab_url="https://gitlab.example.com",
        token="token",
        org_id=123,
        repositories=[{"id": 1, "project_id": 2}],
        update_tag=1,
        common_job_parameters={},
    )

    # Assert
    fetch_tags.assert_called_once()
    assert returned is raw_tags
