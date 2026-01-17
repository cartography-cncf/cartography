from typing import Any
from typing import Dict
from typing import List

from neo4j import Session

from cartography.client.core.tx import read_list_of_dicts_tx


def get_aws_admin_like_principals(neo4j_session: Session) -> List[Dict[str, Any]]:
    """
    Return information on AWS principals that have admin-like privileges - that is, they have IAM policies that allow
    resource=* and action=*.

    Credit to
    https://github.com/marco-lancini/cartography-queries/blob/4d1f3913facdce7a4011141a4c7a15997c03553f/queries/
    queries.json#L236

    Returned data shape: [
        {
            'account_name': 'my_account',
            'account_id': '1234',
            'principal_name': 'admin_role',
            'policy_name': 'highly_privileged_policy',
        },
    ]
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
    return neo4j_session.execute_read(read_list_of_dicts_tx, query)
