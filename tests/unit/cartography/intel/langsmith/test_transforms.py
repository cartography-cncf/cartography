"""
Unit tests pinning the LangSmith transform behaviours that live-API probing and code
review corrected.

Each test names the assumption or defect it guards against, so a future refactor cannot
quietly reintroduce it. These run without Neo4j.
"""

import threading
import time

from cartography.intel.langsmith import agent_auth
from cartography.intel.langsmith import deployments
from cartography.intel.langsmith import organizations
from cartography.intel.langsmith import roles
from cartography.intel.langsmith import users
from cartography.intel.langsmith.util import build_user_lookup
from cartography.intel.langsmith.util import resolve_ls_user_id

ORG = "org-1"
OTHER_ORG = "org-2"


class TestOrganizationBootstrap:
    def test_org_id_comes_from_scope_not_response_body(self):
        """OrganizationInfo.id is nullable, so the scoped org id must win."""
        # Act
        org = organizations.transform_organization("org-1", {"display_name": "Acme"})

        # Assert
        assert org["id"] == "org-1"
        assert org["display_name"] == "Acme"


class TestPermissionCatalog:
    """
    /api/v1/orgs/permissions returns 403 for a personal access token, so the catalog is
    derived from what the roles grant.
    """

    def test_permissions_derived_from_roles(self):
        # Arrange
        raw = [
            {
                "id": "r1",
                "name": "ORGANIZATION_ADMIN",
                "display_name": "Organization Admin",
                "access_scope": "organization",
                "permissions": ["organization:manage", "organization:read"],
            },
            {
                "id": "r2",
                "name": "CUSTOM",
                "display_name": "Auditor",
                "organization_id": ORG,
                "access_scope": "workspace",
                "permissions": ["deployments:read", "organization:read"],
            },
        ]

        # Act
        perms = roles.transform_permissions(raw, ORG)

        # Assert
        assert [p["name"] for p in perms] == [
            "deployments:read",
            "organization:manage",
            "organization:read",
        ]
        by_name = {p["name"]: p for p in perms}
        assert by_name["organization:manage"]["access_scope"] == "organization"
        assert by_name["deployments:read"]["access_scope"] == "workspace"

    def test_no_roles_yields_no_permissions(self):
        # Act and assert
        assert roles.transform_permissions([], ORG) == []

    def test_same_permission_in_two_orgs_is_two_nodes(self):
        """Each organization's cleanup must only reach permissions it owns."""
        # Arrange
        raw = [{"id": "r1", "name": "CUSTOM", "permissions": ["deployments:read"]}]

        # Act
        a_perms = roles.transform_permissions(raw, ORG)
        b_perms = roles.transform_permissions(raw, OTHER_ORG)
        a_roles = roles.transform_roles([{**raw[0], "display_name": "Auditor"}], ORG)

        # Assert
        assert a_perms[0]["id"] != b_perms[0]["id"]
        assert a_roles[0]["permission_ids"] == [a_perms[0]["id"]]


class TestCustomRoleDetection:
    def test_custom_roles_are_identified_by_owning_org_not_by_name(self):
        """Every organization-defined role is stored upstream under the name CUSTOM."""
        # Arrange
        raw = [
            {
                "id": "r1",
                "name": "CUSTOM",
                "display_name": "Auditor",
                "organization_id": ORG,
                "access_scope": "workspace",
                "permissions": [],
            },
            {
                "id": "r2",
                "name": "CUSTOM",
                "display_name": "Release Manager",
                "organization_id": ORG,
                "access_scope": "workspace",
                "permissions": [],
            },
            {
                "id": "r3",
                "name": "WORKSPACE_VIEWER",
                "display_name": "Viewer",
                "organization_id": None,
                "access_scope": "workspace",
                "permissions": [],
            },
        ]

        # Act
        out = {r["role_id"]: r for r in roles.transform_roles(raw, ORG)}

        # Assert
        assert out["r1"]["is_custom"] is True
        assert out["r2"]["is_custom"] is True
        assert out["r3"]["is_custom"] is False
        assert out["r1"]["name"] == out["r2"]["name"] == "CUSTOM"
        assert out["r1"]["display_name"] != out["r2"]["display_name"]


class TestUserIdentityIsSeparateFromOrgState:
    """
    A user can belong to several organizations. Organization-specific state must not be
    written onto the globally keyed user node, or the last organization synced silently
    overwrites the others.
    """

    def _member(self, **over):
        member = {
            "id": "identity-1",
            "ls_user_id": "user-1",
            "email": "hjsimpson@simpson.corp",
            "full_name": "Homer Simpson",
            "is_disabled": False,
            "role_id": "role-1",
            "role_name": "Organization Admin",
            "org_role_id": None,
            "org_role_name": None,
            "tenant_ids": [],
        }
        member.update(over)
        return member

    def test_user_node_carries_no_org_specific_state(self):
        # Act
        us, _ = users.transform_users(ORG, [self._member()], [])

        # Assert
        user = us[0]
        assert user["ls_user_id"] == "user-1"
        for org_scoped in (
            "is_disabled",
            "org_identity_id",
            "role_id",
            "role_name",
            "org_role_id",
            "org_role_name",
            "is_pending",
        ):
            assert org_scoped not in user, org_scoped

    def test_org_state_lands_on_the_membership(self):
        # Act
        _, memberships = users.transform_users(
            ORG, [self._member(is_disabled=True)], []
        )

        # Assert
        membership = memberships[0]
        assert membership["id"] == f"{ORG}|user-1"
        assert membership["identity_id"] == "identity-1"
        assert membership["is_disabled"] is True
        # Live member rows carry the org role in role_id, leaving org_role_id null.
        assert membership["role_id"] == f"{ORG}|role-1"
        assert membership["role_name"] == "Organization Admin"

    def test_two_orgs_produce_one_user_and_two_memberships(self):
        # Act
        a_users, a_memberships = users.transform_users(
            ORG, [self._member(is_disabled=False)], []
        )
        b_users, b_memberships = users.transform_users(
            OTHER_ORG, [self._member(is_disabled=True)], []
        )

        # Assert
        assert a_users[0]["ls_user_id"] == b_users[0]["ls_user_id"] == "user-1"
        # Disabled in one org, active in the other, and both facts survive.
        assert a_memberships[0]["is_disabled"] is False
        assert b_memberships[0]["is_disabled"] is True
        assert a_memberships[0]["id"] != b_memberships[0]["id"]

    def test_pending_invite_without_ls_user_id_is_dropped(self):
        # Arrange
        pending = [{"id": "i9", "email": "new@x.com", "ls_user_id": None}]

        # Act and assert
        assert users.transform_users(ORG, [], pending) == ([], [])

    def test_usernames_collected_for_owner_resolution(self):
        # Arrange
        member = self._member(
            linked_login_methods=[
                {
                    "provider": "oidc",
                    "provisioning_method": "scim",
                    "username": "hjsimpson",
                }
            ]
        )

        # Act
        us, memberships = users.transform_users(ORG, [member], [])

        # Assert
        assert us[0]["usernames"] == ["hjsimpson"]
        assert memberships[0]["login_methods"] == ["oidc"]


class TestWorkspaceLinks:
    def test_links_come_from_the_org_listing_and_skip_unaccepted_invites(self):
        # Arrange
        active = [
            {"ls_user_id": "user-1", "tenant_ids": ["ws-2", "ws-1", "ws-1"]},
            {"ls_user_id": None, "tenant_ids": ["ws-1"]},
        ]

        # Act
        links = users.transform_workspace_links(active)

        # Assert
        assert links == [
            {"ls_user_id": "user-1", "workspace_id": "ws-1"},
            {"ls_user_id": "user-1", "workspace_id": "ws-2"},
        ]


class TestOwnerResolution:
    """created_by is undocumented and observed as an id, an email, or a bare username."""

    def _lookup(self):
        member = {
            "id": "identity-1",
            "ls_user_id": "user-1",
            "email": "HJSimpson@Simpson.Corp",
            "linked_login_methods": [{"provider": "email", "username": "HJSimpson"}],
        }
        return build_user_lookup(*users.transform_users(ORG, [member], []))

    def test_resolves_from_every_observed_identifier_shape(self):
        # Arrange
        lookup = self._lookup()

        # Act and assert
        for candidate in (
            "user-1",
            "identity-1",
            "hjsimpson@simpson.corp",
            "HJSimpson@Simpson.Corp",
            "hjsimpson",
            "HJSimpson",
        ):
            assert resolve_ls_user_id(candidate, lookup) == "user-1", candidate

    def test_unknown_and_missing_resolve_to_none(self):
        # Arrange
        lookup = self._lookup()

        # Act and assert
        assert resolve_ls_user_id(None, lookup) is None
        assert resolve_ls_user_id("", lookup) is None
        assert resolve_ls_user_id("someone-else", lookup) is None


class TestDeploymentSecrets:
    def test_secret_values_are_dropped_and_names_kept(self):
        # Arrange
        raw = [
            {
                "id": "d1",
                "tenant_id": "w1",
                "name": "bot",
                "secrets": [
                    {
                        "name": "OPENAI_API_KEY",
                        "value": "SENTINEL-MUST-NOT-BE-INGESTED",
                    },
                    {
                        "name": "SLACK_BOT_TOKEN",
                        "value": "SENTINEL-MUST-NOT-BE-INGESTED",
                    },
                ],
                "secret_references": [
                    {"name": "DB_PASSWORD", "secret_name": "s", "secret_key": "k"},
                ],
            }
        ]

        # Act
        out = deployments.transform_deployments(raw)[0]

        # Assert
        assert out["secret_names"] == ["OPENAI_API_KEY", "SLACK_BOT_TOKEN"]
        assert out["secret_reference_names"] == ["DB_PASSWORD"]
        assert "SENTINEL" not in str(out)

    def test_null_agent_block_yields_no_agent(self):
        """Deployment.agent is null on the overwhelming majority of real deployments."""
        # Arrange
        raw = [{"id": "d1", "tenant_id": "w1", "name": "bot", "agent": None}]

        # Act
        out = deployments.transform_deployments(raw)
        agents = deployments.transform_agents(out, ORG)

        # Assert
        assert out[0]["agent_id"] is None
        assert agents == []

    def test_agent_block_yields_one_namespaced_agent(self):
        # Arrange
        raw = [
            {
                "id": "d1",
                "tenant_id": "w1",
                "name": "bot",
                "display_name": "Bot",
                "agent": {"agent_id": "asst-1", "environment": "production"},
            }
        ]

        # Act
        agents = deployments.transform_agents(
            deployments.transform_deployments(raw), ORG
        )

        # Assert
        assert agents == [
            {
                "id": f"{ORG}|asst-1",
                "assistant_id": "asst-1",
                "name": "Bot",
                "environment": "production",
                "deployment_ids": ["d1"],
            }
        ]


class TestAgentIdentityIsNamespacedByOrg:
    """
    LangSmith derives an assistant id from its graph, so two organizations running the
    same graph produce the same assistant id. Un-namespaced, their agents, deployments and
    credential paths would merge.
    """

    def _client(self):
        class _C:
            def search_assistants(self, url, tenant_id, page_size=100):
                return [{"assistant_id": "asst-shared", "name": "Shared"}], True

        return _C()

    def test_same_assistant_in_two_orgs_stays_two_agents(self):
        # Arrange
        deps = [{"id": "d1", "tenant_id": "w1", "url": "https://d", "status": "READY"}]

        # Act
        a, _ = deployments.get_assistants(self._client(), deps, ORG)
        b, _ = deployments.get_assistants(self._client(), deps, OTHER_ORG)

        # Assert
        assert a[0]["id"] != b[0]["id"]
        assert a[0]["id"] == f"{ORG}|asst-shared"
        # The raw id is kept, because the agent-auth API is keyed by it.
        assert a[0]["assistant_id"] == b[0]["assistant_id"] == "asst-shared"

    def test_credential_agent_id_is_namespaced_to_match(self):
        # Act
        creds = agent_auth.transform_credentials(
            [{"id": "c1", "agent_id": "asst-shared", "provider_id": "p"}], {}, {}, ORG
        )

        # Assert
        assert creds[0]["agent_id"] == f"{ORG}|asst-shared"
        assert creds[0]["assistant_id"] == "asst-shared"


class TestCredentialProviderResolution:
    """
    provider_id is an operator-chosen slug, so two organizations can both define
    github-prod. Relationship matching carries no implicit organization constraint, so the
    slug is resolved to this organization's provider UUID before loading.
    """

    def test_slug_resolves_to_this_orgs_provider_uuid(self):
        # Act
        creds = agent_auth.transform_credentials(
            [{"id": "c1", "agent_id": "a", "provider_id": "github-prod"}],
            {},
            {"github-prod": "uuid-for-org-1"},
            ORG,
        )

        # Assert
        assert creds[0]["provider_uuid"] == "uuid-for-org-1"

    def test_unknown_slug_leaves_the_edge_unmatched_rather_than_guessing(self):
        # Act
        creds = agent_auth.transform_credentials(
            [{"id": "c1", "agent_id": "a", "provider_id": "not-in-this-org"}],
            {},
            {"github-prod": "uuid-for-org-1"},
            ORG,
        )

        # Assert
        assert creds[0]["provider_uuid"] is None


class TestAgentCredentials:
    def test_connection_attributes_a_human(self):
        # Arrange
        lookup = build_user_lookup(
            [{"ls_user_id": "user-1", "email": "e@x.com", "usernames": []}], []
        )
        raw = [
            {
                "id": "conn-1",
                "agent_id": "asst-1",
                "provider_id": "github-prod",
                "oauth_token_id": "tok-1",
                "scopes": ["repo"],
                "created_by": "user-1",
            }
        ]

        # Act
        out = agent_auth.transform_credentials(raw, lookup, {"github-prod": "p1"}, ORG)[
            0
        ]

        # Assert
        assert out["owner_ls_user_id"] == "user-1"
        assert out["agent_id"] == f"{ORG}|asst-1"
        assert out["scopes"] == ["repo"]

    def test_no_token_material_survives_transform(self):
        # Arrange
        raw = [
            {
                "id": "conn-1",
                "agent_id": "asst-1",
                "provider_id": "github-prod",
                "access_token": "SENTINEL-MUST-NOT-BE-INGESTED",
                "refresh_token": "SENTINEL-MUST-NOT-BE-INGESTED",
            }
        ]

        # Act
        out = agent_auth.transform_credentials(raw, {}, {}, ORG)[0]

        # Assert
        assert "SENTINEL" not in str(out)
        assert "access_token" not in out
        assert "refresh_token" not in out


class TestProviderTransform:
    def test_platform_flag_distinguishes_managed_providers(self):
        # Act
        own = agent_auth.transform_provider(
            {"id": "p1", "provider_id": "github", "name": "GH"}, is_platform=False
        )
        managed = agent_auth.transform_provider(
            {"id": "p2", "provider_id": "google", "name": "G"}, is_platform=True
        )

        # Assert
        assert own["is_platform_provider"] is False
        assert managed["is_platform_provider"] is True

    def test_client_secret_is_never_carried(self):
        # Act
        out = agent_auth.transform_provider(
            {"id": "p1", "provider_id": "s", "client_secret": "shhh", "name": "X"},
            is_platform=False,
        )

        # Assert
        assert "shhh" not in str(out)
        assert "client_secret" not in out


class TestAssistantDiscovery:
    class _FakeClient:
        def __init__(self, by_url):
            self.by_url = by_url
            self._lock = threading.Lock()
            self.calls = []

        def search_assistants(self, deployment_url, tenant_id, page_size=100):
            with self._lock:
                self.calls.append((deployment_url, tenant_id))
            return self.by_url.get(deployment_url, []), True

    def test_assistants_become_agents(self):
        # Arrange
        client = self._FakeClient(
            {
                "https://d1.langgraph.app": [
                    {
                        "assistant_id": "asst-1",
                        "name": "Support",
                        "graph_id": "support_graph",
                        "description": None,
                        "version": 3,
                        "created_at": "2026-02-01T00:00:00Z",
                        "updated_at": "2026-03-01T00:00:00Z",
                    }
                ]
            }
        )
        deps = [
            {
                "id": "d1",
                "tenant_id": "w1",
                "url": "https://d1.langgraph.app",
                "status": "READY",
            },
            {"id": "d2", "tenant_id": "w1", "url": None, "status": "READY"},
        ]

        # Act
        out, complete = deployments.get_assistants(client, deps, ORG)

        # Assert
        # d2 has no URL, so its agents cannot be listed this run.
        assert complete is False
        assert [a["id"] for a in out] == [f"{ORG}|asst-1"]
        assert out[0]["graph_id"] == "support_graph"
        assert out[0]["deployment_ids"] == ["d1"]
        assert client.calls == [("https://d1.langgraph.app", "w1")]

    def test_merge_prefers_assistant_detail_over_agent_block(self):
        # Arrange
        from_block = [
            {"id": f"{ORG}|asst-1", "name": None, "environment": "production"}
        ]
        from_assistants = [
            {
                "id": f"{ORG}|asst-1",
                "name": "Support",
                "graph_id": "g",
                "environment": None,
                "deployment_ids": ["d1"],
            }
        ]

        # Act
        merged = deployments.merge_assistants(from_block, from_assistants)

        # Assert
        assert len(merged) == 1
        agent = merged[0]
        assert agent["name"] == "Support"
        assert agent["graph_id"] == "g"
        assert agent["deployment_ids"] == ["d1"]
        assert agent["environment"] == "production"

    def test_same_assistant_accumulates_serving_deployments(self):
        # Arrange
        assistants = [
            {"id": "a1", "name": "Support", "deployment_ids": ["d1"]},
            {"id": "a1", "name": "Support", "deployment_ids": ["d2"]},
            {"id": "a2", "name": "Triage", "deployment_ids": ["d2"]},
        ]

        # Act
        merged = {a["id"]: a for a in deployments.merge_assistants([], assistants)}

        # Assert
        assert merged["a1"]["deployment_ids"] == ["d1", "d2"]
        assert merged["a2"]["deployment_ids"] == ["d2"]


class TestIncompleteDiscoveryIsNotAnEmptyInventory:
    """
    A failed listing must never look like "these no longer exist": cleanup deletes on
    exactly that signal, which would erase agents and their credentials.
    """

    class _FailingClient:
        def search_assistants(self, url, tenant_id, page_size=100):
            return [], False

    class _PartialClient:
        def search_assistants(self, url, tenant_id, page_size=100):
            if url.endswith("bad"):
                return [], False
            return [{"assistant_id": "asst-ok"}], True

    def test_total_failure_reports_incomplete(self):
        # Arrange
        deps = [{"id": "d", "tenant_id": "w", "url": "https://d", "status": "READY"}]

        # Act
        out, complete = deployments.get_assistants(self._FailingClient(), deps, ORG)

        # Assert
        assert out == []
        assert complete is False

    def test_one_failure_among_many_still_reports_incomplete(self):
        # Arrange
        deps = [
            {"id": "a", "tenant_id": "w", "url": "https://ok", "status": "READY"},
            {"id": "b", "tenant_id": "w", "url": "https://bad", "status": "READY"},
        ]

        # Act
        out, complete = deployments.get_assistants(self._PartialClient(), deps, ORG)

        # Assert
        assert len(out) == 1
        assert complete is False

    def test_no_deployments_is_a_complete_empty_inventory(self):
        # Act
        out, complete = deployments.get_assistants(self._FailingClient(), [], ORG)

        # Assert
        assert out == []
        assert complete is True

    def test_a_deployment_without_a_url_leaves_the_inventory_incomplete(self):
        """It still exists, so its agents may too; they just cannot be listed."""
        # Arrange
        deps = [{"id": "d", "tenant_id": "w", "url": None, "status": "READY"}]

        # Act
        out, complete = deployments.get_assistants(self._FailingClient(), deps, ORG)

        # Assert
        assert out == []
        assert complete is False


class TestAssistantSearchIsScopedAndConcurrent:
    class _RecordingClient:
        def __init__(self):
            self._lock = threading.Lock()
            self.asked = []
            self.max_concurrent = 0
            self._active = 0

        def search_assistants(self, deployment_url, tenant_id, page_size=100):
            with self._lock:
                self.asked.append(deployment_url)
                self._active += 1
                self.max_concurrent = max(self.max_concurrent, self._active)
            time.sleep(0.02)
            with self._lock:
                self._active -= 1
            return [{"assistant_id": f"asst-{deployment_url[-1]}"}], True

    def test_only_ready_deployments_with_a_url_are_probed(self):
        # Arrange
        client = self._RecordingClient()
        deps = [
            {"id": "a", "tenant_id": "w", "url": "https://a", "status": "READY"},
            {
                "id": "b",
                "tenant_id": "w",
                "url": "https://b",
                "status": "AWAITING_DATABASE",
            },
            {
                "id": "c",
                "tenant_id": "w",
                "url": "https://c",
                "status": "AWAITING_DELETE",
            },
            {"id": "d", "tenant_id": "w", "url": "https://d", "status": "UNUSED"},
            {"id": "e", "tenant_id": "w", "url": "https://e", "status": "UNKNOWN"},
            {"id": "f", "tenant_id": "w", "url": None, "status": "READY"},
        ]

        # Act
        out, complete = deployments.get_assistants(client, deps, ORG)

        # Assert
        assert client.asked == ["https://a"]
        assert [a["assistant_id"] for a in out] == ["asst-a"]
        assert complete is False

    def test_nothing_serving_means_no_requests(self):
        # Arrange
        client = self._RecordingClient()
        deps = [{"id": "a", "tenant_id": "w", "url": "https://a", "status": "UNUSED"}]

        # Act
        result = deployments.get_assistants(client, deps, ORG)

        # Assert
        assert result == ([], False)
        assert client.asked == []

    def test_searches_run_concurrently(self):
        """
        Proven with a barrier rather than timing: if the searches ran serially, the first
        worker would wait for peers that never arrive and the barrier would break.
        """
        # Arrange
        count = 6
        barrier = threading.Barrier(count, timeout=10)

        class _BarrierClient:
            def search_assistants(self, deployment_url, tenant_id, page_size=100):
                barrier.wait()
                return [{"assistant_id": f"asst-{deployment_url[-1]}"}], True

        deps = [
            {"id": str(i), "tenant_id": "w", "url": f"https://{i}", "status": "READY"}
            for i in range(count)
        ]

        # Act
        out, complete = deployments.get_assistants(_BarrierClient(), deps, ORG)

        # Assert
        assert len(out) == count
        assert complete is True

    def test_worker_count_never_exceeds_the_cap(self):
        # Arrange
        client = self._RecordingClient()
        total = deployments._MAX_ASSISTANT_WORKERS + 15
        deps = [
            {"id": str(i), "tenant_id": "w", "url": f"https://{i}", "status": "READY"}
            for i in range(total)
        ]

        # Act
        out, _ = deployments.get_assistants(client, deps, ORG)

        # Assert
        assert len(out) == total
        assert len(client.asked) == total
        assert client.max_concurrent <= deployments._MAX_ASSISTANT_WORKERS


class TestNonServingDeploymentsAreStillInventoried:
    def test_a_deployment_awaiting_delete_is_transformed_but_not_probed(self):
        # Arrange
        raw = [
            {
                "id": "d1",
                "tenant_id": "w1",
                "name": "dying-bot",
                "status": "AWAITING_DELETE",
                "url": "https://d1.langgraph.app",
            }
        ]

        class _Boom:
            def search_assistants(self, *a, **k):
                raise AssertionError("must not probe a non-serving deployment")

        # Act
        transformed = deployments.transform_deployments(raw)

        # Assert
        assert [d["id"] for d in transformed] == ["d1"]
        assert transformed[0]["status"] == "AWAITING_DELETE"

        # Act and assert
        assert deployments.get_assistants(_Boom(), transformed, ORG) == ([], False)


class TestCredentialsAreNotLeakedToRedirectTargets:
    """
    Deployment hosts come from API data, not operator config, and requests strips only the
    Authorization header when a redirect changes host. A custom X-Api-Key would be
    forwarded intact, handing an organization-admin token to whatever the redirect names.
    """

    def _client(self):
        from cartography.intel.langsmith.util import LangSmithClient

        return LangSmithClient(
            "lsv2_pt_fake", "https://api.example", "https://host.example"
        )

    def test_redirects_are_not_followed(self):
        # Arrange
        client = self._client()
        posted = {}

        class _Resp:
            status_code = 307
            is_redirect = True
            is_permanent_redirect = False

        class _Session:
            def post(self, url, **kwargs):
                posted.update(kwargs)
                return _Resp()

        client._thread_local.session = _Session()

        # Act
        assistants, complete = client.search_assistants("https://dep.example", "w1")

        # Assert
        assert posted["allow_redirects"] is False
        assert (assistants, complete) == ([], False)

    def test_a_redirect_is_reported_as_incomplete_not_empty(self):
        """Returning ([], True) here would let cleanup delete the agents behind it."""
        # Arrange
        client = self._client()

        class _Resp:
            status_code = 302
            is_redirect = True
            is_permanent_redirect = False

        class _Session:
            def post(self, *a, **k):
                return _Resp()

        client._thread_local.session = _Session()

        # Act and assert
        assert client.search_assistants("https://dep.example", "w1") == ([], False)

    def test_plaintext_deployment_urls_never_receive_the_token(self):
        # Arrange
        client = self._client()

        class _Session:
            def post(self, *a, **k):
                raise AssertionError("must not send credentials over plaintext HTTP")

        client._thread_local.session = _Session()

        # Act and assert
        assert client.search_assistants("http://dep.example", "w1") == ([], False)

    def test_non_200_is_incomplete(self):
        # Arrange
        client = self._client()

        class _Resp:
            status_code = 500
            is_redirect = False
            is_permanent_redirect = False

        class _Session:
            def post(self, *a, **k):
                return _Resp()

        client._thread_local.session = _Session()

        # Act and assert
        assert client.search_assistants("https://dep.example", "w1") == ([], False)

    def test_unexpected_shape_is_incomplete(self):
        # Arrange
        client = self._client()

        class _Resp:
            status_code = 200
            is_redirect = False
            is_permanent_redirect = False

            def json(self):
                return {"detail": "not a list"}

        class _Session:
            def post(self, *a, **k):
                return _Resp()

        client._thread_local.session = _Session()

        # Act and assert
        assert client.search_assistants("https://dep.example", "w1") == ([], False)
