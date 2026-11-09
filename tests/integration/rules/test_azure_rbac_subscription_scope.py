import pytest

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.delegation_boundary_modifiable import (
    delegation_boundary_modifiable,
)
from cartography.rules.data.rules.identity_administration_privileges import (
    identity_administration_privileges,
)
from cartography.rules.data.rules.policy_administration_privileges import (
    policy_administration_privileges,
)

OWNER_GUID = "8e3af657-a8ff-443c-a75c-2fe8c4bcb635"
SUB_A = "00000000-0000-0000-0000-00000000000a"
SUB_B = "00000000-0000-0000-0000-00000000000b"


def _azure_fact(rule):
    return next(fact for fact in rule.facts if fact.id.startswith("azure_"))


@pytest.mark.parametrize(
    "rule",
    [
        delegation_boundary_modifiable,
        identity_administration_privileges,
        policy_administration_privileges,
    ],
    ids=lambda rule: rule.id,
)
def test_inherited_assignment_pairs_each_subscription_with_its_own_role_copy(
    neo4j_session,
    rule,
):
    """
    A role assignment inherited from a management group is listed by every
    subscription, so it is one node linked to each subscription and to each
    subscription's copy of the role definition. The fact must report one row per
    subscription, not one per (subscription, copy) pair.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (sub_a:AzureSubscription {id: $sub_a})
        CREATE (sub_b:AzureSubscription {id: $sub_b})
        CREATE (ra:AzureRoleAssignment {
            id: '/providers/Microsoft.Management/managementGroups/root/providers/Microsoft.Authorization/roleAssignments/ra-1',
            scope: '/providers/Microsoft.Management/managementGroups/root'
        })
        CREATE (user:EntraUser:EntraPrincipal {
            id: 'user-1',
            user_principal_name: 'admin@example.com'
        })
        CREATE (perm:AzurePermissions {actions: ['*'], not_actions: []})
        MERGE (sub_a)-[:RESOURCE]->(ra)
        MERGE (sub_b)-[:RESOURCE]->(ra)
        MERGE (user)-[:HAS_ROLE_ASSIGNMENT]->(ra)
        WITH sub_a, sub_b, ra, perm
        UNWIND [sub_a, sub_b] AS sub
        CREATE (rd:AzureRoleDefinition {
            id: '/subscriptions/' + sub.id + '/providers/Microsoft.Authorization/roleDefinitions/' + $owner,
            role_name: 'Owner'
        })
        MERGE (sub)-[:RESOURCE]->(rd)
        MERGE (ra)-[:ROLE_ASSIGNED]->(rd)
        MERGE (rd)-[:HAS_PERMISSIONS]->(perm)
        """,
        sub_a=SUB_A,
        sub_b=SUB_B,
        owner=OWNER_GUID,
    )
    fact = _azure_fact(rule)

    findings = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_query)

    assert sorted((row["account_id"], row["policy_id"]) for row in findings) == [
        (
            sub,
            f"/subscriptions/{sub}/providers/Microsoft.Authorization/roleDefinitions/{OWNER_GUID}",
        )
        for sub in (SUB_A, SUB_B)
    ]
    visual_rows = list(neo4j_session.run(fact.cypher_visual_query))
    assert len(visual_rows) == 2
