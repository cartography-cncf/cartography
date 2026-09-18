import pytest

from cartography.intel.infisical.projects import transform
from tests.data.infisical import PROJECTS


def test_transform_selects_stable_project_metadata() -> None:
    # Act
    result = transform(PROJECTS)

    # Assert
    assert result == [
        {"id": "project-1", "name": "Payments", "slug": "payments"},
        {
            "id": "project-2",
            "name": "Data Platform",
            "slug": "data-platform",
        },
    ]


def test_transform_requires_project_id() -> None:
    # Arrange
    project = {**PROJECTS[0]}
    project.pop("id")

    # Act and assert
    with pytest.raises(KeyError, match="id"):
        transform([project])
