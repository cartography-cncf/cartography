"""
Unit tests pinning the LangSmith transform behaviours that live-API probing corrected.

Each test names the assumption that turned out to be wrong, so a future refactor cannot
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


class TestOrganizationBootstrap:
    def test_org_id_comes_from_scope_not_response_body(self):
        """OrganizationInfo.id is nullable, so the scoped org id must win."""
        org = organizations.transform_organization("org-1", {"display_name": "Acme"})
        assert org["id"] == "org-1"
        assert org["display_name"] == "Acme"


class TestPermissionCatalog:
    """
    /api/v1/orgs/permissions returns 403 for a personal access token, so the catalog is
    derived from what the roles grant.
    """

    def test_permissions_derived_from_roles(self):
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
                "organization_id": "org-1",
                "access_scope": "workspace",
                "permissions": ["deployments:read", "organization:read"],
            },
        ]
        perms = roles.transform_permissions(raw)
        assert [p["name"] for p in perms] == [
            "deployments:read",
            "organization:manage",
            "organization:read",
        ]
        by_name = {p["name"]: p for p in perms}
        assert by_name["organization:manage"]["access_scope"] == "organization"
        assert by_name["deployments:read"]["access_scope"] == "workspace"

    def test_no_roles_yields_no_permissions(self):
        assert roles.transform_permissions([]) == []


class TestCustomRoleDetection:
    def test_custom_roles_are_identified_by_owning_org_not_by_name(self):
        """Every organization-defined role is stored upstream under the name CUSTOM."""
        raw = [
            {
                "id": "r1",
                "name": "CUSTOM",
                "display_name": "Auditor",
                "organization_id": "org-1",
                "access_scope": "workspace",
                "permissions": [],
            },
            {
                "id": "r2",
                "name": "CUSTOM",
                "display_name": "Release Manager",
                "organization_id": "org-1",
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
        out = {r["id"]: r for r in roles.transform_roles(raw)}
        assert out["r1"]["is_custom"] is True
        assert out["r2"]["is_custom"] is True
        assert out["r3"]["is_custom"] is False
        # The transform carries the raw API keys; the node schema maps `name` to
        # system_name and `display_name` to the queryable name.
        # Both custom roles share the system name and differ only by display name.
        assert out["r1"]["name"] == out["r2"]["name"] == "CUSTOM"
        assert out["r1"]["display_name"] != out["r2"]["display_name"]


class TestUserIdentity:
    def test_org_role_falls_back_to_role_id(self):
        """Live member rows carry the org role in role_id, leaving org_role_id null."""
        member = {
            "id": "identity-1",
            "ls_user_id": "user-1",
            "email": "hjsimpson@simpson.corp",
            "role_id": "role-1",
            "role_name": "Organization Admin",
            "org_role_id": None,
            "org_role_name": None,
            "tenant_ids": [],
        }
        out = users.transform_users([member], [])[0]
        assert out["org_role_id"] == "role-1"
        assert out["org_role_name"] == "Organization Admin"

    def test_identity_uuid_is_not_used_as_the_user_id(self):
        member = {
            "id": "identity-1",
            "ls_user_id": "user-1",
            "email": "e@x.com",
            "tenant_ids": [],
        }
        out = users.transform_users([member], [])[0]
        assert out["ls_user_id"] == "user-1"
        assert out["org_identity_id"] == "identity-1"

    def test_pending_invite_without_ls_user_id_is_dropped(self):
        pending = [{"id": "i9", "email": "new@x.com", "ls_user_id": None}]
        assert users.transform_users([], pending) == []

    def test_usernames_collected_for_owner_resolution(self):
        member = {
            "id": "i1",
            "ls_user_id": "user-1",
            "email": "e@x.com",
            "tenant_ids": [],
            "linked_login_methods": [
                {
                    "provider": "oidc",
                    "provisioning_method": "scim",
                    "username": "hjsimpson",
                },
            ],
        }
        out = users.transform_users([member], [])[0]
        assert out["usernames"] == ["hjsimpson"]


class TestOwnerResolution:
    """created_by is undocumented and observed as an id, an email, or a bare username."""

    def _lookup(self):
        return build_user_lookup(
            [
                {
                    "ls_user_id": "user-1",
                    "org_identity_id": "identity-1",
                    "email": "HJSimpson@Simpson.Corp",
                    "usernames": ["HJSimpson"],
                }
            ]
        )

    def test_resolves_from_every_observed_identifier_shape(self):
        lookup = self._lookup()
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
        lookup = self._lookup()
        assert resolve_ls_user_id(None, lookup) is None
        assert resolve_ls_user_id("", lookup) is None
        assert resolve_ls_user_id("someone-else", lookup) is None


class TestDeploymentSecrets:
    def test_secret_values_are_dropped_and_names_kept(self):
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
        out = deployments.transform_deployments(raw)[0]
        assert out["secret_names"] == ["OPENAI_API_KEY", "SLACK_BOT_TOKEN"]
        assert out["secret_reference_names"] == ["DB_PASSWORD"]
        assert "SENTINEL" not in str(out)

    def test_null_agent_block_yields_no_agent(self):
        """Deployment.agent is null on the overwhelming majority of real deployments."""
        raw = [{"id": "d1", "tenant_id": "w1", "name": "bot", "agent": None}]
        out = deployments.transform_deployments(raw)
        assert out[0]["agent_id"] is None
        assert deployments.transform_agents(out) == []

    def test_agent_block_yields_one_agent(self):
        raw = [
            {
                "id": "d1",
                "tenant_id": "w1",
                "name": "bot",
                "display_name": "Bot",
                "agent": {"agent_id": "asst-1", "environment": "production"},
            }
        ]
        agents = deployments.transform_agents(deployments.transform_deployments(raw))
        assert agents == [
            {
                "id": "asst-1",
                "name": "Bot",
                "environment": "production",
                "deployment_ids": ["d1"],
            }
        ]


class TestAgentCredentials:
    def test_connection_attributes_a_human(self):
        lookup = build_user_lookup(
            [{"ls_user_id": "user-1", "email": "e@x.com", "usernames": []}]
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
        out = agent_auth.transform_credentials(raw, lookup)[0]
        assert out["owner_ls_user_id"] == "user-1"
        assert out["agent_id"] == "asst-1"
        assert out["provider_id"] == "github-prod"
        assert out["scopes"] == ["repo"]

    def test_no_token_material_survives_transform(self):
        raw = [
            {
                "id": "conn-1",
                "agent_id": "asst-1",
                "provider_id": "github-prod",
                "access_token": "should-never-appear",
                "refresh_token": "should-never-appear",
            }
        ]
        out = agent_auth.transform_credentials(raw, {})[0]
        assert "should-never-appear" not in str(out)
        assert "access_token" not in out
        assert "refresh_token" not in out


class TestProviderTransform:
    def test_platform_flag_distinguishes_managed_providers(self):
        own = agent_auth.transform_provider(
            {"id": "p1", "provider_id": "github", "name": "GH"}, is_platform=False
        )
        managed = agent_auth.transform_provider(
            {"id": "p2", "provider_id": "google", "name": "G"}, is_platform=True
        )
        assert own["is_platform_provider"] is False
        assert managed["is_platform_provider"] is True

    def test_client_secret_is_never_carried(self):
        out = agent_auth.transform_provider(
            {"id": "p1", "provider_id": "s", "client_secret": "shhh", "name": "X"},
            is_platform=False,
        )
        assert "shhh" not in str(out)
        assert "client_secret" not in out


class TestAssistantDiscovery:
    """
    A LangGraph Platform agent id is an assistant id, listable only on each deployment's
    own data plane. Without this the agent-to-user OAuth graph is empty, because a
    deployment's agent block is almost always null.
    """

    class _FakeClient:
        def __init__(self, by_url):
            self.by_url = by_url
            self._lock = threading.Lock()
            self.calls = []

        def search_assistants(self, deployment_url, tenant_id, page_size=100):
            # Searches run on a thread pool, so record calls under a lock.
            with self._lock:
                self.calls.append((deployment_url, tenant_id))
            return self.by_url.get(deployment_url, [])

    def test_assistants_become_agents(self):
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
            # No serving URL, so nothing to ask.
            {"id": "d2", "tenant_id": "w1", "url": None, "status": "READY"},
        ]
        out = deployments.get_assistants(client, deps)
        assert [a["id"] for a in out] == ["asst-1"]
        assert out[0]["graph_id"] == "support_graph"
        assert out[0]["deployment_ids"] == ["d1"]
        assert out[0]["version"] == 3
        # Only the deployment with a URL is probed, and the tenant is passed through.
        assert client.calls == [("https://d1.langgraph.app", "w1")]

    def test_merge_prefers_assistant_detail_over_agent_block(self):
        from_block = [{"id": "asst-1", "name": None, "environment": "production"}]
        from_assistants = [
            {
                "id": "asst-1",
                "name": "Support",
                "graph_id": "g",
                "environment": None,
                "deployment_ids": ["d1"],
            }
        ]
        merged = deployments.merge_assistants(from_block, from_assistants)
        assert len(merged) == 1
        agent = merged[0]
        # Assistant detail fills the gaps without discarding what the block knew.
        assert agent["name"] == "Support"
        assert agent["graph_id"] == "g"
        assert agent["deployment_ids"] == ["d1"]
        assert agent["environment"] == "production"

    def test_merge_keeps_agents_with_no_assistant_record(self):
        merged = deployments.merge_assistants(
            [{"id": "asst-1", "name": "Only in block"}], []
        )
        assert [a["id"] for a in merged] == ["asst-1"]

    def test_merge_adds_assistants_with_no_agent_block(self):
        merged = deployments.merge_assistants([], [{"id": "asst-2", "name": "New"}])
        assert [a["id"] for a in merged] == ["asst-2"]


class TestAssistantServedByManyDeployments:
    def test_same_assistant_id_accumulates_serving_deployments(self):
        """LangGraph derives an assistant id from its graph, so deployments can share one."""
        assistants = [
            {"id": "asst-1", "name": "Support", "deployment_ids": ["d1"]},
            {"id": "asst-1", "name": "Support", "deployment_ids": ["d2"]},
            {"id": "asst-2", "name": "Triage", "deployment_ids": ["d2"]},
        ]
        merged = {a["id"]: a for a in deployments.merge_assistants([], assistants)}
        assert merged["asst-1"]["deployment_ids"] == ["d1", "d2"]
        assert merged["asst-2"]["deployment_ids"] == ["d2"]


class TestAssistantSearchIsScopedAndConcurrent:
    """
    Probing a deployment costs a request to its own data plane, and a non-serving one
    costs a full timeout to learn nothing, so only READY deployments with a URL are asked.
    """

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
            return [{"assistant_id": f"asst-{deployment_url[-1]}"}]

    def test_only_ready_deployments_with_a_url_are_probed(self):
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
        out = deployments.get_assistants(client, deps)
        assert client.asked == ["https://a"]
        assert [a["id"] for a in out] == ["asst-a"]

    def test_nothing_serving_means_no_requests(self):
        client = self._RecordingClient()
        deps = [{"id": "a", "tenant_id": "w", "url": "https://a", "status": "UNUSED"}]
        assert deployments.get_assistants(client, deps) == []
        assert client.asked == []

    def test_searches_run_concurrently(self):
        """
        Proven with a barrier rather than timing: if the searches ran serially, the first
        worker would wait for peers that never arrive and the barrier would break.
        """
        count = 6
        barrier = threading.Barrier(count, timeout=10)

        class _BarrierClient:
            def search_assistants(self, deployment_url, tenant_id, page_size=100):
                barrier.wait()
                return [{"assistant_id": f"asst-{deployment_url[-1]}"}]

        deps = [
            {"id": str(i), "tenant_id": "w", "url": f"https://{i}", "status": "READY"}
            for i in range(count)
        ]
        out = deployments.get_assistants(_BarrierClient(), deps)
        assert len(out) == count

    def test_worker_count_never_exceeds_the_cap(self):
        client = self._RecordingClient()
        total = deployments._MAX_ASSISTANT_WORKERS + 15
        deps = [
            {"id": str(i), "tenant_id": "w", "url": f"https://{i}", "status": "READY"}
            for i in range(total)
        ]
        out = deployments.get_assistants(client, deps)
        assert len(out) == total
        assert len(client.asked) == total
        assert client.max_concurrent <= deployments._MAX_ASSISTANT_WORKERS


class TestNonServingDeploymentsAreStillInventoried:
    def test_a_deployment_awaiting_delete_is_transformed_but_not_probed(self):
        """
        Skipping the assistant probe must not drop the deployment from the graph: a
        deployment being torn down is still an asset worth inventorying.
        """
        raw = [
            {
                "id": "d1",
                "tenant_id": "w1",
                "name": "dying-bot",
                "status": "AWAITING_DELETE",
                "url": "https://d1.langgraph.app",
            }
        ]
        transformed = deployments.transform_deployments(raw)
        assert [d["id"] for d in transformed] == ["d1"]
        assert transformed[0]["status"] == "AWAITING_DELETE"

        class _Boom:
            def search_assistants(self, *a, **k):
                raise AssertionError("must not probe a non-serving deployment")

        assert deployments.get_assistants(_Boom(), transformed) == []
