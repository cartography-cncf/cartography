import logging

import neo4j

from cartography.config import Config
from cartography.util import timeit
from cartography.util.lazy import lazy_callable
from cartography.util.lazy import lazy_import

# Bound lazily so that the provider SDK only loads once the config gate below
# has decided that this module has something to sync.
scaleway = lazy_import("scaleway")
sync_apikeys = lazy_callable("cartography.intel.scaleway.iam.apikeys", "sync")
sync_apple_silicon = lazy_callable(
    "cartography.intel.scaleway.baremetal.apple_silicon", "sync"
)
sync_applications = lazy_callable("cartography.intel.scaleway.iam.applications", "sync")
sync_clusters = lazy_callable("cartography.intel.scaleway.kapsule.clusters", "sync")
sync_containers = lazy_callable(
    "cartography.intel.scaleway.serverless.containers", "sync"
)
sync_datawarehouse = lazy_callable(
    "cartography.intel.scaleway.databases.datawarehouse", "sync"
)
sync_dedibox = lazy_callable("cartography.intel.scaleway.baremetal.dedibox", "sync")
sync_dns = lazy_callable("cartography.intel.scaleway.dns.dns", "sync")
sync_domains = lazy_callable("cartography.intel.scaleway.dns.domains", "sync")
sync_elastic_metal = lazy_callable(
    "cartography.intel.scaleway.baremetal.elastic_metal", "sync"
)
sync_filesystems = lazy_callable(
    "cartography.intel.scaleway.storage.filesystems", "sync"
)
sync_flexible_ips = lazy_callable(
    "cartography.intel.scaleway.baremetal.flexible_ips", "sync"
)
sync_flexibleips = lazy_callable(
    "cartography.intel.scaleway.instances.flexibleips", "sync"
)
sync_functions = lazy_callable(
    "cartography.intel.scaleway.serverless.functions", "sync"
)
sync_groups = lazy_callable("cartography.intel.scaleway.iam.groups", "sync")
sync_instances = lazy_callable("cartography.intel.scaleway.instances.instances", "sync")
sync_ips = lazy_callable("cartography.intel.scaleway.network.ips", "sync")
sync_jobs = lazy_callable("cartography.intel.scaleway.serverless.jobs", "sync")
sync_keys = lazy_callable("cartography.intel.scaleway.kms.keys", "sync")
sync_loadbalancers = lazy_callable(
    "cartography.intel.scaleway.loadbalancers.loadbalancers", "sync"
)
sync_mongodb = lazy_callable("cartography.intel.scaleway.databases.mongodb", "sync")
sync_namespaces = lazy_callable(
    "cartography.intel.scaleway.container_registry.namespaces", "sync"
)
sync_objectstorage = lazy_callable(
    "cartography.intel.scaleway.storage.objectstorage", "sync"
)
sync_permissions = lazy_callable("cartography.intel.scaleway.iam.permissions", "sync")
sync_permissionsets = lazy_callable(
    "cartography.intel.scaleway.iam.permissionsets", "sync"
)
sync_policies = lazy_callable("cartography.intel.scaleway.iam.policies", "sync")
sync_private_networks = lazy_callable(
    "cartography.intel.scaleway.network.private_networks", "sync"
)
sync_projects = lazy_callable("cartography.intel.scaleway.projects", "sync")
sync_public_gateways = lazy_callable(
    "cartography.intel.scaleway.network.public_gateways", "sync"
)
sync_rdb = lazy_callable("cartography.intel.scaleway.databases.rdb", "sync")
sync_redis = lazy_callable("cartography.intel.scaleway.databases.redis", "sync")
sync_searchdb = lazy_callable("cartography.intel.scaleway.databases.searchdb", "sync")
sync_secrets = lazy_callable("cartography.intel.scaleway.secrets.secrets", "sync")
sync_securitygroups = lazy_callable(
    "cartography.intel.scaleway.instances.securitygroups", "sync"
)
sync_serverless_sql = lazy_callable(
    "cartography.intel.scaleway.databases.serverless_sql", "sync"
)
sync_snapshots = lazy_callable("cartography.intel.scaleway.storage.snapshots", "sync")
sync_sshkeys = lazy_callable("cartography.intel.scaleway.iam.sshkeys", "sync")
sync_supply_chain = lazy_callable(
    "cartography.intel.scaleway.container_registry.supply_chain", "sync"
)
sync_users = lazy_callable("cartography.intel.scaleway.iam.users", "sync")
sync_volumes = lazy_callable("cartography.intel.scaleway.storage.volumes", "sync")
sync_vpcs = lazy_callable("cartography.intel.scaleway.network.vpcs", "sync")

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
    projects = sync_projects(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )
    projects_id = [project["id"] for project in projects]
    sync_users(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )
    sync_applications(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )
    sync_groups(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )
    sync_apikeys(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )
    sync_permissionsets(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )
    sync_policies(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )
    sync_sshkeys(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )

    # Storage
    sync_volumes(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_snapshots(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_objectstorage(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_filesystems(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Instances
    sync_flexibleips(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_instances(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_securitygroups(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Bare Metal (Elastic Metal / Apple silicon / Dedibox)
    sync_elastic_metal(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_apple_silicon(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_dedibox(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    # Elastic Metal Flexible IPs (loaded after Elastic Metal servers so the
    # IDENTIFIES edge resolves).
    sync_flexible_ips(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Network (VPC + IPAM)
    sync_vpcs(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_private_networks(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_ips(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    # Public Gateways (loaded after PrivateNetworks so ATTACHED_TO edges resolve).
    sync_public_gateways(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Load Balancers
    sync_loadbalancers(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # DNS
    sync_dns(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_domains(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        update_tag=config.update_tag,
    )

    # Key Manager (loaded before Secrets so Secret -> Key ENCRYPTED_BY edges resolve).
    sync_keys(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Secret Manager
    sync_secrets(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Kubernetes (Kapsule). Loaded after VPC/PrivateNetwork so the
    # ScalewayKapsuleCluster -> ScalewayPrivateNetwork edge resolves.
    sync_clusters(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Container Registry. Returns the tag URI -> digest map so serverless
    # containers can resolve their `registry_image` to a digest and declare a
    # HAS_IMAGE edge to the Image node.
    registry_image_digests = sync_namespaces(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    # Enrich registry images with layers + provenance from the OCI registry
    # endpoint (source for code-to-cloud); runs after the registry nodes exist.
    sync_supply_chain(
        neo4j_session,
        config.scaleway_secret_key,
        common_job_parameters,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Managed Databases (loaded after PrivateNetworks so ATTACHED_TO edges resolve).
    sync_rdb(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_redis(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_mongodb(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_datawarehouse(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_serverless_sql(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_searchdb(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # Serverless (Functions / Containers / Jobs). Loaded after PrivateNetworks
    # so the ATTACHED_TO edges resolve, and after the Container Registry so the
    # container HAS_IMAGE -> Image edges resolve (registry_image_digests below).
    sync_functions(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
    sync_containers(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
        registry_image_digests=registry_image_digests,
    )
    sync_jobs(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )

    # IAM permissions: materialize principal -> permission set (HAS_ROLE) and
    # principal -> project (CAN_ACCESS) edges from the policy/rule graph. Runs
    # last so all IAM and project nodes are present.
    sync_permissions(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=config.scaleway_org,
        projects_id=projects_id,
        update_tag=config.update_tag,
    )
