"""
Validation that ``Fact.identity_fields`` can actually key the rows of its own query.

``test_identity_fields.py`` checks that identity fields exist and are returned. That
leaves the shape most likely to break the contract: the query fans out over a to-many
hop and the identity omits the fan-out column, so several rows of one run collapse to a
single logical identity. A consumer keying findings on ``(rule_id, fact_id, identity)``
to reconcile them across syncs cannot represent that: it either drops a finding or
rejects the batch, and the rule silently reports nothing for the affected asset.

The analysis is in ``cartography.rules.spec.model.fanout_risks``. It cannot know a
relationship's cardinality, so the two tables below inject it. Each entry is a claim
about the data model that can be checked against ``cartography/models/``.
"""

import pytest

from cartography.rules.data.rules import RULES
from cartography.rules.spec.model import fanout_risks

# (rule_id, fact_id, rule, fact) for every fact in the registry.
_ALL_FACTS = [
    pytest.param(rule.id, fact.id, rule, fact, id=f"{rule.id}::{fact.id}")
    for rule in RULES.values()
    for fact in rule.facts
]

# `(relationship label, label of the arrow target)`: traversing `(a)-[:REL]->(b)` from
# `b` back to `a` reaches at most one node. Keyed on the pair rather than the label
# alone because a label is not a cardinality: `CONTAINS` is to-one from a blob container
# to its service but to-many from a pod to its containers, and `OWNS` is to-one from a
# Tailscale device to its user but to-many from a tag to its devices.
#
# Prefer an entry here (reusable, and it states the graph invariant once) over an entry
# in `_EXPECTED_FANOUT` (per fact).
_TO_ONE_INCOMING: frozenset[tuple[str, str]] = frozenset(
    {
        # Sub-resource ownership. Universal in cartography: a node reached by walking a
        # RESOURCE edge backwards is the single tenant/account/project that owns it.
        # This one entry accounts for the large majority of the parent columns facts
        # project (account_id, project_id, cluster_name, ...).
        ("RESOURCE", "*"),
        # An access key belongs to exactly one AWSUser.
        ("AWS_ACCESS_KEY", "AWSAccountAccessKey"),
        # A container has one parent workload.
        ("HAS_CONTAINER", "Container"),
        # An AIBOM component is keyed on its source, so it has one AIBOMSource.
        ("HAS_COMPONENT", "AIAgent"),
        # A blob container lives in one blob service, which lives in one storage account.
        ("CONTAINS", "AzureStorageBlobContainer"),
        ("USES", "AzureStorageBlobService"),
        # An Anthropic API key sits in at most one workspace.
        ("CONTAINS", "AnthropicApiKey"),
        # A Tailscale device has one owning user.
        ("OWNS", "TailscaleDevice"),
    }
)

# `(relationship label, label of the arrow target)`: traversing `(a)-[:REL]->(b)`
# forwards reaches at most one `b`.
_TO_ONE_OUTGOING: frozenset[tuple[str, str]] = frozenset(
    {
        # AWSSSMInstanceInformation.id *is* the instance id, so an instance has one.
        ("HAS_INFORMATION", "AWSSSMInstanceInformation"),
    }
)

# (fact_id, variable) -> why this fan-out cannot happen in real data. Only for facts
# where the guarantee comes from outside the graph model, so no table entry can express
# it. The normal fix for a new flag is to widen `identity_fields`, aggregate the
# variable, or add `RETURN DISTINCT`, not to add an entry here.
_EXPECTED_FANOUT: dict[tuple[str, str], str] = {
    # AWS allows one value per tag key per resource, so the `{key: 'Name'}` filter
    # selects at most one AWSTag even though TAGGED is many-to-many in general.
    ("aws_ebs_encryption_disabled", "nametag"): "one Name tag per volume",
    ("aws_ec2_imdsv2_required", "nametag"): "one Name tag per instance",
    # `a` is the account of an instance that is a member of the security group. A
    # security group and its member instances are always in the same account, so
    # a.id is functionally determined by security_group_id.
    ("aws_remote_admin_ipv4", "a"): "group and members share one account",
    ("aws_remote_admin_ipv6", "a"): "group and members share one account",
    # A Lambda has exactly one execution role: AWSLambdaToPrincipalRel matches on the
    # scalar `Role` field of the function config. Not a table entry because
    # STS_ASSUMEROLE_ALLOW also models the IAM trust-policy graph, where one principal
    # can assume many roles.
    ("aws_service_account_manipulation", "role"): "one execution role per Lambda",
    # AWS allows exactly one role per instance profile; the API's `Roles` list holds at
    # most one entry, so the `one_to_many=True` mapping on InstanceProfileToAWSRoleRel
    # cannot actually produce two. Not a table entry because ASSOCIATED_WITH is a
    # generic label used for many-to-many edges elsewhere.
    (
        "aws_service_account_manipulation_via_ec2",
        "role",
    ): "one role per instance profile",
    # SUBJECT is one-to-many, but KubernetesGroup.id is `{cluster_name}/{name}`, so
    # `g.name = 'system:masters'` pins exactly one node per binding. Contrast
    # k8s_default_sa_role_bindings, where the same query shape *is* a fan-out bug:
    # KubernetesServiceAccount ids are namespaced, so one binding can subject several
    # accounts all named 'default'.
    (
        "k8s_system_masters_cluster_role_bindings",
        "g",
    ): "one system:masters group per cluster",
    ("k8s_system_masters_role_bindings", "g"): "one system:masters group per cluster",
}


def _risks(fact):
    return fanout_risks(
        fact.cypher_query,
        fact.asset_label,
        fact.identity_fields,
        to_one_incoming=_TO_ONE_INCOMING,
        to_one_outgoing=_TO_ONE_OUTGOING,
    )


@pytest.mark.parametrize("rule_id, fact_id, rule, fact", _ALL_FACTS)
def test_identity_fields_key_the_query_rows(rule_id, fact_id, rule, fact):
    """No unexplained fan-out: two rows of one fact must not share one identity."""
    unexplained = [
        risk
        for risk in _risks(fact)
        if (fact_id, risk.variable) not in _EXPECTED_FANOUT
    ]
    assert not unexplained, (
        f"Rule '{rule_id}' fact '{fact_id}' declares identity_fields "
        f"{list(fact.identity_fields)} that may not key its own rows:\n"
        + "\n".join(f"  - {risk.detail}" for risk in unexplained)
        + "\nFix by folding the fan-out column into identity_fields, aggregating the "
        "variable (collect/count), replacing the hop with EXISTS { ... }, or adding "
        "RETURN DISTINCT when the extra rows are identical. If the fan-out cannot "
        "happen in real data, record it in _EXPECTED_FANOUT with the reason."
    )


def test_expected_fanout_allowlist_has_no_stale_entries():
    """
    Every allowlist entry must still correspond to a flagged variable.

    Without this, fixing a fact leaves a suppression behind that would mask the next
    regression on the same variable.
    """
    flagged = {
        (fact.id, risk.variable)
        for rule in RULES.values()
        for fact in rule.facts
        for risk in _risks(fact)
    }
    stale = sorted(set(_EXPECTED_FANOUT) - flagged)
    assert (
        not stale
    ), f"_EXPECTED_FANOUT entries no longer flagged and should be deleted: {stale}"
