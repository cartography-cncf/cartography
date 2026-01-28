from typing import Any
from typing import Dict
from typing import List

from neo4j import Session

from cartography.client.core.tx import read_list_of_dicts_tx


def get_aws_admin_like_principals(neo4j_session: Session) -> List[Dict[str, Any]]:
    """
    Retrieve AWS principals with admin-like privileges.

    This function identifies AWS principals that have IAM policies allowing broad access
    with both ``resource=*`` and ``action=*`` permissions, indicating administrator-level
    privileges.

    Args:
        neo4j_session (Session): The Neo4j session object for database queries.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing information about
            admin-like principals. Each dictionary contains:

            - ``account_name`` (str): The name of the AWS account
            - ``account_id`` (str): The AWS account ID
            - ``principal_name`` (str): The name of the principal (user, role, etc.)
            - ``policy_name`` (str): The name of the policy granting admin privileges

    Examples:
        >>> principals = get_aws_admin_like_principals(session)
        >>> print(principals)
        [
            {
                'account_name': 'my_account',
                'account_id': '1234',
                'principal_name': 'admin_role',
                'policy_name': 'highly_privileged_policy',
            },
        ]

    Note:
        The function specifically looks for IAM policy statements with:

        - ``effect = 'Allow'``
        - ``resource`` containing ``*`` (wildcard)
        - ``action`` containing ``*`` (wildcard)

        Results are ordered by account name and principal name for consistent output.

    See Also:
        Original query implementation by Marco Lancini:
        https://github.com/marco-lancini/cartography-queries/blob/4d1f3913facdce7a4011141a4c7a15997c03553f/queries/queries.json#L236
    """
    query = """
    MATCH (stat:AWSPolicyStatement)<-[:STATEMENT]-(policy:AWSPolicy)<-[:POLICY]-(p:AWSPrincipal)
        <-[:RESOURCE]-(a:AWSAccount)
    WHERE
        stat.effect = 'Allow' AND any(x IN stat.resource WHERE x='*')
        AND any(x IN stat.action WHERE x='*')
    RETURN a.name AS account_name, a.id AS account_id, p.name AS principal_name, policy.name AS policy_name
    ORDER BY account_name, principal_name
    """
    return neo4j_session.read_transaction(read_list_of_dicts_tx, query)
