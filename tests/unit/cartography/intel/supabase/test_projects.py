from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.supabase.projects as projects
import tests.data.supabase.projects as fixtures


def test_merge_project_prefers_org_scoped_identity():
    """
    Membership and identity come from the organization-scoped entry; only the
    database object is taken from the enrichment listing.
    """
    org_project = fixtures.SUPABASE_ORG_PROJECTS["projects"][0]
    enrichment = fixtures.SUPABASE_PROJECTS[0]

    merged = projects.merge_project(org_project, "simpson-corp", enrichment)

    assert merged["ref"] == "nuclearplantdbaaaaaa"
    assert merged["organization_slug"] == "simpson-corp"
    assert merged["database"]["host"] == "db.nuclearplantdbaaaaaa.supabase.co"
    assert merged["created_at"] == enrichment["created_at"]


def test_merge_project_without_enrichment_has_no_database():
    """
    A project created by another organization member is absent from /v1/projects, so
    it has no database object. It must still produce a project record, falling back
    to the org-scoped inserted_at, rather than being dropped.
    """
    org_project = fixtures.SUPABASE_ORG_PROJECTS["projects"][2]

    merged = projects.merge_project(org_project, "simpson-corp", None)

    assert merged["ref"] == "sharedprojectdddddddd"
    assert merged["name"] == "shared-by-a-colleague"
    assert merged["organization_slug"] == "simpson-corp"
    assert merged["database"] is None
    assert merged["created_at"] == org_project["inserted_at"]
    # transform_database() declines to invent a database node for it.
    assert projects.transform_database(merged, {}) == []


def _page(refs, limit=100):
    return {
        "projects": [
            {"ref": r, "name": r, "region": "us-east-2", "status": "ACTIVE_HEALTHY"}
            for r in refs
        ],
        "pagination": {"limit": limit},
    }


def test_get_org_projects_follows_pagination():
    """
    The organization-scoped listing is offset-paginated with a default limit of 100.
    Truncating it would look exactly like the projects having been deleted, which the
    cascading cleanup would then act on, so every page must be fetched.
    """
    first = _page([f"ref{i:04d}" for i in range(100)])
    second = _page(["reflast"])

    with patch.object(projects, "get_json", side_effect=[first, second]) as mock_get:
        result = projects.get_org_projects(
            MagicMock(), "https://api.fake", "simpson-corp"
        )

    assert [p["ref"] for p in result][-1] == "reflast"
    assert len(result) == 101
    urls = [call.args[1] for call in mock_get.call_args_list]
    assert "offset=0&limit=100" in urls[0]
    assert "offset=100&limit=100" in urls[1]


def test_get_org_projects_single_short_page_stops():
    with patch.object(
        projects, "get_json", return_value=fixtures.SUPABASE_ORG_PROJECTS
    ) as mock_get:
        result = projects.get_org_projects(
            MagicMock(), "https://api.fake", "simpson-corp"
        )

    assert len(result) == 3
    assert mock_get.call_count == 1


def test_get_org_projects_handles_empty_organization():
    with patch.object(
        projects, "get_json", return_value={"projects": [], "pagination": {}}
    ):
        assert (
            projects.get_org_projects(MagicMock(), "https://api.fake", "empty-org")
            == []
        )


def test_database_exposure_empty_allowlist_is_unrestricted():
    # The Management API treats an empty or absent list as no restriction at all.
    assert projects._database_exposure({}) == {
        "exposed_internet": True,
        "exposed_internet_type": ["direct"],
    }
    assert (
        projects._database_exposure({"dbAllowedCidrs": []})["exposed_internet"] is True
    )


def test_database_exposure_scoped_allowlist_is_not_exposed():
    config = {
        "dbAllowedCidrs": ["10.0.0.0/8"],
        "dbAllowedCidrsV6": ["2600:1f18::/48"],
    }
    assert projects._database_exposure(config) == {
        "exposed_internet": False,
        "exposed_internet_type": None,
    }


def test_database_exposure_explicit_open_cidr_is_exposed():
    assert (
        projects._database_exposure({"dbAllowedCidrs": ["10.0.0.0/8", "0.0.0.0/0"]})[
            "exposed_internet"
        ]
        is True
    )
    assert (
        projects._database_exposure(
            {"dbAllowedCidrs": ["10.0.0.0/8"], "dbAllowedCidrsV6": ["::/0"]}
        )["exposed_internet"]
        is True
    )
