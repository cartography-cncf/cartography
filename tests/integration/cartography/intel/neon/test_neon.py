"""
End-to-end tests for the Neon module.

Only the HTTP boundary is replaced: build_session() returns a fake session that
answers like the Neon API, so the real entry point, transforms, loads and
cleanups all run.
"""

from typing import Any
from unittest.mock import patch

import cartography.intel.neon
import tests.data.neon.neon_api as api
from cartography.config import Config
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
BASE_URL = "https://fake-neon.example.com/api/v2"


class FakeResponse:
    def __init__(self, status_code: int, body: Any = None) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> Any:
        return self._body

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeNeonSession:
    """Routes GET requests by path to canned payloads or status codes."""

    def __init__(self, routes: dict[str, Any]) -> None:
        self.routes = routes
        self.calls: list[str] = []

    def get(self, url: str, params: dict | None = None, timeout: Any = None):
        assert url.startswith(BASE_URL), url
        path = url[len(BASE_URL) :]
        self.calls.append(path)
        route = self.routes.get(path)
        if route is None:
            return FakeResponse(404, {"message": "not found"})
        if callable(route):
            route = route(params or {})
        if isinstance(route, int):
            return FakeResponse(route, {"message": "denied"})
        return FakeResponse(200, route)


def _members(params: dict) -> dict:
    if params.get("cursor") == "cursor-page-2":
        return api.MEMBERS_PAGE_2
    return api.MEMBERS_PAGE_1


def _routes(**overrides: Any) -> dict[str, Any]:
    org = api.ORG_ID
    plant = f"/projects/{api.PLANT_PROJECT_ID}"
    grid = f"/projects/{api.GRID_PROJECT_ID}"
    routes: dict[str, Any] = {
        "/users/me/organizations": api.ORGANIZATIONS,
        f"/organizations/{org}": api.ORGANIZATION,
        f"/organizations/{org}/members": _members,
        f"/organizations/{org}/api_keys": api.API_KEYS,
        "/projects": api.PROJECTS,
        f"{plant}/branches": api.PLANT_BRANCHES,
        f"{plant}/endpoints": api.PLANT_ENDPOINTS,
        f"{grid}/branches": api.GRID_BRANCHES,
        f"{grid}/endpoints": api.GRID_ENDPOINTS,
    }
    for project, branches in (
        (plant, [api.PLANT_MAIN, api.PLANT_PREVIEW, api.PLANT_HOTFIX]),
        (grid, [api.GRID_MAIN]),
    ):
        for branch in branches:
            prefix = f"{project}/branches/{branch}"
            routes[f"{prefix}/roles"] = api.roles_for(branch)
            routes[f"{prefix}/databases"] = api.databases_for(branch)
            routes[f"{prefix}/storage"] = api.storage_for(branch)
            if project == plant:
                routes[f"{prefix}/buckets"] = api.PLANT_BUCKETS
                routes[f"{prefix}/credentials"] = (
                    api.PLANT_MAIN_CREDENTIALS
                    if branch == api.PLANT_MAIN
                    else api.PLANT_DESCENDANT_CREDENTIALS
                )
            else:
                routes[f"{prefix}/buckets"] = api.EMPTY_BUCKETS
                routes[f"{prefix}/credentials"] = api.EMPTY_CREDENTIALS
    routes.update(overrides)
    return routes


def _run(neo4j_session, update_tag: int, routes: dict, org_ids: str | None = None):
    session = FakeNeonSession(routes)
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        neon_api_key="napi_fake",
        neon_base_url=BASE_URL,
        neon_org_ids=org_ids,
    )
    with patch.object(cartography.intel.neon, "build_session", return_value=session):
        cartography.intel.neon.start_neon_ingestion(neo4j_session, config)
    return session


def test_neon_full_sync(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    session = _run(neo4j_session, TEST_UPDATE_TAG, _routes())

    # Organization and members, across both pages of the members listing.
    assert check_nodes(neo4j_session, "NeonOrganization", ["id", "name"]) == {
        (api.ORG_ID, "Springfield Nuclear"),
    }
    assert check_nodes(
        neo4j_session,
        "NeonOrganizationMember",
        ["email", "role", "has_mfa"],
    ) == {
        ("mburns@example.com", "admin", True),
        ("hsimpson@example.com", "member", False),
    }

    # Projects carry the IP allowlist posture.
    projects = {
        r["id"]: (r["ips"], r["protected_only"])
        for r in neo4j_session.run(
            "MATCH (p:NeonProject) RETURN p.id AS id, p.allowed_ips AS ips, "
            "p.allowed_ips_protected_branches_only AS protected_only",
        )
    }
    assert projects == {
        api.PLANT_PROJECT_ID: (["203.0.113.0/24"], True),
        api.GRID_PROJECT_ID: (None, None),
    }
    assert check_rels(
        neo4j_session,
        "NeonOrganization",
        "id",
        "NeonProject",
        "id",
        "RESOURCE",
    ) == {(api.ORG_ID, api.PLANT_PROJECT_ID), (api.ORG_ID, api.GRID_PROJECT_ID)}

    # The API lists children before parents. Every BRANCHED_FROM edge must still
    # exist after a single sync.
    assert check_rels(
        neo4j_session,
        "NeonBranch",
        "id",
        "NeonBranch",
        "id",
        "BRANCHED_FROM",
    ) == {
        (api.PLANT_PREVIEW, api.PLANT_MAIN),
        (api.PLANT_HOTFIX, api.PLANT_PREVIEW),
    }

    # Main is protected so the allowlist applies. Preview is not protected, so
    # protected_branches_only leaves it open. Hotfix is disabled. Grid has no
    # allowlist at all.
    assert check_nodes(
        neo4j_session,
        "NeonEndpoint",
        ["id", "exposed_internet"],
    ) == {
        ("ep-plant-main", False),
        ("ep-plant-preview", True),
        ("ep-plant-hotfix", False),
        ("ep-grid-main", True),
    }
    assert check_rels(
        neo4j_session,
        "NeonEndpoint",
        "id",
        "NeonBranch",
        "id",
        "ATTACHED_TO",
    ) == {
        ("ep-plant-main", api.PLANT_MAIN),
        ("ep-plant-preview", api.PLANT_PREVIEW),
        ("ep-plant-hotfix", api.PLANT_HOTFIX),
        ("ep-grid-main", api.GRID_MAIN),
    }

    # Roles never carry the password the listing returned.
    leaked = neo4j_session.run(
        "MATCH (n) WHERE any(k IN keys(n) WHERE n[k] = $pw) RETURN count(n) AS c",
        pw=api.LEAKED_PASSWORD,
    ).single()["c"]
    assert leaked == 0
    assert check_nodes(neo4j_session, "NeonRole", ["id", "password"]) == {
        (f"{api.PLANT_MAIN}/neondb_owner", None),
        (f"{api.PLANT_PREVIEW}/neondb_owner", None),
        (f"{api.PLANT_HOTFIX}/neondb_owner", None),
        (f"{api.GRID_MAIN}/neondb_owner", None),
    }

    # Databases resolve their host from the branch's read-write compute, and are
    # owned by the branch's own copy of the owner role.
    assert (
        f"{api.PLANT_PREVIEW}/neondb",
        "ep-plant-preview.c-9.us-east-2.aws.neon.tech",
    ) in check_nodes(neo4j_session, "NeonDatabase", ["id", "host"])
    assert check_rels(
        neo4j_session,
        "NeonRole",
        "id",
        "NeonDatabase",
        "id",
        "OWNS",
    ) == {
        (f"{b}/neondb_owner", f"{b}/neondb")
        for b in (api.PLANT_MAIN, api.PLANT_PREVIEW, api.PLANT_HOTFIX, api.GRID_MAIN)
    }

    # One bucket node per branch, each addressed through its own branch endpoint.
    buckets = check_nodes(
        neo4j_session,
        "NeonStorageBucket",
        ["id", "public", "exposed_internet", "url"],
    )
    assert len(buckets) == 6
    assert (
        f"{api.PLANT_PREVIEW}/press-kit",
        True,
        True,
        f"https://{api.PLANT_PREVIEW}.storage.c-9.us-east-2.aws.neon.tech/press-kit",
    ) in buckets
    assert (
        f"{api.PLANT_MAIN}/reactor-telemetry",
        False,
        False,
        f"https://{api.PLANT_MAIN}.storage.c-9.us-east-2.aws.neon.tech/reactor-telemetry",
    ) in buckets
    assert (api.PLANT_HOTFIX, f"{api.PLANT_HOTFIX}/press-kit") in check_rels(
        neo4j_session,
        "NeonBranch",
        "id",
        "NeonStorageBucket",
        "id",
        "CONTAINS",
    )
    # A project with no buckets never asks for its storage endpoint.
    assert (
        f"/projects/{api.GRID_PROJECT_ID}/branches/{api.GRID_MAIN}/storage"
        not in session.calls
    )

    # Inherited credentials are listed on every descendant but stored once, on
    # the branch that issued them.
    assert check_nodes(
        neo4j_session,
        "NeonCredential",
        ["id", "can_write_storage"],
    ) == {
        ("nak_live_plant_main_rw", True),
        ("nak_live_plant_preview_ro", False),
    }
    assert check_rels(
        neo4j_session,
        "NeonCredential",
        "id",
        "NeonBranch",
        "id",
        "ISSUED_ON",
    ) == {
        ("nak_live_plant_main_rw", api.PLANT_MAIN),
        ("nak_live_plant_preview_ro", api.PLANT_PREVIEW),
    }

    # API keys link to their creator's membership and to their project scope.
    assert check_rels(
        neo4j_session,
        "NeonApiKey",
        "name",
        "NeonOrganizationMember",
        "email",
        "OWNED_BY",
    ) == {
        ("ci-deploy", "mburns@example.com"),
        ("plant-only", "hsimpson@example.com"),
    }
    assert check_rels(
        neo4j_session,
        "NeonApiKey",
        "name",
        "NeonProject",
        "id",
        "SCOPED_TO",
    ) == {("plant-only", api.PLANT_PROJECT_ID)}

    # Ontology labels.
    labelled = neo4j_session.run(
        """
        RETURN
            COUNT { MATCH (n:NeonOrganization:Tenant) } AS orgs,
            COUNT { MATCH (n:NeonProject:Tenant) } AS projects,
            COUNT { MATCH (n:NeonOrganizationMember:UserAccount) } AS members,
            COUNT { MATCH (n:NeonApiKey:APIKey) } AS keys,
            COUNT { MATCH (n:NeonCredential:APIKey) } AS credentials,
            COUNT { MATCH (n:NeonDatabase:Database) } AS databases,
            COUNT { MATCH (n:NeonStorageBucket:ObjectStorage) } AS buckets
        """,
    ).single()
    assert dict(labelled) == {
        "orgs": 1,
        "projects": 2,
        "members": 2,
        "keys": 2,
        "credentials": 2,
        "databases": 4,
        "buckets": 6,
    }


def test_neon_org_api_key_uses_explicit_org_ids(neo4j_session):
    """An organization API key cannot call /users/me/organizations."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    session = _run(
        neo4j_session,
        TEST_UPDATE_TAG,
        _routes(**{"/users/me/organizations": 404}),
        org_ids=api.ORG_ID,
    )
    assert "/users/me/organizations" not in session.calls
    assert check_nodes(neo4j_session, "NeonOrganization", ["id"]) == {(api.ORG_ID,)}
    assert len(check_nodes(neo4j_session, "NeonEndpoint", ["id"])) == 4


def test_neon_unreadable_listings_keep_existing_nodes(neo4j_session):
    """A 403 on a Beta listing must not look like an empty inventory."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _run(neo4j_session, TEST_UPDATE_TAG, _routes())

    preview = f"/projects/{api.PLANT_PROJECT_ID}/branches/{api.PLANT_PREVIEW}"
    _run(
        neo4j_session,
        TEST_UPDATE_TAG + 1,
        _routes(
            **{
                f"{preview}/buckets": 403,
                f"{preview}/credentials": 403,
                f"/organizations/{api.ORG_ID}/members": 403,
                f"/organizations/{api.ORG_ID}/api_keys": 403,
            },
        ),
    )

    # Preview's buckets were not refreshed but are still present.
    buckets = check_nodes(neo4j_session, "NeonStorageBucket", ["id", "lastupdated"])
    assert (f"{api.PLANT_PREVIEW}/press-kit", TEST_UPDATE_TAG) in buckets
    assert (f"{api.PLANT_MAIN}/press-kit", TEST_UPDATE_TAG + 1) in buckets
    assert len(buckets) == 6
    # The preview-issued credential is only listed on preview and its child, and
    # the hotfix listing still returned it, so it was refreshed.
    assert len(check_nodes(neo4j_session, "NeonCredential", ["id"])) == 2
    assert len(check_nodes(neo4j_session, "NeonOrganizationMember", ["id"])) == 2
    assert len(check_nodes(neo4j_session, "NeonApiKey", ["id"])) == 2


def test_neon_deleted_project_cascades(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _run(neo4j_session, TEST_UPDATE_TAG, _routes())

    _run(
        neo4j_session,
        TEST_UPDATE_TAG + 1,
        _routes(**{"/projects": {"projects": [api.PLANT_PROJECT]}}),
    )

    assert check_nodes(neo4j_session, "NeonProject", ["id"]) == {
        (api.PLANT_PROJECT_ID,),
    }
    for label in ("NeonBranch", "NeonEndpoint", "NeonRole", "NeonDatabase"):
        ids = {row[0] for row in check_nodes(neo4j_session, label, ["id"])}
        assert not any("grid" in i for i in ids), (label, ids)


def test_neon_incomplete_project_listing_skips_cleanup(neo4j_session):
    """unavailable_project_ids means the project exists but could not be read."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _run(neo4j_session, TEST_UPDATE_TAG, _routes())

    _run(
        neo4j_session,
        TEST_UPDATE_TAG + 1,
        _routes(
            **{
                "/projects": {
                    "projects": [api.PLANT_PROJECT],
                    "unavailable_project_ids": [api.GRID_PROJECT_ID],
                },
            },
        ),
    )

    assert check_nodes(neo4j_session, "NeonProject", ["id"]) == {
        (api.PLANT_PROJECT_ID,),
        (api.GRID_PROJECT_ID,),
    }
    assert ("ep-grid-main",) in check_nodes(neo4j_session, "NeonEndpoint", ["id"])


def test_neon_deleted_branch_is_cleaned_up(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _run(neo4j_session, TEST_UPDATE_TAG, _routes())

    plant = f"/projects/{api.PLANT_PROJECT_ID}"
    branches = {
        **api.PLANT_BRANCHES,
        "branches": [
            b for b in api.PLANT_BRANCHES["branches"] if b["id"] != api.PLANT_HOTFIX
        ],
    }
    endpoints = {
        "endpoints": [
            e
            for e in api.PLANT_ENDPOINTS["endpoints"]
            if e["branch_id"] != api.PLANT_HOTFIX
        ],
    }
    _run(
        neo4j_session,
        TEST_UPDATE_TAG + 1,
        _routes(**{f"{plant}/branches": branches, f"{plant}/endpoints": endpoints}),
    )

    for label in ("NeonBranch", "NeonEndpoint", "NeonRole", "NeonDatabase"):
        ids = {row[0] for row in check_nodes(neo4j_session, label, ["id"])}
        assert not any("hotfix" in i for i in ids), (label, ids)
    bucket_ids = {
        row[0] for row in check_nodes(neo4j_session, "NeonStorageBucket", ["id"])
    }
    assert not any(api.PLANT_HOTFIX in i for i in bucket_ids)
    assert len(bucket_ids) == 4
