import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.flyio.util import get_json
from cartography.intel.flyio.util import require_non_empty
from cartography.models.flyio.machine import FlyMachineSchema
from cartography.models.flyio.service import FlyMachineServicePortSchema
from cartography.models.flyio.service import FlyMachineServiceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    machines = get(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["APP_NAME"],
    )
    transformed_machines = transform_machines(machines)
    services = transform_services(machines)
    service_ports = transform_service_ports(machines)

    load_machines(
        neo4j_session,
        transformed_machines,
        common_job_parameters["APP_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    load_services(
        neo4j_session,
        services,
        common_job_parameters["APP_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    load_service_ports(
        neo4j_session,
        service_ports,
        common_job_parameters["APP_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return transformed_machines


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    app_name: str,
) -> list[dict[str, Any]]:
    return get_json(
        api_session,
        f"{base_url}/v1/apps/{app_name}/machines",
        include_deleted=False,
    )


def transform_machines(machines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for machine in machines:
        machine_id = require_non_empty(machine["id"], "machine id")
        config = machine.get("config") or {}
        guest = config.get("guest") or {}
        restart = config.get("restart") or {}
        metadata = config.get("metadata") or {}
        image_ref = machine.get("image_ref") or {}
        result.append(
            {
                "id": machine_id,
                "name": machine.get("name"),
                "state": machine.get("state"),
                "region": machine.get("region"),
                "instance_id": machine.get("instance_id"),
                "private_ip": machine.get("private_ip"),
                "image": config.get("image"),
                "image_registry": image_ref.get("registry"),
                "image_repository": image_ref.get("repository"),
                "image_tag": image_ref.get("tag"),
                "image_digest": image_ref.get("digest"),
                "cpu_kind": guest.get("cpu_kind"),
                "cpus": guest.get("cpus"),
                "memory_mb": guest.get("memory_mb"),
                "restart_policy": restart.get("policy"),
                "restart_max_retries": restart.get("max_retries"),
                "process_group": metadata.get("fly_process_group"),
                "release_id": metadata.get("fly_release_id"),
                "release_version": metadata.get("fly_release_version"),
                "host_status": machine.get("host_status"),
                "cordoned": machine.get("cordoned"),
                "created_at": machine.get("created_at"),
                "updated_at": machine.get("updated_at"),
            }
        )
    return result


def transform_services(machines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    services = []
    for machine in machines:
        machine_id = require_non_empty(machine["id"], "machine id")
        config = machine.get("config") or {}
        for service in config.get("services") or []:
            protocol = require_non_empty(service["protocol"], "service protocol")
            internal_port = require_non_empty(
                service["internal_port"],
                "service internal_port",
            )
            service_id = f"{machine_id}/{protocol}/{internal_port}"
            services.append(
                {
                    "id": service_id,
                    "protocol": protocol,
                    "internal_port": internal_port,
                    "autostop": service.get("autostop"),
                    "autostart": service.get("autostart"),
                    "min_machines_running": service.get("min_machines_running"),
                    "force_instance_key": service.get("force_instance_key"),
                    "machine_id": machine_id,
                }
            )
    return services


def transform_service_ports(machines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ports = []
    for machine in machines:
        machine_id = require_non_empty(machine["id"], "machine id")
        config = machine.get("config") or {}
        for service in config.get("services") or []:
            protocol = require_non_empty(service["protocol"], "service protocol")
            internal_port = require_non_empty(
                service["internal_port"],
                "service internal_port",
            )
            service_id = f"{machine_id}/{protocol}/{internal_port}"
            for port in service.get("ports") or []:
                external_port = port.get("port")
                start_port = port.get("start_port")
                end_port = port.get("end_port")
                if external_port is not None:
                    port_id_suffix = require_non_empty(
                        external_port,
                        "service external port",
                    )
                else:
                    start_port = require_non_empty(
                        start_port,
                        "service external start_port",
                    )
                    end_port = require_non_empty(
                        end_port,
                        "service external end_port",
                    )
                    port_id_suffix = f"{start_port}-{end_port}"
                ports.append(
                    {
                        "id": f"{service_id}/{port_id_suffix}",
                        "port": external_port,
                        "start_port": start_port,
                        "end_port": end_port,
                        "handlers": port.get("handlers"),
                        "force_https": port.get("force_https"),
                        "service_id": service_id,
                    }
                )
    return ports


@timeit
def load_machines(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    app_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FlyMachineSchema(),
        data,
        lastupdated=update_tag,
        APP_ID=app_id,
    )


@timeit
def load_services(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    app_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FlyMachineServiceSchema(),
        data,
        lastupdated=update_tag,
        APP_ID=app_id,
    )


@timeit
def load_service_ports(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    app_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FlyMachineServicePortSchema(),
        data,
        lastupdated=update_tag,
        APP_ID=app_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FlyMachineServicePortSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(FlyMachineServiceSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(FlyMachineSchema(), common_job_parameters).run(
        neo4j_session,
    )
