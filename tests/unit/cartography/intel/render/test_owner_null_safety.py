"""
`instance.get("owner", {})` only supplies the default `{}` when the "owner" key is
absent. If the API ever returns "owner": null explicitly, that returns None, and
chaining `.get("id")` on None crashes with AttributeError. Every transform() that reads
a nested owner object must guard against an explicit null, not just a missing key.
"""

import pytest

from cartography.intel.render.postgres import transform as postgres_transform
from cartography.intel.render.projects import transform as projects_transform


def test_projects_transform_handles_explicit_null_owner():
    projects = [{"id": "prj-1", "name": "test", "owner": None}]

    rows = projects_transform(projects)

    assert rows[0]["ownerId"] is None


def test_postgres_transform_handles_explicit_null_owner():
    instances = [{"id": "dpg-1", "name": "test", "owner": None}]

    rows = postgres_transform(instances)

    assert rows[0]["ownerId"] is None


def test_projects_transform_raises_id_check_before_owner_lookup_regression_guard():
    # Sanity check that the fix didn't accidentally swallow other errors: a missing id
    # still raises via require_non_empty, independent of the owner fix.
    with pytest.raises(ValueError):
        projects_transform([{"name": "test", "owner": None}])
