from unittest.mock import Mock
from unittest.mock import patch

import pytest

import cartography.intel.flyio
import cartography.intel.flyio.access_tokens
import cartography.intel.flyio.apps
import cartography.intel.flyio.certificates
import cartography.intel.flyio.ips
import cartography.intel.flyio.machines
import cartography.intel.flyio.releases
import cartography.intel.flyio.secrets
import cartography.intel.flyio.users
import cartography.intel.flyio.volumes
from tests.data.flyio.access_tokens import APP_ACCESS_TOKENS_RESPONSE
from tests.data.flyio.access_tokens import ORG_ACCESS_TOKENS_RESPONSE
from tests.data.flyio.apps import APPS_RESPONSE
from tests.data.flyio.certificates import CERTIFICATES_RESPONSE
from tests.data.flyio.ips import IPS_RESPONSE
from tests.data.flyio.machines import MACHINES_RESPONSE
from tests.data.flyio.releases import RELEASES_RESPONSE
from tests.data.flyio.secrets import SECRETS_RESPONSE
from tests.data.flyio.users import ORG_MEMBERS_RESPONSE
from tests.data.flyio.volumes import VOLUMES_RESPONSE

TEST_APP_ID = "jlyv9r258ew18xrg"
TEST_MACHINE_ID = "90802949c92987"


def test_make_auth_header_supports_bare_tokens():
    # Act and assert
    assert cartography.intel.flyio._make_auth_header("test-token") == (
        "Bearer test-token"
    )


def test_make_auth_header_preserves_prefixed_tokens():
    # Act and assert
    assert cartography.intel.flyio._make_auth_header("FlyV1 fm2_test") == (
        "FlyV1 fm2_test"
    )
    assert cartography.intel.flyio._make_auth_header("Bearer test-token") == (
        "Bearer test-token"
    )


def test_transform_apps_and_organizations():
    # Act
    organizations = cartography.intel.flyio.apps.transform_organizations(
        APPS_RESPONSE,
        "jonathanfemi-example-com",
    )
    apps = cartography.intel.flyio.apps.transform_apps(APPS_RESPONSE)

    # Assert
    assert organizations == [
        {
            "id": "jonathanfemi-example-com",
            "name": "jonathanfemi@example.com",
            "slug": "jonathanfemi-example-com",
            "internal_numeric_id": 977819,
        },
    ]
    assert apps == [
        {
            "id": TEST_APP_ID,
            "name": "nhmhvxo3b9",
            "internal_numeric_id": 6726989,
            "network": "default",
            "status": "deployed",
            "machine_count": 3,
            "volume_count": 1,
            "cname_target": "5grkpx.nhmhvxo3b9.fly.dev",
            "app_role": "",
            "organization_slug": "jonathanfemi-example-com",
        },
    ]


def test_transform_organizations_uses_sync_scope_as_id():
    # Arrange
    response = {
        "apps": [
            {
                **APPS_RESPONSE["apps"][0],
                "organization": {
                    **APPS_RESPONSE["apps"][0]["organization"],
                    "slug": "jonathanfemi-example-com",
                },
            },
        ],
    }

    # Act
    organizations = cartography.intel.flyio.apps.transform_organizations(
        response,
        "personal",
    )

    # Assert
    assert organizations == [
        {
            "id": "personal",
            "name": "jonathanfemi@example.com",
            "slug": "jonathanfemi-example-com",
            "internal_numeric_id": 977819,
        },
    ]


def test_transform_machines_does_not_store_env_values():
    # Act
    machines = cartography.intel.flyio.machines.transform_machines(MACHINES_RESPONSE)

    # Assert
    assert machines == [
        {
            "id": TEST_MACHINE_ID,
            "name": "dry-rain-8738",
            "state": "started",
            "region": "lhr",
            "instance_id": "01KJQC1W6NXAK34WQ739F0ERSP",
            "private_ip": "fdaa:10:e286:a7b:34e:c803:57c:2",
            "image": "registry.fly.io/nhmhvxo3b9:deployment-01JMWNHS84ZCCV89XYH9SQ48FX",
            "image_registry": "registry.fly.io",
            "image_repository": "nhmhvxo3b9",
            "image_tag": "deployment-01JMWNHS84ZCCV89XYH9SQ48FX",
            "image_digest": (
                "sha256:"
                "b0cbba70b2f1fbb720502cff65ca83bbdbca1e02a78860ce075efdb320eb9802"
            ),
            "cpu_kind": "shared",
            "cpus": 1,
            "memory_mb": 1024,
            "restart_policy": "on-failure",
            "restart_max_retries": 10,
            "process_group": "app",
            "release_id": "YgoYklRLL8Xo3fBPg6AoX28AG",
            "release_version": "35",
            "host_status": "ok",
            "cordoned": False,
            "created_at": "2025-06-19T22:51:10Z",
            "updated_at": "2026-07-31T06:44:39Z",
        },
    ]
    assert "PORT" not in machines[0]
    assert "PRIMARY_REGION" not in machines[0]


def test_transform_machines_rejects_empty_ids():
    # Arrange
    machines = [{**MACHINES_RESPONSE[0], "id": ""}]

    # Act and assert
    with pytest.raises(ValueError, match="required non-empty id"):
        cartography.intel.flyio.machines.transform_machines(machines)


def test_transform_services_and_ports():
    # Act
    services = cartography.intel.flyio.machines.transform_services(MACHINES_RESPONSE)
    ports = cartography.intel.flyio.machines.transform_service_ports(
        MACHINES_RESPONSE,
    )

    # Assert
    service_id = f"{TEST_MACHINE_ID}/tcp/8000"
    assert services == [
        {
            "id": service_id,
            "protocol": "tcp",
            "internal_port": 8000,
            "autostop": True,
            "autostart": True,
            "min_machines_running": 0,
            "force_instance_key": None,
            "machine_id": TEST_MACHINE_ID,
        },
    ]
    assert ports == [
        {
            "id": f"{service_id}/80",
            "port": 80,
            "handlers": ["http"],
            "force_https": True,
            "service_id": service_id,
        },
        {
            "id": f"{service_id}/443",
            "port": 443,
            "handlers": ["http", "tls"],
            "force_https": None,
            "service_id": service_id,
        },
    ]


def test_transform_secrets_scopes_names_to_app():
    # Act
    secrets = cartography.intel.flyio.secrets.transform(
        SECRETS_RESPONSE,
        TEST_APP_ID,
    )

    # Assert
    assert secrets == [
        {
            "id": f"{TEST_APP_ID}/SECRET_KEY",
            "name": "SECRET_KEY",
            "digest": "fd78cec242f907ba",
            "created_at": "2025-02-22T00:18:21Z",
            "updated_at": "2025-02-22T00:18:21Z",
        },
        {
            "id": f"{TEST_APP_ID}/FLY_API_TOKEN",
            "name": "FLY_API_TOKEN",
            "digest": "7e3ce4aff82bb8bb",
            "created_at": "2025-02-23T16:43:33Z",
            "updated_at": "2025-02-23T16:43:33Z",
        },
    ]


def test_transform_volumes_and_certificates():
    # Act
    volumes = cartography.intel.flyio.volumes.transform(VOLUMES_RESPONSE)
    certificates = cartography.intel.flyio.certificates.transform(
        CERTIFICATES_RESPONSE,
        TEST_APP_ID,
    )

    # Assert
    assert volumes[0]["id"] == "vol_vlykw0x679gyz5p4"
    assert volumes[0]["attached_machine_id"] == TEST_MACHINE_ID
    assert volumes[0]["encrypted"] is True
    assert certificates == [
        {
            "id": f"{TEST_APP_ID}/www.example.com",
            "hostname": "www.example.com",
            "status": "active",
            "dns_provider": "enom",
            "configured": True,
            "acme_dns_configured": True,
            "acme_alpn_configured": True,
            "acme_http_configured": True,
            "ownership_txt_configured": True,
            "acme_requested": True,
            "has_custom_certificate": False,
            "has_fly_certificate": True,
            "certificate_authorities": ["lets_encrypt"],
            "sources": ["fly"],
            "issuers": [],
            "created_at": "2026-07-31T06:53:00Z",
            "updated_at": "2026-07-31T07:00:00Z",
        },
    ]


def test_transform_ips():
    # Act
    ips = cartography.intel.flyio.ips.transform(IPS_RESPONSE, TEST_APP_ID)

    # Assert
    assert ips == [
        {
            "id": "ip_v6_id",
            "address": "2a09:8280:1::66:a54d:0",
            "type": "v6",
            "region": "global",
            "created_at": "2026-07-31T09:10:00Z",
            "direction": "ingress",
            "ip_version": 6,
            "is_public": True,
            "service_name": None,
            "network_name": "default",
            "network_organization_slug": "personal",
        },
        {
            "id": "ip_private_v6_id",
            "address": "fdaa:10:e286:a7b::1",
            "type": "private_v6",
            "region": "global",
            "created_at": "2026-07-31T09:11:00Z",
            "direction": "ingress",
            "ip_version": 6,
            "is_public": False,
            "service_name": None,
            "network_name": "default",
            "network_organization_slug": "personal",
        },
        {
            "id": f"{TEST_APP_ID}/66.241.124.236",
            "address": "66.241.124.236",
            "type": "shared_v4",
            "region": None,
            "created_at": None,
            "direction": "ingress",
            "ip_version": 4,
            "is_public": True,
            "service_name": None,
            "network_name": None,
            "network_organization_slug": None,
        },
        {
            "id": "egress_v4_id",
            "address": "66.241.125.42",
            "type": "egress_v4",
            "region": "lhr",
            "created_at": "2026-07-31T09:12:00Z",
            "direction": "egress",
            "ip_version": 4,
            "is_public": True,
            "service_name": None,
            "network_name": None,
            "network_organization_slug": None,
        },
    ]


def test_transform_users():
    # Act
    users = cartography.intel.flyio.users.transform(ORG_MEMBERS_RESPONSE)

    # Assert
    assert users == [
        {
            "id": "Re9RMq7mRleO0UyLAKpq",
            "name": None,
            "email": "jonathanfemi@example.com",
            "role": "ADMIN",
            "joined_at": "2025-02-21T17:12:43Z",
        },
    ]


def test_transform_access_tokens():
    # Act
    app_tokens = cartography.intel.flyio.access_tokens.transform_app_tokens(
        APP_ACCESS_TOKENS_RESPONSE,
    )
    org_tokens = cartography.intel.flyio.access_tokens.transform_organization_tokens(
        ORG_ACCESS_TOKENS_RESPONSE,
    )

    # Assert
    assert app_tokens == [
        {
            "id": "app_token_active",
            "name": "FLY_API_TOKEN",
            "expires_at": "2125-01-30T16:38:02Z",
            "revoked_at": None,
            "user_id": "Re9RMq7mRleO0UyLAKpq",
            "user_name": None,
            "user_email": "jonathanfemi@example.com",
            "revoked": False,
        },
        {
            "id": "app_token_revoked",
            "name": "flyctl deploy token",
            "expires_at": "2045-02-18T16:30:33Z",
            "revoked_at": "2025-02-23T16:34:00Z",
            "user_id": "Re9RMq7mRleO0UyLAKpq",
            "user_name": None,
            "user_email": "jonathanfemi@example.com",
            "revoked": True,
        },
    ]
    assert org_tokens[0] == {
        "id": "org_token_active",
        "name": "cartography-flyio-prod-test",
        "expires_at": "2026-08-01T13:17:36Z",
        "revoked_at": None,
        "user_id": "Re9RMq7mRleO0UyLAKpq",
        "user_name": None,
        "user_email": "jonathanfemi@example.com",
        "revoked": False,
    }


def test_transform_releases():
    # Act
    releases = cartography.intel.flyio.releases.transform(RELEASES_RESPONSE)

    # Assert
    assert releases == [
        {
            "id": "YgoYklRLL8Xo3fBPg6AoX28AG",
            "version": 35,
            "stable": True,
            "in_progress": False,
            "reason": "deploy",
            "description": "Deploy image",
            "status": "succeeded",
            "deployment_strategy": "rolling",
            "evaluation_id": "eval_01KJQC1W6NXAK34WQ739F0ERSP",
            "created_at": "2026-07-31T06:40:00Z",
            "image_ref": (
                "registry.fly.io/nhmhvxo3b9:"
                "deployment-01JMWNHS84ZCCV89XYH9SQ48FX"
            ),
            "user_id": "user_123",
            "user_name": "Jonathan Femi",
            "user_email": "jonathanfemi@example.com",
        },
        {
            "id": "release_previous",
            "version": 34,
            "stable": False,
            "in_progress": False,
            "reason": "secrets",
            "description": "Update secrets",
            "status": "failed",
            "deployment_strategy": "immediate",
            "evaluation_id": None,
            "created_at": "2026-07-30T06:40:00Z",
            "image_ref": None,
            "user_id": None,
            "user_name": None,
            "user_email": None,
        },
    ]


@patch.object(cartography.intel.flyio.users, "post_graphql")
def test_get_users_uses_graphql(mock_post_graphql):
    # Arrange
    api_session = Mock()
    mock_post_graphql.return_value = ORG_MEMBERS_RESPONSE

    # Act
    response = cartography.intel.flyio.users.get(
        api_session,
        "https://api.fly.io/graphql",
        "personal",
    )

    # Assert
    assert response == ORG_MEMBERS_RESPONSE
    mock_post_graphql.assert_called_once_with(
        api_session,
        "https://api.fly.io/graphql",
        cartography.intel.flyio.users.FLY_ORG_MEMBERS_QUERY,
        {"slug": "personal"},
    )


@patch.object(cartography.intel.flyio.access_tokens, "post_graphql")
def test_get_access_tokens_uses_graphql(mock_post_graphql):
    # Arrange
    api_session = Mock()
    mock_post_graphql.side_effect = [
        ORG_ACCESS_TOKENS_RESPONSE,
        APP_ACCESS_TOKENS_RESPONSE,
    ]

    # Act
    org_response = cartography.intel.flyio.access_tokens.get_organization(
        api_session,
        "https://api.fly.io/graphql",
        "personal",
    )
    app_response = cartography.intel.flyio.access_tokens.get_app(
        api_session,
        "https://api.fly.io/graphql",
        "example-app",
    )

    # Assert
    assert org_response == ORG_ACCESS_TOKENS_RESPONSE
    assert app_response == APP_ACCESS_TOKENS_RESPONSE
    assert mock_post_graphql.call_args_list[0].args == (
        api_session,
        "https://api.fly.io/graphql",
        cartography.intel.flyio.access_tokens.FLY_ORG_ACCESS_TOKENS_QUERY,
        {"slug": "personal"},
    )
    assert mock_post_graphql.call_args_list[1].args == (
        api_session,
        "https://api.fly.io/graphql",
        cartography.intel.flyio.access_tokens.FLY_APP_ACCESS_TOKENS_QUERY,
        {"appName": "example-app"},
    )


@patch.object(cartography.intel.flyio.releases, "post_graphql")
def test_get_releases_uses_graphql(mock_post_graphql):
    # Arrange
    api_session = Mock()
    mock_post_graphql.return_value = RELEASES_RESPONSE

    # Act
    response = cartography.intel.flyio.releases.get(
        api_session,
        "https://api.fly.io/graphql",
        "example-app",
    )

    # Assert
    assert response == RELEASES_RESPONSE
    mock_post_graphql.assert_called_once_with(
        api_session,
        "https://api.fly.io/graphql",
        cartography.intel.flyio.releases.FLY_RELEASES_QUERY,
        {"appName": "example-app", "limit": 100, "after": None},
    )


@patch.object(cartography.intel.flyio.releases, "post_graphql")
def test_get_releases_follows_next_cursor(mock_post_graphql):
    # Arrange
    api_session = Mock()
    mock_post_graphql.side_effect = [
        {
            "app": {
                "releases": {
                    "nodes": [{"id": "release_1"}],
                    "pageInfo": {
                        "hasNextPage": True,
                        "endCursor": "cursor-1",
                    },
                },
            },
        },
        {
            "app": {
                "releases": {
                    "nodes": [{"id": "release_2"}],
                    "pageInfo": {
                        "hasNextPage": False,
                        "endCursor": None,
                    },
                },
            },
        },
    ]

    # Act
    response = cartography.intel.flyio.releases.get(
        api_session,
        "https://api.fly.io/graphql",
        "example-app",
    )

    # Assert
    assert response == {
        "app": {
            "releases": {
                "nodes": [{"id": "release_1"}, {"id": "release_2"}],
            },
        },
    }
    assert mock_post_graphql.call_args_list[0].args == (
        api_session,
        "https://api.fly.io/graphql",
        cartography.intel.flyio.releases.FLY_RELEASES_QUERY,
        {"appName": "example-app", "limit": 100, "after": None},
    )
    assert mock_post_graphql.call_args_list[1].args == (
        api_session,
        "https://api.fly.io/graphql",
        cartography.intel.flyio.releases.FLY_RELEASES_QUERY,
        {"appName": "example-app", "limit": 100, "after": "cursor-1"},
    )


@patch.object(cartography.intel.flyio.ips, "post_graphql")
def test_get_ips_uses_graphql(mock_post_graphql):
    # Arrange
    api_session = Mock()
    mock_post_graphql.return_value = IPS_RESPONSE

    # Act
    response = cartography.intel.flyio.ips.get(
        api_session,
        "https://api.fly.io/graphql",
        "example-app",
    )

    # Assert
    assert response == IPS_RESPONSE
    mock_post_graphql.assert_called_once_with(
        api_session,
        "https://api.fly.io/graphql",
        cartography.intel.flyio.ips.FLY_IPS_QUERY,
        {"appName": "example-app"},
    )


@patch.object(cartography.intel.flyio.certificates, "get_json")
def test_get_certificates_follows_next_cursor(mock_get_json):
    # Arrange
    api_session = Mock()
    mock_get_json.side_effect = [
        {
            "certificates": [
                {"hostname": "www.example.com"},
            ],
            "next_cursor": "page-2",
            "total_count": 2,
        },
        {
            "certificates": [
                {"hostname": "api.example.com"},
            ],
            "total_count": 2,
        },
    ]

    # Act
    response = cartography.intel.flyio.certificates.get(
        api_session,
        "https://api.machines.dev",
        "example-app",
    )

    # Assert
    assert response == {
        "certificates": [
            {"hostname": "www.example.com"},
            {"hostname": "api.example.com"},
        ],
        "total_count": 2,
    }
    assert mock_get_json.call_args_list[0].kwargs == {}
    assert mock_get_json.call_args_list[1].kwargs == {"cursor": "page-2"}
