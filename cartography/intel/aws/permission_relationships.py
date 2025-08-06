import logging
import os
import re
from string import Template
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Pattern
from typing import Tuple

import boto3
import neo4j
import yaml

from cartography.graph.statement import GraphStatement
from cartography.util import timeit

logger = logging.getLogger(__name__)


def evaluate_clause(clause: str, match: str) -> bool:
    """Evaluates the a clause in IAM. Clauses can be AWS [not]actions and [not]resources

    Arguments:
        clause {str, re.Pattern} -- The clause you are evaluating against. Clauses can use
            variable length wildcards (*)
            fixed length wildcards (?)
        match {str} -- The item to match against.

    Returns:
        [bool] -- True if the clause matched, False otherwise
    """
    result = compile_regex(clause).fullmatch(match)
    return result is not None


def evaluate_notaction_for_permission(statement: Dict, permission: str) -> bool:
    """Return whether an IAM 'notaction' clause in the given statement applies to the item"""
    if "notaction" not in statement:
        return False
    for clause in statement["notaction"]:
        if evaluate_clause(clause, permission):
            return True
    return False


def evaluate_action_for_permission(statement: Dict, permission: str) -> bool:
    """Return whether an IAM 'action' clause in the given statement applies to the permission"""
    if "action" not in statement:
        return True
    for clause in statement["action"]:
        if evaluate_clause(clause, permission):
            return True
    return False


def evaluate_resource_for_permission(statement: Dict, resource_arn: str) -> bool:
    """Return whether the given IAM 'resource' statement applies to the resource_arn"""
    if "resource" not in statement:
        return False
    for clause in statement["resource"]:
        if evaluate_clause(clause, resource_arn):
            return True
    return False


def evaluate_notresource_for_permission(statement: Dict, resource_arn: str) -> bool:
    """Return whether an IAM 'notresource' clause in the given statement applies to the resource_arn"""
    if "notresource" not in statement:
        return False
    for clause in statement["notresource"]:
        if evaluate_clause(clause, resource_arn):
            return True
    return False


def evaluate_statements_for_permission(
    statements: List[Dict],
    permission: str,
    resource_arn: str,
) -> bool:
    """Evaluate an entire statement for a specific permission against a resource

    Arguments:
        statements {[dict]} -- The list of statements to be evaluated
        permission {str} -- The permission to evaluate. ex "s3:GetObject"
        resource_arn {[type]} -- The resource to test the permission against

    Returns:
        [bool] -- If the statement grants the specific permission to the resource
    """
    allowed = False
    for statement in statements:
        if not evaluate_notaction_for_permission(statement, permission):
            if evaluate_action_for_permission(statement, permission):
                if evaluate_resource_for_permission(statement, resource_arn):
                    if not evaluate_notresource_for_permission(statement, resource_arn):
                        return True

    return allowed


def evaluate_policy_for_permissions(
    statements: List[Dict],
    permissions: List[str],
    resource_arn: str,
) -> Tuple[bool, bool]:
    """Evaluates an entire policy for specific permissions to a resource.
    AWS Policy evaluation reference
    https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html

    Arguments:
        statements {[dict]} -- The list of statements for the policy
        permissions {[str]} -- The permissions to evaluate
        resource_arn {[type]} -- The resource to test the permission against

    Returns:
        [(bool, bool)] -- (allowed_by_policy, explicitly_denied_by_policy)
        return cases
        (True, False) - The policy allows the action
        (False, False) - The poliy does not allow the action, but also doesn't explicitly deny it
        (False, True) - The policy specifically denies the action. There is no need to evaluate other policies
    """
    allow_statements = [s for s in statements if s["effect"] == "Allow"]
    deny_statements = [s for s in statements if s["effect"] == "Deny"]
    for permission in permissions:
        if evaluate_statements_for_permission(
            deny_statements,
            permission,
            resource_arn,
        ):
            # The action explicitly denied then no other policy can override it
            return False, True
        else:
            if evaluate_statements_for_permission(
                allow_statements,
                permission,
                resource_arn,
            ):
                # The action is allowed by this policy
                return True, False
    # The action is not allowed by this policy, but not specifically denied either
    return False, False


def principal_allowed_on_resource(
    policies: Dict,
    resource_arn: str,
    permissions: List[str],
) -> bool:
    """Evaluates an entire set of policies for a specific resource for a specific permission.


    Arguments:
        policies {[dict]} -- The policys to evaluate
        resource_arn {str} -- The resource to test the permission against
        permissions {[str]} -- The permissions to evaluate

    Returns:
        [bool] -- True if the policies allow the permission against the resource
    """
    if not isinstance(permissions, list):
        raise ValueError("permissions is not a list")
    granted = False
    for _, statements in policies.items():
        allowed, explicit_deny = evaluate_policy_for_permissions(
            statements,
            permissions,
            resource_arn,
        )

        if explicit_deny:

            return False
        if not granted and allowed:
            granted = True

    return granted


def calculate_permission_relationships(
    principals: Dict,
    resource_arns: List[str],
    permissions: List[str],
) -> List[Dict]:
    """Evaluate principals permissions to resources
    This currently only evaluates policies on IAM principals. It does not take into account
    Resource Policies - Policies attached to the resource instead of the IAM principal
    Permission Boundaries - Boundaries for an IAM principal
    Session Policies - Special policies for Federated users

    AWS Policy evaluation reference
    https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html

    Arguments:
        principals {[dict]} -- The principals to check permission for
        resource_arns {[str]} -- The resources to test the permission against
        permissions {[str]} -- The permissions to evaluate

    Returns:
        [dict] -- The allowed mappings
    """
    allowed_mappings: List[Dict] = []
    for resource_arn in resource_arns:
        for principal_arn, policies in principals.items():
            if principal_allowed_on_resource(policies, resource_arn, permissions):
                allowed_mappings.append(
                    {"principal_arn": principal_arn, "resource_arn": resource_arn},
                )
    return allowed_mappings


def parse_statement_node(node_group: List[Any]) -> List[Any]:
    """Parse a dict from group of Neo4J node

    Arguments:
        node_group {[Neo4j.Node]} -- the node to parse

    Returns:
        [list] -- A list of statements from the node
    """
    return [n._properties for n in node_group]


def compile_regex(item: str) -> Pattern:
    r"""Compile a clause into a regex. Clause checking in AWS is case insensitive
    The following regex symbols will be replaced to make AWS * and ? matching a regex
    * -> .* (wildcard)
    ? -> .? (single character wildcard)
    . -> \\. (make period a literal period)

    Arguments:
        item {str} -- the item to create the regex for

    Returns:
        [re.Pattern] -- The precompiled regex pattern.
        If the pattern does not compile it will return an re.Pattern of empty string
    """

    if isinstance(item, str):
        item = item.replace(".", "\\.").replace("*", ".*").replace("?", ".?")
        try:
            return re.compile(item, flags=re.IGNORECASE)
        except re.error:
            logger.warning(f"Regex did not compile for {item}")
            # in this case it must still return a regex.
            # So it will return an re.Pattern of empry stringm
            return re.compile("", flags=re.IGNORECASE)
    else:
        return item


def compile_statement(statements: List[Any]) -> List[Any]:
    """Compile a statement by precompiling the regex for the relevant clauses. This is done to boost
    performance by not recompiling the regex over and over again.

    Arguments:
        statements {dict} -- The statement dictionary

    Returns:
        [dict] -- the compiled statement
    """
    properties = ["action", "resource", "notresource", "notaction"]
    for statement in statements:
        for statement_property in properties:
            if statement_property in statement:
                statement[statement_property] = [
                    compile_regex(item) for item in statement[statement_property]
                ]
    return statements


def get_principals_for_account(neo4j_session: neo4j.Session, account_id: str) -> Dict:
    get_policy_query = """
    MATCH
    (acc:AWSAccount{id:$AccountId})-[:RESOURCE]->
    (principal:AWSPrincipal)-[:POLICY]->
    (policy:AWSPolicy)-[:STATEMENT]->
    (statements:AWSPolicyStatement)
    RETURN
    DISTINCT principal.arn as principal_arn, policy.id as policy_id, collect(statements) as statements
    """
    results = neo4j_session.run(
        get_policy_query,
        AccountId=account_id,
    )
    principals: Dict[Any, Any] = {}
    for r in results:
        principal_arn = r["principal_arn"]
        policy_id = r["policy_id"]
        statements = r["statements"]
        if principal_arn not in principals:
            principals[principal_arn] = {}
        principals[principal_arn][policy_id] = compile_statement(
            parse_statement_node(statements),
        )
    return principals


def safe_substitute_schema(schema: str, properties: Dict[str, Any]) -> str:
    """Safely substitute properties into the schema template.

    Arguments:
        schema {str} -- The resource ARN schema template
        properties {Dict[str, Any]} -- The properties to substitute

    Returns:
        str -- The schema with properties substituted
    """
    property_pattern = r"\{\{([^}]+)\}\}"
    template_schema = re.sub(property_pattern, r"$\1", schema)

    template = Template(template_schema)
    return template.safe_substitute(properties)


def calculate_condition_clause(
    conditional_target_relations: Optional[List[str]] = None,
) -> str:
    if not conditional_target_relations:
        return ""
    return " WHERE " + " AND ".join(
        [
            f"((resource)-[:{relation}]->() OR ()-[:{relation}]->(resource))"
            for relation in conditional_target_relations
        ]
    )


def extract_property_names_from_schema(schema: str) -> List[str]:
    property_pattern = r"\{\{([^}]+)\}\}"
    return re.findall(property_pattern, schema)


def get_resource_arns(
    neo4j_session: neo4j.Session,
    account_id: str,
    node_label: str,
    conditional_target_relations: Optional[List[str]] = None,
    resource_arn_schema: str = "{{arn}}",
) -> List[str]:
    if not isinstance(resource_arn_schema, str):
        raise ValueError("resource_arn_schema is not a string")

    # Extract properties from the schema to form the return clause
    properties = extract_property_names_from_schema(resource_arn_schema)
    return_clause = "RETURN " + ", ".join(
        f"resource.{prop} as {prop}" for prop in properties
    )

    get_resource_query = Template(
        """
    MATCH (acc:AWSAccount{id:$AccountId})-[:RESOURCE]->(resource:$node_label)
    $condition_clause
    $return_clause
    """
    )

    condition_clause = calculate_condition_clause(conditional_target_relations)

    get_resource_query_template = get_resource_query.safe_substitute(
        node_label=node_label,
        return_clause=return_clause,
        condition_clause=condition_clause,
    )
    results = list(
        neo4j_session.run(
            get_resource_query_template,
            AccountId=account_id,
        )
    )

    if results and any(value is None for value in results[0].values()):
        logger.warning(
            f"Skipping... The target node label '{node_label}' doesn't have the following properties: {[prop for prop, value in results[0].items() if value is None]}."
            f"Please add/update the resource_arn_schema value in the permission_relationships.yaml file, to make sure the target node has the required properties."
        )
        return []

    # Generate ARN strings by safe substituting properties into the schema
    resource_arns = []
    for r in results:
        properties_dict = dict(r)

        resource_arn = safe_substitute_schema(resource_arn_schema, properties_dict)
        if resource_arn:
            resource_arns.append(resource_arn)

    if not resource_arns:
        logger.warning(
            f"Could not fetch associated resources properties for target node '{node_label}'. "
            f"If 'resource_arn_schema' is defined, "
            f"make sure it follows the format of the resource ARN in your policy's resource definition."
        )
        return []

    return resource_arns


def extract_properties_from_arn(arn: str, schema: str) -> Dict[str, str]:
    # Not to proud of this regex function, but it works for now
    # TODO: Refactor this to use a more efficient regex
    properties = extract_property_names_from_schema(schema)
    schema_regex = schema

    prop_patterns = {}

    for prop in properties:
        prop_start = schema.find(f"{{{{{prop}}}}}")
        prop_end = prop_start + len(f"{{{{{prop}}}}}")

        next_chars = []
        for i in range(prop_end, len(schema)):
            if schema[i] not in ["{", "}"]:
                next_chars.append(schema[i])
                break

        if next_chars:
            capture_pattern = f"[^{''.join(next_chars)}]+"
        else:
            capture_pattern = ".*"

        prop_patterns[prop] = capture_pattern
        schema_regex = schema_regex.replace(
            f"{{{{{prop}}}}}", f"(?P<{prop}>{capture_pattern})"
        )

    schema_regex = re.escape(schema_regex)

    for prop, capture_pattern in prop_patterns.items():
        escaped_pattern = re.escape(f"(?P<{prop}>{capture_pattern})")
        schema_regex = schema_regex.replace(
            escaped_pattern, f"(?P<{prop}>{capture_pattern})"
        )

    pattern = re.compile(schema_regex)
    match = pattern.match(arn)

    if match is None:
        return {}

    return match.groupdict()


def load_principal_mappings(
    neo4j_session: neo4j.Session,
    principal_mappings: List[Dict],
    node_label: str,
    relationship_name: str,
    update_tag: int,
    resource_arn_schema: str = "{{arn}}",
) -> None:
    if not principal_mappings:
        return

    for mapping in principal_mappings:
        resource_arn = mapping["resource_arn"]
        extracted_props = extract_properties_from_arn(resource_arn, resource_arn_schema)

        # Create WHERE conditions for each property
        where_conditions = []
        for prop_name, prop_value in extracted_props.items():
            where_conditions.append(f"resource.{prop_name} = '{prop_value}'")

        where_clause = " AND ".join(where_conditions)

        map_policy_query = Template(
            """
        MATCH (principal:AWSPrincipal{arn:$principal_arn})
        MATCH (resource:$node_label)
        WHERE $where_clause
        MERGE (principal)-[r:$relationship_name]->(resource)
        SET r.lastupdated = $aws_update_tag
        """,
        )
        map_policy_query_template = map_policy_query.safe_substitute(
            node_label=node_label,
            relationship_name=relationship_name,
            where_clause=where_clause,
        )
        neo4j_session.run(
            map_policy_query_template,
            principal_arn=mapping["principal_arn"],
            aws_update_tag=update_tag,
        )


def cleanup_rpr(
    neo4j_session: neo4j.Session,
    node_label: str,
    relationship_name: str,
    update_tag: int,
    current_aws_id: str,
) -> None:
    logger.info(
        "Cleaning up relationship '%s' for node label '%s'",
        relationship_name,
        node_label,
    )
    cleanup_rpr_query = Template(
        """
        MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(principal:AWSPrincipal)-[r:$relationship_name]->
        (resource:$node_label)
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE  DELETE (r) return COUNT(*) as TotalCompleted
    """,
    )
    cleanup_rpr_query_template = cleanup_rpr_query.safe_substitute(
        node_label=node_label,
        relationship_name=relationship_name,
    )

    statement = GraphStatement(
        cleanup_rpr_query_template,
        {"UPDATE_TAG": update_tag, "AWS_ID": current_aws_id},
        True,
        1000,
        parent_job_name=f"{relationship_name}:{node_label}",
        parent_job_sequence_num=1,
    )
    statement.run(neo4j_session)


def parse_permission_relationships_file(file_path: str) -> List[Any]:
    try:
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)
        with open(file_path) as f:
            relationship_mapping = yaml.load(f, Loader=yaml.FullLoader)
        return relationship_mapping
    except FileNotFoundError:
        logger.warning(
            f"Permission relationships mapping file {file_path} not found, skipping sync stage {__name__}. "
            f"If you want to run this sync, please explicitly set a value for --permission-relationships-file in the "
            f"command line interface.",
        )
        return []


def validate_resource_arn_schema(raw_resource_arn_schema: str) -> str:
    """To validate the resource ARN schema"""
    if not isinstance(raw_resource_arn_schema, str):
        return "{{arn}}"
    properties = extract_property_names_from_schema(raw_resource_arn_schema)
    if not properties:
        logger.warning(
            f"No properties found in resource ARN schema: {raw_resource_arn_schema}.Defaulting to '{{arn}}'."
        )
        return "{{arn}}"
    return raw_resource_arn_schema


def is_valid_rpr(rpr: Dict) -> bool:
    required_fields = ["permissions", "relationship_name", "target_label"]
    for field in required_fields:
        if field not in rpr:
            return False

    return True


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info(
        "Syncing Permission Relationships for account '%s'.",
        current_aws_account_id,
    )
    principals = get_principals_for_account(neo4j_session, current_aws_account_id)
    pr_file = common_job_parameters["permission_relationships_file"]
    if not pr_file:
        logger.warning(
            "Permission relationships file was not specified, skipping. If this is not expected, please check your "
            "value of --permission-relationships-file",
        )
        return
    relationship_mapping = parse_permission_relationships_file(pr_file)
    for rpr in relationship_mapping:
        if not is_valid_rpr(rpr):
            raise ValueError(
                """
        Resource permission relationship is missing fields.
        Required fields: permissions, relationship_name, target_label"
        """,
            )
        permissions = rpr["permissions"]
        relationship_name = rpr["relationship_name"]
        target_label = rpr["target_label"]

        # Extract optional fields
        conditional_target_relations = rpr.get("conditional_target_relations")
        raw_resource_arn_schema = rpr.get("resource_arn_schema", "{{arn}}")
        resource_arn_schema = validate_resource_arn_schema(raw_resource_arn_schema)

        logger.info(
            "Syncing relationship '%s' for node label '%s'",
            relationship_name,
            target_label,
        )

        resource_arns = get_resource_arns(
            neo4j_session,
            current_aws_account_id,
            target_label,
            conditional_target_relations,
            resource_arn_schema,
        )

        allowed_mappings = calculate_permission_relationships(
            principals,
            resource_arns,
            permissions,
        )
        load_principal_mappings(
            neo4j_session,
            allowed_mappings,
            target_label,
            relationship_name,
            update_tag,
            resource_arn_schema,
        )
        cleanup_rpr(
            neo4j_session,
            target_label,
            relationship_name,
            update_tag,
            current_aws_account_id,
        )
