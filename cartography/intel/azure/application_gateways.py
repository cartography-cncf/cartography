import logging
from typing import Any

import neo4j
from azure.mgmt.network import NetworkManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.azure.util.tag import transform_tags
from cartography.models.azure.application_gateway.application_gateway import (
    AzureApplicationGatewaySchema,
)
from cartography.models.azure.application_gateway.application_gateway_backend_pool import (
    AzureApplicationGatewayBackendPoolSchema,
)
from cartography.models.azure.application_gateway.application_gateway_frontend_ip import (
    AzureApplicationGatewayFrontendIPSchema,
)
from cartography.models.azure.application_gateway.application_gateway_rule import (
    AzureApplicationGatewayRuleSchema,
)
from cartography.models.azure.tags.application_gateway_tag import (
    AzureApplicationGatewayTagsSchema,
)
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def _get(obj: dict, *keys: str) -> Any:
    """
    Read a field by any of its spellings. Older Azure SDKs flatten `as_dict()` into
    snake_case keys; azure-mgmt-network 31+ emits the ARM wire shape, with camelCase
    keys nested under "properties".
    """
    properties = obj.get("properties") or {}
    for key in keys:
        if key in obj:
            return obj[key]
        if key in properties:
            return properties[key]
    return None


def _get_list(obj: dict, *keys: str) -> list[dict]:
    return _get(obj, *keys) or []


def _ref_id(obj: dict, *keys: str) -> str | None:
    return (_get(obj, *keys) or {}).get("id")


def _first_subnet_id(application_gateway: dict) -> str | None:
    for cfg in _get_list(
        application_gateway, "gateway_ip_configurations", "gatewayIPConfigurations"
    ):
        subnet_id = _ref_id(cfg, "subnet")
        if subnet_id:
            return subnet_id
    return None


@timeit
def get_application_gateways(client: NetworkManagementClient) -> list[dict]:
    """
    Get a list of all Application Gateways in a subscription.
    """
    return [ag.as_dict() for ag in client.application_gateways.list_all()]


def transform_application_gateways(application_gateways: list[dict]) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for ag in application_gateways:
        sku = _get(ag, "sku") or {}
        transformed.append(
            {
                "id": ag.get("id"),
                "name": ag.get("name"),
                "location": ag.get("location"),
                "sku_name": sku.get("name"),
                "sku_tier": sku.get("tier"),
                "sku_capacity": sku.get("capacity"),
                "operational_state": _get(ag, "operational_state", "operationalState"),
                "provisioning_state": _get(
                    ag, "provisioning_state", "provisioningState"
                ),
                "enable_http2": _get(ag, "enable_http2", "enableHttp2"),
                "firewall_policy_id": _ref_id(ag, "firewall_policy", "firewallPolicy"),
                "subnet_id": _first_subnet_id(ag),
                "tags": ag.get("tags"),
            }
        )
    return transformed


def transform_frontend_ips(application_gateway: dict) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for config in _get_list(
        application_gateway, "frontend_ip_configurations", "frontendIPConfigurations"
    ):
        transformed.append(
            {
                "id": config.get("id"),
                "name": config.get("name"),
                "private_ip_address": _get(
                    config, "private_ip_address", "privateIPAddress"
                ),
                "private_ip_allocation_method": _get(
                    config,
                    "private_ip_allocation_method",
                    "privateIPAllocationMethod",
                ),
                "public_ip_address_id": _ref_id(
                    config, "public_ip_address", "publicIPAddress"
                ),
                "subnet_id": _ref_id(config, "subnet"),
            }
        )
    return transformed


def transform_backend_pools(application_gateway: dict) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for pool in _get_list(
        application_gateway, "backend_address_pools", "backendAddressPools"
    ):
        backend_addresses = _get_list(pool, "backend_addresses", "backendAddresses")
        fqdns = [a["fqdn"] for a in backend_addresses if a.get("fqdn")]
        ip_addresses = [
            ip for a in backend_addresses if (ip := _get(a, "ip_address", "ipAddress"))
        ]

        nic_ids: list[str] = []
        for ip_config in _get_list(
            pool, "backend_ip_configurations", "backendIPConfigurations"
        ):
            ip_config_id = ip_config.get("id")
            # NIC ID is the parent of the ipConfiguration:
            # /.../networkInterfaces/{nic-name}/ipConfigurations/{config-name}
            if ip_config_id and "/ipConfigurations/" in ip_config_id:
                nic_ids.append(ip_config_id.split("/ipConfigurations/")[0])

        transformed.append(
            {
                "id": pool.get("id"),
                "name": pool.get("name"),
                "fqdns": fqdns,
                "ip_addresses": ip_addresses,
                "NIC_IDS": nic_ids,
            }
        )
    return transformed


def _build_frontend_port_lookup(application_gateway: dict) -> dict[str, int | None]:
    lookup: dict[str, int | None] = {}
    for port in _get_list(application_gateway, "frontend_ports", "frontendPorts"):
        port_id = port.get("id")
        if port_id:
            lookup[port_id] = _get(port, "port")
    return lookup


def _build_listener_lookup(
    application_gateway: dict,
) -> dict[str, dict[str, Any]]:
    """
    Build a lookup of listener id -> flattened listener attributes plus the
    frontend IP id it references. Used to fold listener data onto the Rule node.
    """
    port_lookup = _build_frontend_port_lookup(application_gateway)
    lookup: dict[str, dict[str, Any]] = {}
    for listener in _get_list(application_gateway, "http_listeners", "httpListeners"):
        listener_id = listener.get("id")
        if not listener_id:
            continue
        frontend_port_id = _ref_id(listener, "frontend_port", "frontendPort")
        lookup[listener_id] = {
            "listener_protocol": _get(listener, "protocol"),
            "listener_port": (
                port_lookup.get(frontend_port_id) if frontend_port_id else None
            ),
            "listener_host_name": _get(listener, "host_name", "hostName"),
            "listener_host_names": _get(listener, "host_names", "hostNames"),
            "listener_require_server_name_indication": _get(
                listener,
                "require_server_name_indication",
                "requireServerNameIndication",
            ),
            "listener_ssl_certificate_id": _ref_id(
                listener, "ssl_certificate", "sslCertificate"
            ),
            "FRONTEND_IP_ID": _ref_id(
                listener, "frontend_ip_configuration", "frontendIPConfiguration"
            ),
        }
    return lookup


def _build_backend_http_settings_lookup(
    application_gateway: dict,
) -> dict[str, dict[str, Any]]:
    """
    Build a lookup of backend http settings id -> flattened settings attributes.
    Used to fold settings data onto the Rule node.
    """
    lookup: dict[str, dict[str, Any]] = {}
    for settings in _get_list(
        application_gateway,
        "backend_http_settings_collection",
        "backendHttpSettingsCollection",
    ):
        settings_id = settings.get("id")
        if not settings_id:
            continue
        lookup[settings_id] = {
            "backend_protocol": _get(settings, "protocol"),
            "backend_port": _get(settings, "port"),
            "backend_cookie_based_affinity": _get(
                settings, "cookie_based_affinity", "cookieBasedAffinity"
            ),
            "backend_request_timeout": _get(
                settings, "request_timeout", "requestTimeout"
            ),
            "backend_host_name": _get(settings, "host_name", "hostName"),
            "backend_pick_host_name_from_backend_address": _get(
                settings,
                "pick_host_name_from_backend_address",
                "pickHostNameFromBackendAddress",
            ),
        }
    return lookup


def transform_rules(application_gateway: dict) -> list[dict]:
    """
    Flatten request_routing_rules with their referenced HTTP listener and
    backend HTTP settings into a single record per rule, parallel to how
    AzureLoadBalancerRule carries protocol / frontend_port / backend_port.

    PathBasedRouting rules route to a `url_path_map` whose individual path rules
    can target different backend pools / settings. Resolving only the map's
    defaults would misrepresent the routing topology, so we keep `url_path_map_id`
    as a property pointer and skip the `ROUTES_TO` / backend_* fields for those
    rules until path rules are modelled explicitly.
    """
    listener_lookup = _build_listener_lookup(application_gateway)
    settings_lookup = _build_backend_http_settings_lookup(application_gateway)

    empty_listener: dict[str, Any] = {
        "listener_protocol": None,
        "listener_port": None,
        "listener_host_name": None,
        "listener_host_names": None,
        "listener_require_server_name_indication": None,
        "listener_ssl_certificate_id": None,
        "FRONTEND_IP_ID": None,
    }
    empty_settings: dict[str, Any] = {
        "backend_protocol": None,
        "backend_port": None,
        "backend_cookie_based_affinity": None,
        "backend_request_timeout": None,
        "backend_host_name": None,
        "backend_pick_host_name_from_backend_address": None,
    }

    transformed: list[dict[str, Any]] = []
    for rule in _get_list(
        application_gateway, "request_routing_rules", "requestRoutingRules"
    ):
        listener_id = _ref_id(rule, "http_listener", "httpListener")
        backend_pool_id = _ref_id(rule, "backend_address_pool", "backendAddressPool")
        backend_http_settings_id = _ref_id(
            rule, "backend_http_settings", "backendHttpSettings"
        )
        url_path_map_id = _ref_id(rule, "url_path_map", "urlPathMap")

        listener_attrs = (
            listener_lookup.get(listener_id, empty_listener)
            if listener_id
            else empty_listener
        )
        settings_attrs = (
            settings_lookup.get(backend_http_settings_id, empty_settings)
            if backend_http_settings_id
            else empty_settings
        )

        transformed.append(
            {
                "id": rule.get("id"),
                "name": rule.get("name"),
                "rule_type": _get(rule, "rule_type", "ruleType"),
                "priority": _get(rule, "priority"),
                "url_path_map_id": url_path_map_id,
                "listener_id": listener_id,
                "backend_http_settings_id": backend_http_settings_id,
                "BACKEND_POOL_ID": backend_pool_id,
                **listener_attrs,
                **settings_attrs,
            }
        )
    return transformed


@timeit
def load_application_gateways(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureApplicationGatewaySchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_frontend_ips(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    application_gateway_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureApplicationGatewayFrontendIPSchema(),
        data,
        lastupdated=update_tag,
        APPLICATION_GATEWAY_ID=application_gateway_id,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_backend_pools(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    application_gateway_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureApplicationGatewayBackendPoolSchema(),
        data,
        lastupdated=update_tag,
        APPLICATION_GATEWAY_ID=application_gateway_id,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_rules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    application_gateway_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureApplicationGatewayRuleSchema(),
        data,
        lastupdated=update_tag,
        APPLICATION_GATEWAY_ID=application_gateway_id,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_application_gateway_tags(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    application_gateways: list[dict],
    update_tag: int,
) -> None:
    """
    Loads tags for Application Gateways.
    """
    tags = transform_tags(application_gateways, subscription_id)
    load(
        neo4j_session,
        AzureApplicationGatewayTagsSchema(),
        tags,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup_application_gateway_tags(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Runs cleanup job for Azure Application Gateway tags.
    """
    GraphJob.from_node_schema(
        AzureApplicationGatewayTagsSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(
        f"Syncing Azure Application Gateways for subscription {subscription_id}.",
    )
    client = NetworkManagementClient(credentials.credential, subscription_id)

    application_gateways = get_application_gateways(client)
    transformed_ags = transform_application_gateways(application_gateways)
    load_application_gateways(
        neo4j_session, transformed_ags, subscription_id, update_tag
    )
    load_application_gateway_tags(
        neo4j_session, subscription_id, transformed_ags, update_tag
    )

    for ag in application_gateways:
        ag_id = ag["id"]

        frontend_ips = transform_frontend_ips(ag)
        load_frontend_ips(
            neo4j_session, frontend_ips, ag_id, subscription_id, update_tag
        )

        backend_pools = transform_backend_pools(ag)
        load_backend_pools(
            neo4j_session, backend_pools, ag_id, subscription_id, update_tag
        )

        rules = transform_rules(ag)
        load_rules(neo4j_session, rules, ag_id, subscription_id, update_tag)

    # Run cleanup for child components and the parent at subscription scope (their
    # sub_resource_relationship is the AzureSubscription). Running this *outside*
    # the loop ensures we still purge stale child nodes when every gateway has been
    # deleted from Azure between syncs and the loop never executes.
    GraphJob.from_node_schema(
        AzureApplicationGatewayFrontendIPSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        AzureApplicationGatewayBackendPoolSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        AzureApplicationGatewayRuleSchema(), common_job_parameters
    ).run(neo4j_session)

    GraphJob.from_node_schema(
        AzureApplicationGatewaySchema(), common_job_parameters
    ).run(neo4j_session)
    cleanup_application_gateway_tags(neo4j_session, common_job_parameters)
