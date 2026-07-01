import logging

import neo4j
import scaleway

import cartography.intel.scaleway.container_registry.namespaces
import cartography.intel.scaleway.databases.mongodb
import cartography.intel.scaleway.databases.rdb
import cartography.intel.scaleway.databases.redis
import cartography.intel.scaleway.dns.dns
import cartography.intel.scaleway.iam.apikeys
import cartography.intel.scaleway.iam.applications
import cartography.intel.scaleway.iam.groups
import cartography.intel.scaleway.iam.permissionsets
import cartography.intel.scaleway.iam.policies
import cartography.intel.scaleway.iam.users
import cartography.intel.scaleway.instances.flexibleips
import cartography.intel.scaleway.instances.instances
import cartography.intel.scaleway.instances.securitygroups
import cartography.intel.scaleway.kapsule.clusters
import cartography.intel.scaleway.kms.keys
import cartography.intel.scaleway.loadbalancers.loadbalancers
import cartography.intel.scaleway.network.ips
import cartography.intel.scaleway.network.private_networks
import cartography.intel.scaleway.network.vpcs
import cartography.intel.scaleway.projects
import cartography.intel.scaleway.secrets.secrets
import cartography.intel.scaleway.storage.objectstorage
import cartography.intel.scaleway.storage.snapshots
import cartography.intel.scaleway.storage.volumes
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_scaleway_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Scaleway data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    if (
        not config.scaleway_access_key
        or not config.scaleway_secret_key
        or not config.scaleway_org
    ):
        logger.info(
            "Tailscale import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    # Create client
    client = scaleway.Client(
        access_key=config.scaleway_access_key,
        secret_key=config.scaleway_secret_key,
    )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "ORG_ID": config.scaleway_org,
    }

    # Organization level
    projects = cartography.intel.scaleway.projects.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )
    projects_id = [project["id"] for project in projects]
    cartography.intel.scaleway.iam.users.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )
    cartography.intel.scaleway.iam.applications.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )
    cartography.intel.scaleway.iam.groups.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )
    cartography.intel.scaleway.iam.apikeys.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )
    cartography.intel.scaleway.iam.permissionsets.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )
    cartography.intel.scaleway.iam.policies.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )

    # Storage
    cartography.intel.scaleway.storage.volumes.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    cartography.intel.scaleway.storage.snapshots.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    cartography.intel.scaleway.storage.objectstorage.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Instances
    # DISABLED due to https://github.com/scaleway/scaleway-sdk-python/issues/1040
    """
    cartography.intel.scaleway.instances.flexibleips.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    """
    cartography.intel.scaleway.instances.instances.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    cartography.intel.scaleway.instances.securitygroups.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Network (VPC + IPAM)
    cartography.intel.scaleway.network.vpcs.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    cartography.intel.scaleway.network.private_networks.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    cartography.intel.scaleway.network.ips.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Load Balancers
    cartography.intel.scaleway.loadbalancers.loadbalancers.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # DNS
    cartography.intel.scaleway.dns.dns.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Key Manager (loaded before Secrets so Secret -> Key ENCRYPTED_BY edges resolve).
    cartography.intel.scaleway.kms.keys.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Secret Manager
    cartography.intel.scaleway.secrets.secrets.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Kubernetes (Kapsule). Loaded after VPC/PrivateNetwork so the
    # ScalewayKapsuleCluster -> ScalewayPrivateNetwork edge resolves.
    cartography.intel.scaleway.kapsule.clusters.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Container Registry
    cartography.intel.scaleway.container_registry.namespaces.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Managed Databases (loaded after PrivateNetworks so ATTACHED_TO edges resolve).
    cartography.intel.scaleway.databases.rdb.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    cartography.intel.scaleway.databases.redis.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    cartography.intel.scaleway.databases.mongodb.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
