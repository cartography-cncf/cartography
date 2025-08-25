import logging
import re
from typing import Any
from typing import Dict
from typing import List
from typing import TypedDict

import boto3
import neo4j
import yaml
from arn import Arn
from kubernetes.client.models import V1ConfigMap

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.rbac import get_cluster_role_bindings
from cartography.intel.kubernetes.rbac import get_role_bindings
from cartography.intel.kubernetes.rbac import transform_users
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.groups import KubernetesGroupSchema
from cartography.models.kubernetes.oidc import KubernetesOIDCProviderSchema
from cartography.models.kubernetes.users import KubernetesUserSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


class ParsedAuthMappings(TypedDict):
    roles: List[Dict[str, Any]]
    users: List[Dict[str, Any]]
    accounts: List[str]
    templated_roles: List[Dict[str, Any]]
    templated_users: List[Dict[str, Any]]


def process_templated_string(template_string: str, arn: str) -> str:
    """
    Process templated string by replacing template variables with actual values.

    Currently supports:
    - {{AccountID}}: Replaced with account ID from the provided ARN
    - {{SessionNameRaw}}: Cannot be resolved at ConfigMap parse time, requires regex matching
    - {{SessionName}}: Cannot be resolved at ConfigMap parse time, requires regex matching
    """
    if not template_string or not arn:
        return template_string

    processed_string = template_string

    # Handle {{AccountID}} template first
    if "{{AccountID}}" in processed_string:
        try:
            parsed_arn = Arn(arn)
            account_id = parsed_arn.account
            processed_string = processed_string.replace("{{AccountID}}", account_id)
            logger.debug(
                f"Replaced {{{{AccountID}}}} with {account_id} in string: {template_string} -> {processed_string}"
            )
        except Exception:
            logger.warning(
                f"Failed to parse account ID from ARN {arn} for templated string {template_string}"
            )
            return template_string  # Return original if we can't parse

    # Check for SessionNameRaw templates - these cannot be resolved at parse time
    # Return the partially processed string (with AccountID resolved) for regex matching
    if (
        "{{SessionNameRaw}}" in processed_string
        or "{{SessionName}}" in processed_string
    ):
        logger.debug(
            f"String contains session name template that requires regex matching: {processed_string}"
        )
        return processed_string  # Return partially processed string

    return processed_string


def template_to_regex(template_string: str) -> str:
    """
    Convert a templated string into a regular expression pattern.

    Supports:
    - {{AccountID}}: Matches 12-digit AWS account IDs
    - {{SessionNameRaw}}: Matches session names (preserves special characters)
    - {{SessionName}}: Matches session names (transliterated special characters)
    """
    if not template_string:
        return ""

    # Start with the template string
    pattern = template_string

    # Replace templates with regex capture groups
    pattern = pattern.replace("{{AccountID}}", r"(\d{12})")
    pattern = pattern.replace("{{SessionNameRaw}}", r"([^/\s]+)")
    pattern = pattern.replace(
        "{{SessionName}}", r"([^/\s]+)"
    )  # Same pattern as SessionNameRaw

    # Escape any other regex special characters, but preserve our capture groups
    # We need to be careful not to escape the parentheses we just added
    escaped_pattern = ""
    i = 0
    while i < len(pattern):
        if (
            pattern[i : i + 1] == "("
            and i + 1 < len(pattern)
            and pattern[i + 1 : i + 2] in "[^"
        ):
            # This is one of our capture groups, find the closing parenthesis
            paren_count = 1
            j = i + 1
            while j < len(pattern) and paren_count > 0:
                if pattern[j] == "(":
                    paren_count += 1
                elif pattern[j] == ")":
                    paren_count -= 1
                j += 1
            # Add the capture group as-is
            escaped_pattern += pattern[i:j]
            i = j
        else:
            # Escape this character if it's a regex special character
            if pattern[i] in r".^$*+?{}[]|()\\":
                escaped_pattern += "\\" + pattern[i]
            else:
                escaped_pattern += pattern[i]
            i += 1

    return f"^{escaped_pattern}$"


def find_templated_users(
    templated_mappings: List[Dict[str, Any]], actual_k8s_users: List[str], arn: str
) -> List[Dict[str, Any]]:
    """
    Find actual Kubernetes users that match templated patterns.
    """
    matched_users = []

    for mapping in templated_mappings:
        template_username = mapping.get("username", "")
        if not template_username or "{{" not in template_username:
            continue

        # Convert template to regex
        regex_pattern = template_to_regex(template_username)
        if not regex_pattern:
            continue

        try:
            compiled_regex = re.compile(regex_pattern)

            # Find matching users
            for k8s_user in actual_k8s_users:
                match = compiled_regex.match(k8s_user)
                if match:
                    # Create a resolved mapping
                    resolved_mapping = mapping.copy()
                    resolved_mapping["username"] = (
                        k8s_user  # Use the actual resolved username
                    )
                    resolved_mapping["template_match"] = {
                        "original_template": template_username,
                        "captured_values": match.groups(),
                    }
                    matched_users.append(resolved_mapping)
                    logger.debug(
                        f"Matched template '{template_username}' to user '{k8s_user}' for ARN {arn}"
                    )

        except re.error as e:
            logger.warning(
                f"Invalid regex pattern '{regex_pattern}' from template '{template_username}': {e}"
            )
            continue

    return matched_users


def process_templated_group_name(
    group_name: str, original_template: str, captured_values: tuple
) -> str:
    """
    Process templated group name by replacing template variables with captured values.
    """
    if not group_name or not captured_values:
        return group_name

    resolved_group_name = group_name

    # Determine the order of templates in the original username template
    # This tells us which capture group corresponds to which template
    account_id_index = None
    session_name_raw_index = None
    session_name_index = None

    # Find positions of templates in original template to determine capture group order
    template_positions = []
    if "{{AccountID}}" in original_template:
        template_positions.append(
            ("{{AccountID}}", original_template.find("{{AccountID}}"))
        )
    if "{{SessionNameRaw}}" in original_template:
        template_positions.append(
            ("{{SessionNameRaw}}", original_template.find("{{SessionNameRaw}}"))
        )
    if "{{SessionName}}" in original_template:
        template_positions.append(
            ("{{SessionName}}", original_template.find("{{SessionName}}"))
        )

    # Sort by position to determine capture group order
    template_positions.sort(key=lambda x: x[1])

    # Assign capture group indices based on position order
    for i, (template_name, _) in enumerate(template_positions):
        if template_name == "{{AccountID}}":
            account_id_index = i
        elif template_name == "{{SessionNameRaw}}":
            session_name_raw_index = i
        elif template_name == "{{SessionName}}":
            session_name_index = i

    # Replace AccountID templates
    if (
        "{{AccountID}}" in resolved_group_name
        and account_id_index is not None
        and account_id_index < len(captured_values)
    ):
        resolved_group_name = resolved_group_name.replace(
            "{{AccountID}}", captured_values[account_id_index]
        )

    # Replace SessionNameRaw templates
    if (
        "{{SessionNameRaw}}" in resolved_group_name
        and session_name_raw_index is not None
        and session_name_raw_index < len(captured_values)
    ):
        resolved_group_name = resolved_group_name.replace(
            "{{SessionNameRaw}}", captured_values[session_name_raw_index]
        )

    # Replace SessionName templates
    if (
        "{{SessionName}}" in resolved_group_name
        and session_name_index is not None
        and session_name_index < len(captured_values)
    ):
        resolved_group_name = resolved_group_name.replace(
            "{{SessionName}}", captured_values[session_name_index]
        )

    return resolved_group_name


def parse_aws_account_from_kube_user(kube_user_name: str) -> str:
    """
    Parse AWS account ID from a Kubernetes user's name if it's an ARN.
    """
    try:
        arn = Arn(kube_user_name)
        return arn.account
    except Exception:
        # Not a valid ARN, return empty string
        return ""


@timeit
@aws_handle_regions
def get_aws_auth_configmap(client: K8sClient) -> V1ConfigMap:
    """
    Get aws-auth ConfigMap from kube-system namespace.
    """
    logger.info(f"Retrieving aws-auth ConfigMap from cluster {client.name}")
    return client.core.read_namespaced_config_map(
        name="aws-auth", namespace="kube-system"
    )


def parse_aws_auth_mappings(configmap: V1ConfigMap) -> ParsedAuthMappings:
    """
    Parse mapRoles, mapUsers, and mapAccounts from aws-auth ConfigMap.

    :param configmap: V1ConfigMap containing aws-auth data
    :return: Dictionary with 'roles', 'users', 'accounts', 'templated_roles', and 'templated_users' lists
    """
    # Parse mapRoles
    map_roles_yaml = configmap.data.get("mapRoles", "")
    role_mappings = yaml.safe_load(map_roles_yaml) or []

    # Parse mapUsers
    map_users_yaml = configmap.data.get("mapUsers", "")
    user_mappings = yaml.safe_load(map_users_yaml) or []

    # Parse mapAccounts
    map_accounts_yaml = configmap.data.get("mapAccounts", "")
    account_mappings: List[str] = yaml.safe_load(map_accounts_yaml) or []

    # Process templated entries
    filtered_role_mappings = []
    templated_role_mappings = []
    for mapping in role_mappings:
        username = mapping.get("username", "")
        rolearn = mapping.get("rolearn", "")

        # Check if username contains SessionNameRaw templates that need regex matching
        if "{{SessionNameRaw}}" in username or "{{SessionName}}" in username:
            # Process any AccountID templates first as there might be both SessionName and AccountID templates
            processed_mapping = mapping.copy()
            processed_username = process_templated_string(username, rolearn)
            processed_mapping["username"] = processed_username

            # Also process templated group names for AccountID
            groups = mapping.get("groups", [])
            if groups:
                processed_groups = []
                for group in groups:
                    processed_group = process_templated_string(group, rolearn)
                    processed_groups.append(processed_group)
                processed_mapping["groups"] = processed_groups

            templated_role_mappings.append(processed_mapping)
            logger.debug(
                f"Collected templated role mapping for regex matching: {username} -> {processed_username}"
            )
            continue

        # Process templated username if it just contains an AccountID template
        if "{{" in username:
            processed_username = process_templated_string(username, rolearn)
            if processed_username != username:
                # Create a copy of the mapping with processed username
                processed_mapping = mapping.copy()
                processed_mapping["username"] = processed_username

                # Also process templated group names if they exist
                groups = mapping.get("groups", [])
                if groups:
                    processed_groups = []
                    for group in groups:
                        if "{{" in group:
                            processed_group = process_templated_string(group, rolearn)
                            processed_groups.append(processed_group)
                        else:
                            processed_groups.append(group)
                    processed_mapping["groups"] = processed_groups

                filtered_role_mappings.append(processed_mapping)
                logger.debug(
                    f"Processed templated role mapping: {username} -> {processed_username}"
                )
            else:
                # Skip if we couldn't process the template
                logger.debug(
                    f"Skipping role mapping with unprocessable template: {username}"
                )
        else:
            # Check if only groups are templated (username is not templated)
            groups = mapping.get("groups", [])
            has_templated_groups = any("{{" in group for group in groups)

            if has_templated_groups:
                # Create a copy of the mapping with processed group names
                processed_mapping = mapping.copy()
                processed_groups = []
                for group in groups:
                    if "{{" in group:
                        processed_group = process_templated_string(group, rolearn)
                        processed_groups.append(processed_group)
                    else:
                        processed_groups.append(group)
                processed_mapping["groups"] = processed_groups
                filtered_role_mappings.append(processed_mapping)
                logger.debug(
                    f"Processed templated groups in role mapping: {groups} -> {processed_groups}"
                )
            else:
                # Non-templated mapping, keep as-is
                filtered_role_mappings.append(mapping)

    filtered_user_mappings = []
    templated_user_mappings = []
    for mapping in user_mappings:
        username = mapping.get("username", "")
        userarn = mapping.get("userarn", "")

        # Check if username contains SessionNameRaw templates that need regex matching
        if "{{SessionNameRaw}}" in username or "{{SessionName}}" in username:
            # Process any AccountID templates first, then store for regex matching
            processed_mapping = mapping.copy()
            processed_username = process_templated_string(username, userarn)
            processed_mapping["username"] = processed_username

            # Also process templated group names for AccountID
            groups = mapping.get("groups", [])
            if groups:
                processed_groups = []
                for group in groups:
                    processed_group = process_templated_string(group, userarn)
                    processed_groups.append(processed_group)
                processed_mapping["groups"] = processed_groups

            templated_user_mappings.append(processed_mapping)
            logger.debug(
                f"Collected templated user mapping for regex matching: {username} -> {processed_username}"
            )
            continue

        # Process templated username if it contains other templates (like AccountID)
        if "{{" in username:
            processed_username = process_templated_string(username, userarn)
            if processed_username != username:
                # Create a copy of the mapping with processed username
                processed_mapping = mapping.copy()
                processed_mapping["username"] = processed_username

                # Also process templated group names if they exist
                groups = mapping.get("groups", [])
                if groups:
                    processed_groups = []
                    for group in groups:
                        if "{{" in group:
                            processed_group = process_templated_string(group, userarn)
                            processed_groups.append(processed_group)
                        else:
                            processed_groups.append(group)
                    processed_mapping["groups"] = processed_groups

                filtered_user_mappings.append(processed_mapping)
                logger.debug(
                    f"Processed templated user mapping: {username} -> {processed_username}"
                )
            else:
                # Skip if we couldn't process the template
                logger.debug(
                    f"Skipping user mapping with unprocessable template: {username}"
                )
        else:
            # Check if only groups are templated (username is not templated)
            groups = mapping.get("groups", [])
            has_templated_groups = any("{{" in group for group in groups)

            if has_templated_groups:
                # Create a copy of the mapping with processed group names
                processed_mapping = mapping.copy()
                processed_groups = []
                for group in groups:
                    if "{{" in group:
                        processed_group = process_templated_string(group, userarn)
                        processed_groups.append(processed_group)
                    else:
                        processed_groups.append(group)
                processed_mapping["groups"] = processed_groups
                filtered_user_mappings.append(processed_mapping)
                logger.debug(
                    f"Processed templated groups in user mapping: {groups} -> {processed_groups}"
                )
            else:
                # Non-templated mapping, keep as-is
                filtered_user_mappings.append(mapping)

    # Account mappings are just account IDs, no templating to filter
    filtered_account_mappings = account_mappings

    logger.info(
        f"Parsed {len(filtered_role_mappings)} role mappings, {len(filtered_user_mappings)} user mappings, "
        f"and {len(filtered_account_mappings)} account mappings from aws-auth ConfigMap"
    )
    return {
        "roles": filtered_role_mappings,
        "users": filtered_user_mappings,
        "accounts": filtered_account_mappings,
        "templated_roles": templated_role_mappings,
        "templated_users": templated_user_mappings,
    }


def transform_aws_auth_mappings(
    role_mappings: List[Dict[str, Any]],
    user_mappings: List[Dict[str, Any]],
    account_mappings: List[str],
    templated_role_mappings: List[Dict[str, Any]],
    templated_user_mappings: List[Dict[str, Any]],
    cluster_name: str,
    k8s_client: K8sClient,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Transform role, user, and account mappings into user/group data with AWS relationships.
    Includes regex matching for templated entries with SessionNameRaw.
    """
    users = []
    groups = []

    # Get actual Kubernetes users from role bindings once (used by both templated matching and mapAccounts)
    role_bindings = get_role_bindings(k8s_client)
    cluster_role_bindings = get_cluster_role_bindings(k8s_client)
    all_rbac_users = transform_users(role_bindings, cluster_role_bindings, cluster_name)
    actual_k8s_usernames = [user["name"] for user in all_rbac_users]

    # Process templated role mappings via regex matching
    for mapping in templated_role_mappings:
        role_arn = mapping.get("rolearn")
        if not role_arn:
            continue

        # Find matching users via regex
        matched_mappings = find_templated_users(
            [mapping], actual_k8s_usernames, role_arn
        )
        for matched_mapping in matched_mappings:
            resolved_username = matched_mapping["username"]
            group_names = matched_mapping.get("groups", [])
            captured_values = matched_mapping["template_match"]["captured_values"]

            # Create user data with AWS role relationship
            users.append(
                {
                    "id": f"{cluster_name}/{resolved_username}",
                    "name": resolved_username,
                    "cluster_name": cluster_name,
                    "aws_role_arn": role_arn,
                }
            )

            # Create group data with AWS role relationship for each group
            for group_name in group_names:
                # Process templated group names using captured values
                resolved_group_name = group_name
                if (
                    "{{AccountID}}" in group_name
                    or "{{SessionNameRaw}}" in group_name
                    or "{{SessionName}}" in group_name
                ) and captured_values:
                    # Use the original username template to determine capture group order
                    original_template = matched_mapping["template_match"][
                        "original_template"
                    ]
                    resolved_group_name = process_templated_group_name(
                        group_name, original_template, captured_values
                    )

                groups.append(
                    {
                        "id": f"{cluster_name}/{resolved_group_name}",
                        "name": resolved_group_name,
                        "cluster_name": cluster_name,
                        "aws_role_arn": role_arn,
                    }
                )

            logger.debug(
                f"Processed templated role mapping via regex: {matched_mapping['template_match']['original_template']} -> {resolved_username}"
            )

    # Process templated user mappings via regex matching
    for mapping in templated_user_mappings:
        user_arn = mapping.get("userarn")
        if not user_arn:
            continue

        # Find matching users via regex
        matched_mappings = find_templated_users(
            [mapping], actual_k8s_usernames, user_arn
        )
        for matched_mapping in matched_mappings:
            resolved_username = matched_mapping["username"]
            group_names = matched_mapping.get("groups", [])
            captured_values = matched_mapping["template_match"]["captured_values"]

            # Create user data with AWS user relationship
            users.append(
                {
                    "id": f"{cluster_name}/{resolved_username}",
                    "name": resolved_username,
                    "cluster_name": cluster_name,
                    "aws_user_arn": user_arn,
                }
            )

            # Create group data with AWS user relationship for each group
            for group_name in group_names:
                # Process templated group names using captured values
                resolved_group_name = group_name
                if (
                    "{{AccountID}}" in group_name
                    or "{{SessionNameRaw}}" in group_name
                    or "{{SessionName}}" in group_name
                ) and captured_values:
                    # Use the original username template to determine capture group order
                    original_template = matched_mapping["template_match"][
                        "original_template"
                    ]
                    resolved_group_name = process_templated_group_name(
                        group_name, original_template, captured_values
                    )

                groups.append(
                    {
                        "id": f"{cluster_name}/{resolved_group_name}",
                        "name": resolved_group_name,
                        "cluster_name": cluster_name,
                        "aws_user_arn": user_arn,
                    }
                )

            logger.debug(
                f"Processed templated user mapping via regex: {matched_mapping['template_match']['original_template']} -> {resolved_username}"
            )

    # Process role mappings
    for mapping in role_mappings:
        role_arn = mapping.get("rolearn")
        username = (
            mapping.get("username") or role_arn
        )  # Default to ARN if username not provided
        group_names = mapping.get("groups", [])

        if not role_arn:
            continue

        # Create user data with AWS role relationship (always create user, using ARN as username if needed)
        users.append(
            {
                "id": f"{cluster_name}/{username}",
                "name": username,
                "cluster_name": cluster_name,
                "aws_role_arn": role_arn,  # For the AWS Role relationship
            }
        )

        # Create group data with AWS role relationship for each group
        for group_name in group_names:
            groups.append(
                {
                    "id": f"{cluster_name}/{group_name}",
                    "name": group_name,
                    "cluster_name": cluster_name,
                    "aws_role_arn": role_arn,  # For the AWS Role relationship
                }
            )

    # Process user mappings
    for mapping in user_mappings:
        user_arn = mapping.get("userarn")
        username = (
            mapping.get("username") or user_arn
        )  # Default to ARN if username not provided
        group_names = mapping.get("groups", [])

        if not user_arn:
            continue

        # Create user data with AWS user relationship (always create user, using ARN as username if needed)
        users.append(
            {
                "id": f"{cluster_name}/{username}",
                "name": username,
                "cluster_name": cluster_name,
                "aws_user_arn": user_arn,  # For the AWS User relationship
            }
        )

        # Create group data with AWS user relationship for each group
        for group_name in group_names:
            groups.append(
                {
                    "id": f"{cluster_name}/{group_name}",
                    "name": group_name,
                    "cluster_name": cluster_name,
                    "aws_user_arn": user_arn,  # For the AWS User relationship
                }
            )

    # Process account mappings
    if account_mappings:
        logger.info(
            f"Processing mapAccounts for {len(account_mappings)} allowed accounts"
        )

        # Filter users whose account ID is in allowed accounts (reuse all_rbac_users from above)
        account_users_added = 0
        for user in all_rbac_users:
            user_account_id = parse_aws_account_from_kube_user(user["name"])
            if user_account_id and user_account_id in account_mappings:
                # Add AWS relationship properties for both role and user matching
                account_user = {
                    "id": user["id"],
                    "name": user["name"],
                    "cluster_name": cluster_name,
                    "aws_role_arn": user["name"],  # Try matching as AWS role
                    "aws_user_arn": user["name"],  # Try matching as AWS user
                    "aws_account_id": user_account_id,  # For debugging/logging
                }
                users.append(account_user)
                account_users_added += 1

        logger.info(
            f"Added {account_users_added} users from mapAccounts (allowed accounts: {account_mappings})"
        )

    logger.info(
        f"Transformed {len(users)} users and {len(groups)} groups with AWS role/user/account mappings"
    )

    return {"users": users, "groups": groups}


@timeit
@aws_handle_regions
def get_oidc_provider(
    boto3_session: boto3.session.Session, region: str, cluster_name: str
) -> List[Dict[str, Any]]:
    """
    Get external OIDC identity provider (just okta right now) configurations for an EKS cluster.

    Returns raw AWS API responses for configured external identity providers.
    """
    client = boto3_session.client("eks", region_name=region)
    oidc_providers = []

    # Extract just the cluster name from ARN if needed
    # ARN format: arn:aws:eks:region:account:cluster/cluster-name
    if cluster_name.startswith("arn:aws:eks:"):
        cluster_name = cluster_name.split("/")[-1]

    # Get configured external identity provider configs
    configs_response = client.list_identity_provider_configs(clusterName=cluster_name)

    for config in configs_response["identityProviderConfigs"]:
        if config["type"] == "oidc":
            # Get detailed config for this OIDC provider
            detail_response = client.describe_identity_provider_config(
                clusterName=cluster_name,
                identityProviderConfig={"type": "oidc", "name": config["name"]},
            )

            oidc_providers.append(detail_response["identityProviderConfig"]["oidc"])

    return oidc_providers


def transform_oidc_provider(
    oidc_providers: List[Dict[str, Any]],
    cluster_name: str,
) -> List[Dict[str, Any]]:
    transformed_providers = []

    for provider in oidc_providers:
        # Extract fields from raw AWS API response
        provider_name = provider["identityProviderConfigName"]
        issuer_url = provider["issuerUrl"]

        # Create a unique ID for the external OIDC provider
        # Format: cluster_name/oidc/provider_name
        provider_id = f"{cluster_name}/oidc/{provider_name}"

        transformed_provider = {
            "id": provider_id,
            "issuer_url": issuer_url,
            "cluster_name": cluster_name,
            "k8s_platform": "eks",
            "client_id": provider.get("clientId", ""),
            "status": provider.get("status", "UNKNOWN"),
            "name": provider_name,
            "arn": provider.get("identityProviderConfigArn", ""),
        }

        transformed_providers.append(transformed_provider)

    return transformed_providers


def load_oidc_provider(
    neo4j_session: neo4j.Session,
    oidc_providers: List[Dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    """
    Load EKS OIDC provider into Neo4j using schema-based loading.
    """
    logger.info("Loading EKS OIDC provider")
    load(
        neo4j_session,
        KubernetesOIDCProviderSchema(),
        oidc_providers,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


def load_aws_role_mappings(
    neo4j_session: neo4j.Session,
    users: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
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


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    logger.debug("Running cleanup job for EKS AWS Role relationships")

    cleanup_job = GraphJob.from_node_schema(
        KubernetesUserSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)

    cleanup_job = GraphJob.from_node_schema(
        KubernetesGroupSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)


def sync(
    neo4j_session: neo4j.Session,
    k8s_client: K8sClient,
    boto3_session: boto3.session.Session,
    region: str,
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    """
    Sync EKS identity providers:
    1. AWS IAM mappings (aws-auth ConfigMap mapRoles, mapUsers, mapAccounts)
    2. External OIDC providers (EKS API)
    """
    logger.info(f"Starting EKS identity provider sync for cluster {cluster_name}")

    # 1. Sync AWS IAM role mappings (aws-auth ConfigMap)
    logger.info("Syncing AWS IAM role and user mappings from aws-auth ConfigMap")
    configmap = get_aws_auth_configmap(k8s_client)
    parsed_mappings = parse_aws_auth_mappings(configmap)

    if (
        parsed_mappings["roles"]
        or parsed_mappings["users"]
        or parsed_mappings["accounts"]
    ):
        transformed_data = transform_aws_auth_mappings(
            parsed_mappings["roles"],
            parsed_mappings["users"],
            parsed_mappings["accounts"],
            parsed_mappings["templated_roles"],
            parsed_mappings["templated_users"],
            cluster_name,
            k8s_client,
        )
        load_aws_role_mappings(
            neo4j_session,
            transformed_data["users"],
            transformed_data["groups"],
            update_tag,
            cluster_id,
            cluster_name,
        )
        logger.info(
            f"Successfully synced {len(parsed_mappings['roles'])} AWS IAM role mappings "
            f"and {len(parsed_mappings['users'])} AWS IAM user mappings"
        )
    else:
        logger.info("No role or user mappings found in aws-auth ConfigMap")

    # 2. Sync External OIDC providers (EKS API)
    logger.info("Syncing external OIDC providers from EKS API")

    # Get OIDC providers from EKS API
    oidc_providers = get_oidc_provider(boto3_session, region, cluster_name)

    if oidc_providers:
        # Transform OIDC providers (infrastructure metadata only)
        transformed_oidc_providers = transform_oidc_provider(
            oidc_providers, cluster_name
        )

        # Load OIDC providers
        load_oidc_provider(
            neo4j_session,
            transformed_oidc_providers,
            update_tag,
            cluster_id,
            cluster_name,
        )
        logger.info(
            f"Successfully synced {len(oidc_providers)} external OIDC providers"
        )
    else:
        logger.info("No external OIDC providers found for cluster")

    # Cleanup
    common_job_parameters = {
        "UPDATE_TAG": update_tag,
        "CLUSTER_ID": cluster_id,
    }
    cleanup(neo4j_session, common_job_parameters)

    logger.info(
        f"Successfully completed EKS identity provider sync for cluster {cluster_name}"
    )
