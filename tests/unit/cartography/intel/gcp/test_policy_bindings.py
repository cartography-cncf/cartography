from cartography.intel.gcp.policy_bindings import _parse_full_resource_name


def test_parse_project():
    assert _parse_full_resource_name(
        "//cloudresourcemanager.googleapis.com/projects/project-abc",
    ) == ("GCPProject", "project-abc")


def test_parse_folder_keeps_type_prefix():
    # GCPFolder.id is "folders/{id}" (matches resourcemanager v3 `name` field).
    assert _parse_full_resource_name(
        "//cloudresourcemanager.googleapis.com/folders/1414",
    ) == ("GCPFolder", "folders/1414")


def test_parse_organization_keeps_type_prefix():
    # GCPOrganization.id is "organizations/{id}".
    assert _parse_full_resource_name(
        "//cloudresourcemanager.googleapis.com/organizations/1337",
    ) == ("GCPOrganization", "organizations/1337")


def test_parse_bucket():
    assert _parse_full_resource_name(
        "//storage.googleapis.com/buckets/test-bucket",
    ) == ("GCPBucket", "test-bucket")


def test_parse_bucket_subresource_resolves_to_owning_bucket():
    # Cloud Asset may return policies attached to sub-paths; we only link back
    # to the top-level resource present in the ontology.
    assert _parse_full_resource_name(
        "//storage.googleapis.com/buckets/test-bucket/objects/foo.txt",
    ) == ("GCPBucket", "test-bucket")


def test_parse_unknown_service_returns_none():
    assert _parse_full_resource_name(
        "//bigquery.googleapis.com/projects/p/datasets/d",
    ) == (None, None)


def test_parse_empty_suffix_returns_none():
    assert _parse_full_resource_name(
        "//cloudresourcemanager.googleapis.com/projects/",
    ) == (None, None)
