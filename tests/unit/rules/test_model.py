import pytest

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import fanout_risks
from cartography.rules.spec.model import Framework
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import MODULE_TO_CARTOGRAPHY_INTEL
from cartography.rules.spec.model import RESERVED_FINDING_FIELDS
from cartography.rules.spec.model import returned_aliases
from cartography.sync import TOP_LEVEL_MODULES


def test_framework_normalizes_to_lowercase():
    """Test that Framework matching fields are normalized to lowercase."""
    fw = Framework(
        name="CIS AWS Foundations Benchmark",
        short_name="CIS",
        requirement="1.14",
        scope="AWS",
        revision="5.0",
        control_title="Access Keys Not Rotated",
    )
    assert fw.name == "cis aws foundations benchmark"
    assert fw.short_name == "cis"
    assert fw.scope == "aws"
    assert fw.revision == "5.0"
    assert fw.requirement == "1.14"
    assert fw.control_title == "Access Keys Not Rotated"


def test_framework_control_title_preserves_display_casing_and_is_not_filter_key():
    """Framework control_title is user-facing copy and does not participate in matching."""
    fw = Framework(
        name="CIS Kubernetes Benchmark",
        short_name="CIS",
        requirement="5.1.8",
        scope="Kubernetes",
        revision="1.12",
        control_title="Limit use of bind, impersonate, and escalate permissions",
    )

    assert (
        fw.control_title == "Limit use of bind, impersonate, and escalate permissions"
    )
    assert fw.matches("cis", "kubernetes", "1.12")


def test_framework_optional_fields():
    """Test that Framework works with optional scope and revision."""
    # Only required fields
    fw_minimal = Framework(
        name="NIST Framework",
        short_name="NIST",
        requirement="AC-1",
    )
    assert fw_minimal.scope is None
    assert fw_minimal.revision is None
    assert fw_minimal.control_title is None
    assert fw_minimal.requirement == "ac-1"

    # With scope only
    fw_with_scope = Framework(
        name="CIS Benchmark",
        short_name="CIS",
        requirement="1.1",
        scope="aws",
    )
    assert fw_with_scope.scope == "aws"
    assert fw_with_scope.revision is None

    # With revision only
    fw_with_revision = Framework(
        name="SOC 2",
        short_name="SOC2",
        requirement="CC6.1",
        revision="2017",
    )
    assert fw_with_revision.scope is None
    assert fw_with_revision.revision == "2017"


def test_framework_matches_case_insensitive():
    """Test that Framework.matches() is case-insensitive."""
    fw = Framework(
        name="CIS AWS Foundations Benchmark",
        short_name="CIS",
        requirement="1.14",
        scope="aws",
        revision="5.0",
    )
    # All match variations should work
    assert fw.matches("CIS")
    assert fw.matches("cis")
    assert fw.matches("CIS", "AWS")
    assert fw.matches("cis", "aws", "5.0")
    assert fw.matches(short_name="CIS", scope="AWS", revision="5.0")


def test_framework_matches_partial_filter():
    """Test that Framework.matches() works with partial filters."""
    fw = Framework(
        name="CIS AWS Foundations Benchmark",
        short_name="CIS",
        requirement="1.14",
        scope="aws",
        revision="5.0",
    )
    # Partial matches
    assert fw.matches("cis")
    assert fw.matches("cis", "aws")
    assert fw.matches(scope="aws")
    assert fw.matches(revision="5.0")

    # Non-matches
    assert not fw.matches("nist")
    assert not fw.matches("cis", "gcp")
    assert not fw.matches("cis", "aws", "4.0")


def test_framework_matches_with_optional_fields():
    """Test that Framework.matches() handles optional fields correctly."""
    # Framework without scope
    fw_no_scope = Framework(
        name="NIST Framework",
        short_name="NIST",
        requirement="AC-1",
    )
    assert fw_no_scope.matches("nist")
    assert not fw_no_scope.matches("nist", "aws")  # Can't match scope if None

    # Framework without revision
    fw_no_revision = Framework(
        name="CIS Benchmark",
        short_name="CIS",
        requirement="1.1",
        scope="aws",
    )
    assert fw_no_revision.matches("cis")
    assert fw_no_revision.matches("cis", "aws")
    assert not fw_no_revision.matches(
        "cis", "aws", "5.0"
    )  # Can't match revision if None


def test_all_module_keys_in_mapping_except_cross_cloud():
    """
    Test that all keys from the Module enum are present in MODULE_TO_CARTOGRAPHY_INTEL
    except for CROSS_CLOUD.
    """
    # Get all module enum values except CROSS_CLOUD
    expected_modules = {module for module in Module if module != Module.CROSS_CLOUD}

    # Get the keys from the mapping dictionary
    mapping_keys = set(MODULE_TO_CARTOGRAPHY_INTEL.keys())

    # Verify that all expected modules are in the mapping
    missing_modules = expected_modules - mapping_keys
    extra_modules = mapping_keys - expected_modules

    # Assert no modules are missing from the mapping
    assert (
        missing_modules == set()
    ), f"The following modules are missing from MODULE_TO_CARTOGRAPHY_INTEL: {missing_modules}"

    # Assert no extra modules are in the mapping
    assert (
        extra_modules == set()
    ), f"The following unexpected modules are in MODULE_TO_CARTOGRAPHY_INTEL: {extra_modules}"


def test_cross_cloud_not_in_mapping():
    """
    Test that CROSS_CLOUD is specifically not in the MODULE_TO_CARTOGRAPHY_INTEL mapping.
    """
    assert (
        Module.CROSS_CLOUD not in MODULE_TO_CARTOGRAPHY_INTEL
    ), "CROSS_CLOUD should not be present in MODULE_TO_CARTOGRAPHY_INTEL"


def test_mapping_values_exists():
    """
    Test that all values in MODULE_TO_CARTOGRAPHY_INTEL are strings.
    """
    for module, intel_name in MODULE_TO_CARTOGRAPHY_INTEL.items():
        assert intel_name is not None, f"Value for {module} should not be None"
        assert isinstance(intel_name, str), f"Value for {module} should be a string"
        assert intel_name != "", f"Value for {module} should not be empty"
        assert (
            intel_name in TOP_LEVEL_MODULES
        ), f"Value for {module} ('{intel_name}') should be a valid Cartography INTEL module"


def _fact_kwargs(**overrides) -> dict:
    """Minimal valid Fact kwargs, overridable per test."""
    kwargs = dict(
        id="example-fact",
        name="Example",
        description="Example",
        module=Module.AWS,
        maturity=Maturity.EXPERIMENTAL,
        cypher_query="MATCH (u:AWSUser) RETURN u.arn AS user_arn",
        cypher_visual_query="MATCH (u:AWSUser) RETURN *",
        cypher_count_query="MATCH (u:AWSUser) RETURN COUNT(u) AS count",
        identity_fields=("user_arn",),
        asset_label="AWSUser",
        asset_id_field="user_arn",
    )
    kwargs.update(overrides)
    return kwargs


def test_fact_accepts_a_coherent_declaration():
    """The baseline used by the negative cases below must itself be valid."""
    assert Fact(**_fact_kwargs()).asset_label == "AWSUser"


def test_fact_rejects_reserved_finding_field_aliases():
    """`source` and `extra` belong to the Finding base and must not be aliased."""
    for reserved in sorted(RESERVED_FINDING_FIELDS):
        query = f"MATCH (u:AWSUser) RETURN u.arn AS user_arn, u.name AS {reserved}"
        with pytest.raises(ValueError, match="reserved Finding field"):
            Fact(**_fact_kwargs(cypher_query=query))


def test_fact_allows_reserved_name_as_intermediate_with_alias():
    """Only output columns are reserved; query-internal bindings are not.

    `WITH x AS source` never reaches the Finding model, so rejecting it would be
    a false positive.
    """
    query = "MATCH (u:AWSUser) WITH u, u.name AS source RETURN u.arn AS user_arn"
    assert Fact(**_fact_kwargs(cypher_query=query)).asset_id_field == "user_arn"


def test_fact_rejects_asset_label_not_bound_by_query():
    """A fact cannot claim an asset label its own query never binds."""
    with pytest.raises(ValueError, match="never binds a variable to that label"):
        Fact(**_fact_kwargs(asset_label="UserAccount"))


def test_fact_rejects_asset_id_field_only_bound_in_intermediate_with():
    """An alias produced by a `WITH` is query state, not an output column."""
    query = "MATCH (u:AWSUser) WITH u, u.arn AS user_arn RETURN u.name AS other"
    with pytest.raises(ValueError, match="is not returned by its cypher_query"):
        Fact(**_fact_kwargs(cypher_query=query))


def test_fact_rejects_identity_field_not_returned_by_query():
    """An identity a consumer cannot read from the output is not an identity."""
    with pytest.raises(ValueError, match="cypher_query does not return"):
        Fact(**_fact_kwargs(identity_fields=("user_arn", "policy_arn")))


def test_fact_rejects_asset_id_field_from_a_different_node():
    """The (label, id) anchor must describe one node, not two."""
    query = "MATCH (u:AWSUser) MATCH (r:AWSRole) RETURN r.arn AS user_arn"
    with pytest.raises(ValueError, match="reads no property off"):
        Fact(**_fact_kwargs(cypher_query=query))


def test_fact_ignores_return_inside_a_call_subquery():
    """A nested `CALL { ... RETURN ... }` is not the fact's projection."""
    query = (
        "MATCH (u:AWSUser) CALL { MATCH (x:AWSRole) RETURN count(x) AS n } "
        "RETURN u.arn AS user_arn, n"
    )
    assert Fact(**_fact_kwargs(cypher_query=query)).asset_id_field == "user_arn"


def test_returned_aliases_reads_only_the_final_projection():
    """Aliases come from the final RETURN: `AS x` or a bare carried variable."""
    query = """
    MATCH (c:KubernetesCluster)-[:RESOURCE]->(p:KubernetesPod)
    WITH c.name AS cluster_name, p.namespace AS namespace, p.name AS pod_name
    ORDER BY pod_name
    WITH cluster_name, namespace, collect(pod_name) AS pod_names
    MATCH (ns:KubernetesNamespace)
    RETURN DISTINCT
        ns.id AS namespace_id,
        coalesce(ns.friendly_name, 'a, b') AS label,
        CASE WHEN size(pod_names) > 1 THEN 'many' ELSE 'one' END AS kind,
        namespace,
        pod_names,
        cluster_name
    ORDER BY namespace_id LIMIT 10
    """
    assert returned_aliases(query) == {
        "namespace_id",
        "label",
        "kind",
        "namespace",
        "pod_names",
        "cluster_name",
    }


# `(parent)-[:RESOURCE]->(child)` ownership, the one invariant these cases rely on.
_TO_ONE_IN = frozenset({("RESOURCE", "*")})
_TO_ONE_OUT: frozenset[tuple[str, str]] = frozenset()


def _risks(
    query: str, identity_fields: tuple[str, ...], asset_label: str = "GCPInstance"
):
    return {
        (risk.variable, risk.condition)
        for risk in fanout_risks(
            query,
            asset_label,
            identity_fields,
            to_one_incoming=_TO_ONE_IN,
            to_one_outgoing=_TO_ONE_OUT,
        )
    }


_FANOUT_QUERY = """
MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
MATCH (instance)-[:NETWORK_INTERFACE]->(:GCPNetworkInterface)-[:RESOURCE]->(access:GCPNicAccessConfig)
RETURN
    instance.id AS instance_id,
    project.id AS project_id,
    access.public_ip AS external_ip
"""


def test_fanout_risks_flags_a_projected_column_the_identity_omits():
    """The reported shape: one row per access config, identity keyed on the instance.

    `project` must not be flagged alongside it: it is reached by walking a RESOURCE
    edge backwards, so it is the single owning project, not a fan-out.
    """
    assert _risks(_FANOUT_QUERY, ("instance_id",)) == {("access", "projected")}


def test_fanout_risks_accepts_the_identity_that_includes_the_fan_out_column():
    """Folding the fan-out column into the identity resolves it."""
    assert _risks(_FANOUT_QUERY, ("instance_id", "external_ip")) == set()


def test_fanout_risks_measures_multiplicity_against_the_identity_not_the_anchor():
    """Pinning a variable also pins whatever is to-one from it.

    `access` is pinned by `external_ip`, so the project that owns it is pinned too even
    though the walk to it starts two hops from the anchor.
    """
    query = _FANOUT_QUERY.replace(
        "MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)",
        "MATCH (project:GCPProject)-[:RESOURCE]->(access)",
    ).replace("MATCH (instance)-", "MATCH (instance:GCPInstance)-")
    assert _risks(query, ("instance_id", "external_ip")) == set()


def test_fanout_risks_flags_a_variable_that_only_duplicates_rows():
    """A to-many hop contributing no output column repeats identical rows."""
    query = """
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH (instance)-[:NETWORK_INTERFACE]->(nic:GCPNetworkInterface)
    RETURN instance.id AS instance_id, project.id AS project_id
    """
    assert _risks(query, ("instance_id",)) == {("nic", "invisible")}


def test_fanout_risks_accepts_return_distinct_for_identical_rows():
    """`RETURN DISTINCT` collapses duplicates, so an invisible fan-out is resolved."""
    query = """
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH (instance)-[:NETWORK_INTERFACE]->(nic:GCPNetworkInterface)
    RETURN DISTINCT instance.id AS instance_id, project.id AS project_id
    """
    assert _risks(query, ("instance_id",)) == set()


def test_fanout_risks_accepts_an_aggregate_in_the_final_projection():
    """An aggregate makes Cypher group by the other columns, folding away the rest.

    `nic` contributes no output column, so grouping collapses it exactly as DISTINCT
    would, without the query having to say DISTINCT.
    """
    query = """
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH (instance)-[:NETWORK_INTERFACE]->(nic:GCPNetworkInterface)
    RETURN instance.id AS instance_id, min(project.id) AS project_id
    """
    assert _risks(query, ("instance_id",)) == set()


def test_fanout_risks_does_not_let_return_distinct_excuse_a_projected_column():
    """DISTINCT dedupes whole rows, so rows differing only outside the identity survive."""
    query = _FANOUT_QUERY.replace("RETURN", "RETURN DISTINCT")
    assert _risks(query, ("instance_id",)) == {("access", "projected")}


def test_fanout_risks_accepts_an_aggregated_fan_out():
    """An aggregate folds the extra rows into one value."""
    query = """
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH (instance)-[:NETWORK_INTERFACE]->(:GCPNetworkInterface)-[:RESOURCE]->(access:GCPNicAccessConfig)
    WITH instance, project, collect(DISTINCT access.public_ip) AS external_ips
    RETURN instance.id AS instance_id, project.id AS project_id, external_ips
    """
    assert _risks(query, ("instance_id",)) == set()


def test_fanout_risks_ignores_a_variable_bound_only_in_a_subquery():
    """`EXISTS { ... }` and `CALL { ... }` filter rows, they do not multiply them."""
    query = """
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    WHERE EXISTS { (instance)-[:NETWORK_INTERFACE]->(nic:GCPNetworkInterface) }
    RETURN instance.id AS instance_id, project.id AS project_id
    """
    assert _risks(query, ("instance_id",)) == set()


def test_fanout_risks_accepts_an_optional_match_anti_join():
    """`OPTIONAL MATCH` plus `IS NULL` keeps only rows where nothing matched."""
    query = """
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    OPTIONAL MATCH (instance)-[:NETWORK_INTERFACE]->(nic:GCPNetworkInterface)
    WITH instance, project, nic
    WHERE nic IS NULL
    RETURN instance.id AS instance_id, project.id AS project_id
    """
    assert _risks(query, ("instance_id",)) == set()


def test_fanout_risks_survives_a_comment_marker_inside_a_string_literal():
    """A `//` inside a literal must not be read as the start of a comment."""
    query = """
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH (instance)-[:NETWORK_INTERFACE]->(nic:GCPNetworkInterface)
    WHERE nic.name <> 'https://example.com/'
    RETURN instance.id AS instance_id, project.id AS project_id
    """
    assert _risks(query, ("instance_id",)) == {("nic", "invisible")}


def test_fanout_risks_resolves_an_identity_field_through_an_intermediate_with():
    """A `WITH x AS y` rename must still trace the identity back to its variable."""
    query = """
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH (instance)-[:NETWORK_INTERFACE]->(:GCPNetworkInterface)-[:RESOURCE]->(access:GCPNicAccessConfig)
    WITH instance, access.public_ip AS ip
    RETURN instance.id AS instance_id, ip AS external_ip
    """
    assert _risks(query, ("instance_id", "external_ip")) == set()
