import logging
from typing import Any, Dict, List
import yaml

from kubernetes.client.models import V1ConfigMap

from cartography.intel.kubernetes.util import K8sClient
from cartography.util import timeit
from cartography.client.core.tx import load
from cartography.models.kubernetes.users import KubernetesUserSchema
from cartography.models.kubernetes.groups import KubernetesGroupSchema
from cartography.graph.job import GraphJob
import neo4j

logger = logging.getLogger(__name__)


@timeit
def get_aws_auth_configmap(client: K8sClient) -> V1ConfigMap:
    """
    Get aws-auth ConfigMap from kube-system namespace.
    """
    logger.info(f"Retrieving aws-auth ConfigMap from cluster {client.name}")
    return client.core.read_namespaced_config_map(
        name="aws-auth",
        namespace="kube-system"
    )


def parse_role_mappings(configmap: V1ConfigMap) -> List[Dict[str, Any]]:
    """
    Parse mapRoles from aws-auth ConfigMap.
    
    :param configmap: V1ConfigMap containing aws-auth data
    :return: List of role mapping dictionaries
    """
    map_roles_yaml = configmap.data['mapRoles']
    role_mappings = yaml.safe_load(map_roles_yaml) or []
    
    # Filter out templated entries because these are not real users
    filtered_mappings = []
    for mapping in role_mappings:
        username = mapping.get('username', '')
        if '{{' in username:
            logger.debug(f"Skipping templated username: {username}")
            continue
        filtered_mappings.append(mapping)
    
    logger.info(f"Parsed {len(filtered_mappings)} role mappings from aws-auth ConfigMap")
    return filtered_mappings


def transform_aws_role_mappings(
    role_mappings: List[Dict[str, Any]], 
    cluster_name: str
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Transform role mappings into user/group data with AWS role relationships.
    """
    users = []
    groups = []
    
    for mapping in role_mappings:
        role_arn = mapping.get('rolearn')
        username = mapping.get('username')
        group_names = mapping.get('groups', [])
        
        if not role_arn:
            continue
            
        # Create user data with AWS role relationship if present
        if username:
            users.append({
                'id': f"{cluster_name}/{username}",
                'name': username,
                'cluster_name': cluster_name,
                'aws_role_arn': role_arn,  # For the AWS Role relationship
            })
        
        # Create group data with AWS role relationship for each group
        for group_name in group_names:
            groups.append({
                'id': f"{cluster_name}/{group_name}",
                'name': group_name,
                'cluster_name': cluster_name,
                'aws_role_arn': role_arn,  # For the AWS Role relationship
            })
    
    logger.info(f"Transformed {len(users)} users and {len(groups)} groups with AWS role mappings")
    
    return {
        'users': users,
        'groups': groups
    }


@timeit
def load_aws_role_mappings(
    neo4j_session: neo4j.Session,
    users: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str
) -> None:
    """
    Load Kubernetes Users/Groups with AWS Role relationships into Neo4j using schema-based loading.
    """
    logger.info(f"Loading {len(users)} Kubernetes Users with AWS Role mappings")
    
    # Load Kubernetes Users with AWS Role relationships
    if users:
        load(
            neo4j_session,
            KubernetesUserSchema(),
            users,
            lastupdated=update_tag,
            CLUSTER_ID=cluster_id,
            CLUSTER_NAME=cluster_name,
        )
    
    logger.info(f"Loading {len(groups)} Kubernetes Groups with AWS Role mappings")
    
    # Load Kubernetes Groups with AWS Role relationships
    if groups:
        load(
            neo4j_session,
            KubernetesGroupSchema(),
            groups,
            lastupdated=update_tag,
            CLUSTER_ID=cluster_id,
            CLUSTER_NAME=cluster_name,
        )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    logger.debug("Running cleanup job for EKS AWS Role relationships")
    
    cleanup_job = GraphJob.from_node_schema(
        KubernetesUserSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)
    
    cleanup_job = GraphJob.from_node_schema(
        KubernetesGroupSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    k8s_client: K8sClient,
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    """
    Sync EKS aws-auth ConfigMap role mappings to create AWS Role to Kubernetes User/Group relationships.
    
    This function should be called AFTER the main Kubernetes RBAC sync to ensure Users and Groups
    already exist in the graph. It will update existing Users/Groups with AWS Role relationships.
    """
    logger.info(f"Starting EKS aws-auth sync for cluster {cluster_name}")
    
    configmap = get_aws_auth_configmap(k8s_client)
    
    role_mappings = parse_role_mappings(configmap)
    
    if not role_mappings:
        logger.info("No role mappings found in aws-auth ConfigMap")
        return
    
    transformed_data = transform_aws_role_mappings(role_mappings, cluster_name)
    
    load_aws_role_mappings(
        neo4j_session,
        transformed_data['users'],
        transformed_data['groups'],
        update_tag,
        cluster_id,
        cluster_name
    )
    
    common_job_parameters = {
        "UPDATE_TAG": update_tag,
        "CLUSTER_ID": cluster_id,
    }
    cleanup(neo4j_session, common_job_parameters)
    
    logger.info(f"Successfully completed EKS aws-auth sync for cluster {cluster_name}") 
    
    