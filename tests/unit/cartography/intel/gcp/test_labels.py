from cartography.intel.gcp.labels import get_labels


def test_get_labels_instance_uses_partial_uri():
    """
    Verify that get_labels uses the explicit id_field ("partial_uri") for instances,
    not "id" which doesn't exist in transformed instance dicts.
    """
    resources = [
        {
            "partial_uri": "projects/my-project/zones/us-east1-b/instances/my-instance",
            "labels": {"env": "dev"},
        },
    ]
    labels = get_labels(resources, "gcp_instance")
    assert len(labels) == 1
    assert (
        labels[0]["id"]
        == "projects/my-project/zones/us-east1-b/instances/my-instance:env:dev"
    )
    assert (
        labels[0]["resource_id"]
        == "projects/my-project/zones/us-east1-b/instances/my-instance"
    )


def test_get_labels_skips_resources_without_id_field():
    """
    Verify that resources missing the id_field are silently skipped.
    """
    resources = [
        {"name": "no-id-here", "labels": {"env": "prod"}},
    ]
    labels = get_labels(resources, "gcp_bucket")
    assert labels == []


def test_get_labels_unknown_resource_type():
    """
    Verify that an unknown resource type returns empty list.
    """
    labels = get_labels([{"id": "x", "labels": {"a": "b"}}], "unknown_type")
    assert labels == []


def test_get_labels_cloud_sql_uses_nested_user_labels_and_self_link_id():
    """
    Verify Cloud SQL labels resolve from settings.userLabels and use selfLink as resource_id.
    """
    resources = [
        {
            "selfLink": "https://sqladmin.googleapis.com/sql/v1beta4/projects/p/instances/i",
            "settings": {"userLabels": {"owner": "sec"}},
        },
    ]
    labels = get_labels(resources, "gcp_cloud_sql_instance")
    assert len(labels) == 1
    assert (
        labels[0]["id"]
        == "https://sqladmin.googleapis.com/sql/v1beta4/projects/p/instances/i:owner:sec"
    )
    assert (
        labels[0]["resource_id"]
        == "https://sqladmin.googleapis.com/sql/v1beta4/projects/p/instances/i"
    )
