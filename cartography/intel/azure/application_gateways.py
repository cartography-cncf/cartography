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
from cartography.models.azure.application_gateway.application_gateway_backend_http_settings import (
    AzureApplicationGatewayBackendHTTPSettingsSchema,
)
from cartography.models.azure.application_gateway.application_gateway_backend_pool import (
    AzureApplicationGatewayBackendPoolSchema,
)
from cartography.models.azure.application_gateway.application_gateway_frontend_ip import (
    AzureApplicationGatewayFrontendIPSchema,
)
from cartography.models.azure.application_gateway.application_gateway_http_listener import (
    AzureApplicationGatewayHTTPListenerSchema,
)
from cartography.models.azure.application_gateway.application_gateway_request_routing_rule import (
    AzureApplicationGatewayRequestRoutingRuleSchema,
)
from cartography.models.azure.tags.application_gateway_tag import (
    AzureApplicationGatewayTagsSchema,
)
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def _get(obj: dict, key: str) -> Any:
    """
    Read a field that the Azure SDK may emit either at the top level of the dict
    or nested under "properties".
    """
    if key in obj:
        return obj.get(key)
    return obj.get("properties", {}).get(key)


def _first_subnet_id(application_gateway: dict) -> str | None:
    for cfg in application_gateway.get("gateway_ip_configurations", []) or []:
        subnet = cfg.get("subnet") or cfg.get("properties", {}).get("subnet") or {}
        subnet_id = subnet.get("id")
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
        sku = ag.get("sku") or {}
        firewall_policy = (
            ag.get("firewall_policy")
            or ag.get("properties", {}).get("firewall_policy")
            or {}
        )
        transformed.append(
            {
                "id": ag.get("id"),
                "name": ag.get("name"),
                "location": ag.get("location"),
                "sku_name": sku.get("name"),
                "sku_tier": sku.get("tier"),
                "sku_capacity": sku.get("capacity"),
                "operational_state": _get(ag, "operational_state"),
                "provisioning_state": _get(ag, "provisioning_state"),
                "enable_http2": _get(ag, "enable_http2"),
                "firewall_policy_id": firewall_policy.get("id"),
                "subnet_id": _first_subnet_id(ag),
                "tags": ag.get("tags"),
            }
        )
    return transformed


def transform_frontend_ips(application_gateway: dict) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for config in application_gateway.get("frontend_ip_configurations", []) or []:
        public_ip_ref = (
            config.get("public_ip_address")
            or config.get("properties", {}).get("public_ip_address")
            or {}
        )
        subnet_ref = (
            config.get("subnet") or config.get("properties", {}).get("subnet") or {}
        )
        transformed.append(
            {
                "id": config.get("id"),
                "name": config.get("name"),
                "private_ip_address": _get(config, "private_ip_address"),
                "private_ip_allocation_method": _get(
                    config, "private_ip_allocation_method"
                ),
                "public_ip_address_id": public_ip_ref.get("id"),
                "subnet_id": subnet_ref.get("id"),
            }
        )
    return transformed


def transform_backend_pools(application_gateway: dict) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for pool in application_gateway.get("backend_address_pools", []) or []:
        backend_addresses = (
            pool.get("backend_addresses")
            or pool.get("properties", {}).get("backend_addresses")
            or []
        )
        fqdns = [a.get("fqdn") for a in backend_addresses if a.get("fqdn")]
        ip_addresses = [
            a.get("ip_address") for a in backend_addresses if a.get("ip_address")
        ]

        nic_ids: list[str] = []
        ip_configs = (
            pool.get("backend_ip_configurations")
            or pool.get("properties", {}).get("backend_ip_configurations")
            or []
        )
        for ip_config in ip_configs:
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
    for port in application_gateway.get("frontend_ports", []) or []:
        port_id = port.get("id")
        if port_id:
            lookup[port_id] = _get(port, "port")
    return lookup


def transform_http_listeners(application_gateway: dict) -> list[dict]:
    port_lookup = _build_frontend_port_lookup(application_gateway)
    transformed: list[dict[str, Any]] = []
    for listener in application_gateway.get("http_listeners", []) or []:
        frontend_ip_ref = (
            listener.get("frontend_ip_configuration")
            or listener.get("properties", {}).get("frontend_ip_configuration")
            or {}
        )
        frontend_port_ref = (
            listener.get("frontend_port")
            or listener.get("properties", {}).get("frontend_port")
            or {}
        )
        ssl_cert_ref = (
            listener.get("ssl_certificate")
            or listener.get("properties", {}).get("ssl_certificate")
            or {}
        )
        frontend_port_id = frontend_port_ref.get("id")
        transformed.append(
            {
                "id": listener.get("id"),
                "name": listener.get("name"),
                "protocol": _get(listener, "protocol"),
                "frontend_port": (
                    port_lookup.get(frontend_port_id) if frontend_port_id else None
                ),
                "host_name": _get(listener, "host_name"),
                "host_names": _get(listener, "host_names"),
                "require_server_name_indication": _get(
                    listener, "require_server_name_indication"
                ),
                "ssl_certificate_id": ssl_cert_ref.get("id"),
                "FRONTEND_IP_ID": frontend_ip_ref.get("id"),
            }
        )
    return transformed


def transform_backend_http_settings(application_gateway: dict) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for settings in (
        application_gateway.get("backend_http_settings_collection", []) or []
    ):
        transformed.append(
            {
                "id": settings.get("id"),
                "name": settings.get("name"),
                "protocol": _get(settings, "protocol"),
                "port": _get(settings, "port"),
                "cookie_based_affinity": _get(settings, "cookie_based_affinity"),
                "request_timeout": _get(settings, "request_timeout"),
                "host_name": _get(settings, "host_name"),
                "pick_host_name_from_backend_address": _get(
                    settings, "pick_host_name_from_backend_address"
                ),
            }
        )
    return transformed


def _build_url_path_map_lookup(
    application_gateway: dict,
) -> dict[str, dict[str, str | None]]:
    """
    Build a lookup of url_path_map id -> default backend pool / settings ids.

    PathBasedRouting rules carry their effective backend through a `url_path_map`
    rather than directly on the rule, so we resolve the path map's defaults to keep
    the rule node's `ROUTES_TO` / `USES_SETTINGS` edges populated.
    """
    lookup: dict[str, dict[str, str | None]] = {}
    for path_map in application_gateway.get("url_path_maps", []) or []:
        path_map_id = path_map.get("id")
        if not path_map_id:
            continue
        default_pool = (
            path_map.get("default_backend_address_pool")
            or path_map.get("properties", {}).get("default_backend_address_pool")
            or {}
        )
        default_settings = (
            path_map.get("default_backend_http_settings")
            or path_map.get("properties", {}).get("default_backend_http_settings")
            or {}
        )
        lookup[path_map_id] = {
            "backend_pool_id": default_pool.get("id"),
            "backend_http_settings_id": default_settings.get("id"),
        }
    return lookup


def transform_request_routing_rules(application_gateway: dict) -> list[dict]:
    path_map_lookup = _build_url_path_map_lookup(application_gateway)
    transformed: list[dict[str, Any]] = []
    for rule in application_gateway.get("request_routing_rules", []) or []:
        listener_ref = (
            rule.get("http_listener")
            or rule.get("properties", {}).get("http_listener")
            or {}
        )
        backend_pool_ref = (
            rule.get("backend_address_pool")
            or rule.get("properties", {}).get("backend_address_pool")
            or {}
        )
        backend_settings_ref = (
            rule.get("backend_http_settings")
            or rule.get("properties", {}).get("backend_http_settings")
            or {}
        )
        url_path_map_ref = (
            rule.get("url_path_map")
            or rule.get("properties", {}).get("url_path_map")
            or {}
        )

        backend_pool_id = backend_pool_ref.get("id")
        backend_http_settings_id = backend_settings_ref.get("id")
        # PathBasedRouting: fall back to the url_path_map's defaults when the rule
        # has no direct backend pool / settings.
        url_path_map_id = url_path_map_ref.get("id")
        if url_path_map_id and url_path_map_id in path_map_lookup:
            defaults = path_map_lookup[url_path_map_id]
            if not backend_pool_id:
                backend_pool_id = defaults.get("backend_pool_id")
            if not backend_http_settings_id:
                backend_http_settings_id = defaults.get("backend_http_settings_id")

        transformed.append(
            {
                "id": rule.get("id"),
                "name": rule.get("name"),
                "rule_type": _get(rule, "rule_type"),
                "priority": _get(rule, "priority"),
                "url_path_map_id": url_path_map_id,
                "HTTP_LISTENER_ID": listener_ref.get("id"),
                "BACKEND_POOL_ID": backend_pool_id,
                "BACKEND_HTTP_SETTINGS_ID": backend_http_settings_id,
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
def load_http_listeners(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    application_gateway_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureApplicationGatewayHTTPListenerSchema(),
        data,
        lastupdated=update_tag,
        APPLICATION_GATEWAY_ID=application_gateway_id,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_backend_http_settings(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    application_gateway_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureApplicationGatewayBackendHTTPSettingsSchema(),
        data,
        lastupdated=update_tag,
        APPLICATION_GATEWAY_ID=application_gateway_id,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_request_routing_rules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    application_gateway_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureApplicationGatewayRequestRoutingRuleSchema(),
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

        http_listeners = transform_http_listeners(ag)
        load_http_listeners(
            neo4j_session, http_listeners, ag_id, subscription_id, update_tag
        )

        backend_http_settings = transform_backend_http_settings(ag)
        load_backend_http_settings(
            neo4j_session,
            backend_http_settings,
            ag_id,
            subscription_id,
            update_tag,
        )

        rules = transform_request_routing_rules(ag)
        load_request_routing_rules(
            neo4j_session, rules, ag_id, subscription_id, update_tag
        )

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
        AzureApplicationGatewayHTTPListenerSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        AzureApplicationGatewayBackendHTTPSettingsSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        AzureApplicationGatewayRequestRoutingRuleSchema(), common_job_parameters
    ).run(neo4j_session)

    GraphJob.from_node_schema(
        AzureApplicationGatewaySchema(), common_job_parameters
    ).run(neo4j_session)
    cleanup_application_gateway_tags(neo4j_session, common_job_parameters)
