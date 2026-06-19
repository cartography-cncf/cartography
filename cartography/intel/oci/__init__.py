# Copyright (c) 2020, Oracle and/or its affiliates.
import base64
import json
import logging
import time
from collections import namedtuple
from typing import Any
from typing import Dict
from typing import List

import neo4j
import oci
import oci.artifacts
import oci.key_management
import oci.logging
import oci.monitoring
from oci.exceptions import ConfigFileNotFound
from oci.exceptions import InvalidConfig
from oci.exceptions import ProfileNotFound

from . import compartment
from . import iam
from . import organizations
from . import storage
from . import utils
from .resources import RESOURCE_FUNCTIONS
from cartography.config import Config
from cartography.intel.oci.util.common import parse_and_validate_oci_requested_syncs
# from cartography.util import run_analysis_job
# from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)
Resources = namedtuple('Resources', 'compute iam network storage oke monitoring encryption logging containerregistry')


def _sync_one_compartment(
    neo4j_session: neo4j.Session,
    resources: Resources,
    compartment_id: str,
    tenancy_id: str,
    requested_syncs: List[str],
    oci_sync_tag: int,
    common_job_parameters: Dict[str, Any],
    regions: List[str],
) -> None:
    """
    Sync requested services for a single OCI compartment.
    Similar to Azure's _sync_one_subscription.

    If this is the default compartment (compartment_id == tenancy_id), IAM is run first
    to populate regions. For child compartments, IAM is skipped.
    """
    _comp_tic = time.perf_counter()
    _service_timings: Dict = {}
    _failed_services: Dict = {}
    is_default_compartment = (compartment_id == tenancy_id)

    # For default compartment, run IAM first to populate regions
    if is_default_compartment and "iam" in requested_syncs:
        logger.info("Syncing OCI IAM for tenancy '%s'.", tenancy_id)
        _svc_tic = time.perf_counter()
        _svc_status = "success"
        _svc_err: Dict = {}
        try:
            iam.sync(
                neo4j_session, resources.iam, tenancy_id, oci_sync_tag,
                common_job_parameters, regions,
            )
            _svc_elapsed = round(time.perf_counter() - _svc_tic, 4)
            _service_timings["iam"] = _svc_elapsed
        except Exception as e:
            _svc_status = "error"
            _svc_elapsed = round(time.perf_counter() - _svc_tic, 4)
            _svc_err = {"error_type": type(e).__name__, "error_message": str(e)}
            _failed_services["iam"] = str(e)
            logger.error("Error syncing OCI IAM: %s", e, exc_info=True)
        finally:
            _ev: Dict = {
                "event": "oci_service_timing",
                "tenancy": tenancy_id,
                "compartment": compartment_id,
                "service": "iam",
                "duration_seconds": _svc_elapsed,
                "status": _svc_status,
            }
            if _svc_err:
                _ev.update(_svc_err)
            logger.info(json.dumps(_ev))

    # Get regions from neo4j (populated by IAM region subscriptions)
    updated_regions = [r["name"] for r in utils.get_regions_in_tenancy(neo4j_session, tenancy_id)]
    if updated_regions:
        regions = updated_regions

    # Run remaining resource syncs (skip IAM since it's already handled above)
    for func_name in requested_syncs:
        if func_name == "iam":
            continue
        if func_name in RESOURCE_FUNCTIONS:
            logger.info("Syncing OCI %s for compartment '%s'.", func_name, compartment_id)
            _svc_tic = time.perf_counter()
            _svc_status = "success"
            _svc_err = {}
            try:
                RESOURCE_FUNCTIONS[func_name](
                    neo4j_session, getattr(resources, func_name), tenancy_id, oci_sync_tag,
                    common_job_parameters, regions,
                )
                _svc_elapsed = round(time.perf_counter() - _svc_tic, 4)
                _service_timings[func_name] = _svc_elapsed
            except Exception as e:
                _svc_status = "error"
                _svc_elapsed = round(time.perf_counter() - _svc_tic, 4)
                _svc_err = {"error_type": type(e).__name__, "error_message": str(e)}
                _failed_services[func_name] = str(e)
                logger.error(
                    "Error syncing OCI %s for compartment '%s': %s", func_name, compartment_id, e, exc_info=True,
                )
            finally:
                _ev = {
                    "event": "oci_service_timing",
                    "tenancy": tenancy_id,
                    "compartment": compartment_id,
                    "service": func_name,
                    "duration_seconds": _svc_elapsed,
                    "status": _svc_status,
                }
                if _svc_err:
                    _ev.update(_svc_err)
                logger.info(json.dumps(_ev))
        else:
            logger.warning(
                'OCI sync function "%s" was specified but does not exist. Did you misspell it?', func_name,
            )
    logger.info(
        json.dumps({
            "event": "oci_compartment_timing_summary",
            "tenancy": tenancy_id,
            "compartment": compartment_id,
            "total_duration_seconds": round(time.perf_counter() - _comp_tic, 4),
            "service_timings": _service_timings,
            "slowest_service": max(_service_timings, key=_service_timings.get) if _service_timings else None,
            "failed_services": _failed_services,
        }),
    )


def _sync_multiple_compartments(
    neo4j_session: neo4j.Session,
    credentials: Dict[str, Any],
    tenancy_id: str,
    compartments: List[Dict[str, Any]],
    requested_syncs: List[str],
    sync_tag: int,
    common_job_parameters: Dict[str, Any],
    regions: List[str],
) -> None:
    """
    Sync OCI resources for the requested compartments.
    Similar to Azure's _sync_multiple_subscriptions.
    """
    logger.info("Syncing OCI compartments under tenancy '%s'.", tenancy_id)

    resources = _initialize_resources(credentials)

    common_job_parameters["OCI_TENANCY_ID"] = tenancy_id

    for comp in compartments:
        compartment_id = comp["compartmentId"]
        common_job_parameters["OCI_COMPARTMENT_ID"] = compartment_id

        logger.info(
            "Syncing OCI Compartment with ID '%s'.",
            compartment_id,
        )

        _sync_one_compartment(
            neo4j_session, resources, compartment_id, tenancy_id,
            requested_syncs, sync_tag, common_job_parameters, regions,
        )

        del common_job_parameters["OCI_COMPARTMENT_ID"]


def _get_network_resource(credentials: Dict[str, Any]) -> oci.core.virtual_network_client.VirtualNetworkClient:
    """
    Instantiates a OCI VirtualNetworkClient resource object to call the Network API.
     See https://docs.cloud.oracle.com/en-us/iaas/Content/Network/Concepts/overview.htm.
    :param credentials: OCI Credentials object
    :return: A VirtualNetworkClient resource object
    """
    return oci.core.VirtualNetworkClient(credentials)


def _get_iam_resource(credentials: Dict[str, Any]) -> oci.identity.identity_client.IdentityClient:
    """
    Instantiates a OCI IdentityCleint resource object to call the Identity API. This is used to users,
     ..., ... and ... data. See https://docs.cloud.oracle.com/iaas/Content/Compute/Concepts/computeoverview.htm.
    :param credentials: OCI Credentials object
    :return: A IdentityClient resource object
    """
    return oci.identity.IdentityClient(credentials)


def _get_compute_resource(credentials: Dict[str, Any]) -> oci.core.compute_client.ComputeClient:
    """
    Instantiates a OCI ComputeClient resource object to call the Compute API. This is used to pull zone, instance, and
    networking data. https://docs.cloud.oracle.com/iaas/Content/Compute/Concepts/computeoverview.htm.
    :param credentials: The OCI Credentials object
    :return: A ComputeClient resource object
    """
    return oci.core.ComputeClient(credentials)


def _get_encryption_resource(credentials: Dict[str, Any]) -> oci.key_management.KmsVaultClient:
    """
    Instantiates an OCI KmsVaultClient resource object to call the KMS Vault API.
    See https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm.
    :param credentials: OCI Credentials object
    :return: A KmsVaultClient resource object
    """
    return oci.key_management.KmsVaultClient(credentials)


def _get_monitoring_resource(credentials: Dict[str, Any]) -> oci.monitoring.MonitoringClient:
    """
    Instantiates an OCI MonitoringClient resource object to call the Monitoring API.
    See https://docs.oracle.com/en-us/iaas/Content/Monitoring/Concepts/monitoringoverview.htm.
    :param credentials: OCI Credentials object
    :return: A MonitoringClient resource object
    """
    return oci.monitoring.MonitoringClient(credentials)


def _get_logging_resource(credentials: Dict[str, Any]) -> oci.logging.LoggingManagementClient:
    """
    Instantiates an OCI LoggingManagementClient resource object to call the Logging API.
    Additional clients (Audit, Object Storage) are created internally by the sync
    function using this client's config/signer — same pattern as monitoring.py.
    See https://docs.oracle.com/en-us/iaas/Content/Logging/Concepts/loggingoverview.htm.
    :param credentials: OCI Credentials object
    :return: A LoggingManagementClient resource object
    """
    return oci.logging.LoggingManagementClient(credentials)


def _get_containerregistry_resource(credentials: Dict[str, Any]) -> oci.artifacts.ArtifactsClient:
    """
    Instantiates an OCI ArtifactsClient resource object to call the Container Registry API.
    See https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registryoverview.htm.
    :param credentials: OCI Credentials object
    :return: An ArtifactsClient resource object
    """
    return oci.artifacts.ArtifactsClient(credentials)


def _get_storage_resource(credentials: Dict[str, Any]) -> storage.OCIStorageClients:
    """
    Bundle the three OCI SDK clients used by the storage sync (Object Storage,
    Block Storage, File Storage) under a single attribute on the Resources
    namedtuple. The orchestrator addresses storage as one logical sync.
    :param credentials: The OCI Credentials object
    :return: A bundled OCIStorageClients container
    """
    return storage.OCIStorageClients(
        object_storage=oci.object_storage.ObjectStorageClient(credentials),
        blockstorage=oci.core.BlockstorageClient(credentials),
        file_storage=oci.file_storage.FileStorageClient(credentials),
    )


def _get_oke_resource(credentials: Dict[str, Any]) -> oci.container_engine.ContainerEngineClient:
    """
    Instantiates a OCI ContainerEngineClient resource object to call the
    Container Engine for Kubernetes (OKE) API.
    See https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengoverview.htm.
    :param credentials: The OCI Credentials object
    :return: A ContainerEngineClient resource object
    """
    return oci.container_engine.ContainerEngineClient(credentials)


def _initialize_resources(credentials: Dict[str, Any]) -> Resources:
    """
    Create namedtuple of all resource objects necessary for OCI data gathering.
    :param credentials: The OCI config object
    :return: namedtuple of all resource objects
    """
    return Resources(
        compute=_get_compute_resource(credentials),
        containerregistry=_get_containerregistry_resource(credentials),
        encryption=_get_encryption_resource(credentials),
        iam=_get_iam_resource(credentials),
        logging=_get_logging_resource(credentials),
        monitoring=_get_monitoring_resource(credentials),
        network=_get_network_resource(credentials),
        storage=_get_storage_resource(credentials),
        oke=_get_oke_resource(credentials),
    )


def start_oci_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Starts the OCI ingestion process by initializing OCI credentials, creating the necessary
    resource objects, and syncing data for the specified compartment.

    If config.params["oci_config"] exists, it is used as a base64-encoded JSON string containing:
    {
        user_ocid, fingerprint, private_key_content, tenancy_ocid, region,
        compartment_ocid, is_default_compartment
    }

    - tenancy_ocid: Always required for OCI SDK auth
    - compartment_ocid: The compartment to scope resource listing to
    - is_default_compartment: If true, run IAM sync. If false, skip IAM.

    Otherwise, falls back to reading credentials from ~/.oci/config.

    :param neo4j_session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """
    _ingestion_tic = time.perf_counter()
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "WORKSPACE_ID": config.params["workspace"]["id_string"] if hasattr(config, 'params') and config.params else "",
    }

    oci_config_b64 = config.params.get("ociConfig") if hasattr(config, 'params') and config.params else None

    if oci_config_b64:
        # Use base64-encoded JSON config from params
        logger.info("Using OCI credentials from config.params['oci_config'].")
        try:
            oci_config_json = json.loads(base64.b64decode(oci_config_b64).decode())
        except (ValueError, json.JSONDecodeError) as e:
            logger.error("Failed to decode OCI config from base64/JSON: %s", e)
            return

        try:
            tenancy_ocid = config.oci_tenancy_id
            compartment_ocid = config.oci_compartment_id
            credentials = {
                "user": config.params.get("userOcid"),
                "fingerprint": config.params.get("fingerprint") or oci_config_json["fingerprint"],
                "key_content": oci_config_json["private_key_content"],
                "tenancy": tenancy_ocid,
                "region": _resolve_region(config.params.get("defaultRegion", "PHX")),
            }
            oci.config.validate_config(credentials)
        except (KeyError, InvalidConfig) as e:
            logger.debug("Error occurred validating OCI config from params.", exc_info=True)
            logger.error(
                (
                    "Unable to initialize OCI creds from config.params. Error: %s "
                    "Make sure your OCI credentials are configured correctly and "
                    "that the identity you are authenticating to has the required Audit policies attached "
                    "(https://docs.cloud.oracle.com/iaas/Content/Identity/Concepts/commonpolicies.htm)."
                ),
                e,
            )
            return

        is_default_compartment = (compartment_ocid == tenancy_ocid)

        common_job_parameters["OCI_TENANCY_ID"] = tenancy_ocid
        common_job_parameters["OCI_COMPARTMENT_ID"] = compartment_ocid
        common_job_parameters["IS_DEFAULT_COMPARTMENT"] = is_default_compartment

        # Determine requested syncs
        requested_syncs: List[str] = list(RESOURCE_FUNCTIONS.keys())
        if config.oci_requested_syncs:
            oci_requested_syncs_string = ""
            for service in config.oci_requested_syncs:
                oci_requested_syncs_string += f"{service.get('name', ' ')},"
            requested_syncs = parse_and_validate_oci_requested_syncs(oci_requested_syncs_string[:-1])

        # Initialize resources
        resources = _initialize_resources(credentials)

        # Create workspace and tenancy nodes
        organizations.load_oci_accounts(
            neo4j_session, {"DEFAULT": credentials}, config.update_tag, common_job_parameters,
            identity_client=resources.iam,
        )

        # Load compartment nodes into Neo4j
        compartment_list = compartment.get_current_oci_compartment(resources.iam, compartment_ocid)
        if not compartment_list:
            compartment_list = [{"compartmentId": compartment_ocid, "name": compartment_ocid}]
        compartment.sync(neo4j_session, tenancy_ocid, compartment_list, config.update_tag, common_job_parameters)

        # Get regions from payload
        regions = config.params.get("regions")

        # Sync resources for the requested compartment
        _sync_multiple_compartments(
            neo4j_session, credentials, tenancy_ocid, compartment_list,
            requested_syncs, config.update_tag, common_job_parameters, regions,
        )
        logger.info(
            json.dumps({
                "event": "oci_tenancy_timing_summary",
                "tenancy": tenancy_ocid,
                "total_duration_seconds": round(time.perf_counter() - _ingestion_tic, 4),
            }),
        )
        return common_job_parameters
    else:
        # Fallback: read from ~/.oci/config file
        logger.info("No config.params['oci_config'] found, falling back to ~/.oci/config file.")
        try:
            credentials = oci.config.from_file("~/.oci/config", "DEFAULT")
            oci.config.validate_config(credentials)
        except (ConfigFileNotFound, ProfileNotFound, InvalidConfig) as e:
            logger.debug("Error occurred calling oci.config.from_file.", exc_info=True)
            logger.error(
                (
                    "Unable to initialize OCI creds. If you don't have OCI data or don't want to load "
                    "OCI data then you can ignore this message. Otherwise, the error code is: %s "
                    "Make sure your OCI credentials are configured correctly, your credentials file (if any) is valid, and "
                    "that the identity you are authenticating to has the required Audit policies attached "
                    "(https://docs.cloud.oracle.com/iaas/Content/Identity/Concepts/commonpolicies.htm)."
                ),
                e,
            )
            return

        if config.oci_sync_all_profiles:
            oci_accounts = organizations.get_oci_accounts_from_config()
        else:
            oci_accounts = organizations.get_oci_account_default()

        if not oci_accounts:
            logger.warning(
                "No valid OCI credentials could be found. No OCI accounts can be synced. Exiting OCI sync stage.",
            )
            return

        tenancy_id = list(oci_accounts.values())[0]["tenancy"]
        compartment_id = config.oci_compartment_id or tenancy_id

        common_job_parameters["OCI_TENANCY_ID"] = tenancy_id
        common_job_parameters["OCI_COMPARTMENT_ID"] = compartment_id

        # Determine requested syncs
        requested_syncs: List[str] = list(RESOURCE_FUNCTIONS.keys())
        if config.oci_requested_syncs:
            oci_requested_syncs_string = ""
            for service in config.oci_requested_syncs:
                oci_requested_syncs_string += f"{service.get('name', ' ')},"
            requested_syncs = parse_and_validate_oci_requested_syncs(oci_requested_syncs_string[:-1])

        # Create workspace and tenancy nodes
        organizations.sync(neo4j_session, oci_accounts, config.update_tag, common_job_parameters, resources.iam)

        # Load compartment nodes into Neo4j
        resources = _initialize_resources(list(oci_accounts.values())[0])
        compartment_list = compartment.get_current_oci_compartment(resources.iam, compartment_id)
        if not compartment_list:
            compartment_list = [{"compartmentId": compartment_id, "name": compartment_id}]
        compartment.sync(neo4j_session, tenancy_id, compartment_list, config.update_tag, common_job_parameters)

        # Get regions
        regions = [oci_accounts[list(oci_accounts.keys())[0]].get("region", "")]

        _sync_multiple_compartments(
            neo4j_session, list(oci_accounts.values())[0], tenancy_id, compartment_list,
            requested_syncs, config.update_tag, common_job_parameters, regions,
        )
        logger.info(
            json.dumps({
                "event": "oci_tenancy_timing_summary",
                "tenancy": tenancy_id,
                "total_duration_seconds": round(time.perf_counter() - _ingestion_tic, 4),
            }),
        )


def _resolve_region(region_key: str) -> str:
    """Convert OCI region short key (e.g. PHX) to full region name (e.g. us-phoenix-1)."""
    region_map = {
        "AMS": "eu-amsterdam-1",
        "IAD": "us-ashburn-1",
        "DXB": "me-dubai-1",
        "FRA": "eu-frankfurt-1",
        "JED": "me-jeddah-1",
        "JNB": "af-johannesburg-1",
        "LHR": "uk-london-1",
        "YUL": "ca-montreal-1",
        "BOM": "ap-mumbai-1",
        "KIX": "ap-osaka-1",
        "PHX": "us-phoenix-1",
        "SJC": "us-sanjose-1",
        "GRU": "sa-saopaulo-1",
        "SYD": "ap-sydney-1",
        "NRT": "ap-tokyo-1",
        "YYZ": "ca-toronto-1",
        "ICN": "ap-seoul-1",
        "HYD": "ap-hyderabad-1",
        "MEL": "ap-melbourne-1",
        "SIN": "ap-singapore-1",
        "CDG": "eu-paris-1",
        "ARN": "eu-stockholm-1",
        "ZRH": "eu-zurich-1",
        "MTZ": "il-jerusalem-1",
        "LIN": "eu-milan-1",
        "MRS": "eu-marseille-1",
        "MAD": "eu-madrid-1",
        "ORD": "us-chicago-1",
        "SCL": "sa-santiago-1",
        "VCP": "sa-vinhedo-1",
        "QRO": "mx-queretaro-1",
        "MTY": "mx-monterrey-1",
        "BOG": "sa-bogota-1",
        "VAP": "sa-valparaiso-1",
    }
    return region_map.get(region_key.upper(), region_key)
