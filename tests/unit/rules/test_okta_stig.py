import re
from pathlib import Path

from cartography.rules.data.frameworks.stig import STIG_OKTA_CONTROL_TITLES
from cartography.rules.data.rules import okta_stig
from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.okta_stig import okta_inactive_users_not_disabled
from cartography.rules.data.rules.okta_stig import (
    okta_verify_fips_compliance_not_required,
)
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

OKTA_STIG_RULES = tuple(
    value for value in vars(okta_stig).values() if isinstance(value, Rule)
)

# Every V-ID in the Okta IDaaS STIG V1R2.
OKTA_STIG_V1R2_VULN_IDS = {
    *(f"V-2731{n}" for n in range(86, 100)),
    *(f"V-2732{n:02d}" for n in range(0, 10)),
    "V-279689",
    *(f"V-27969{n}" for n in range(0, 4)),
}

# DoD-specific checks that are intentionally out of scope.
DOD_ONLY_VULN_IDS = {"V-273192", "V-273204", "V-273207"}

COVERAGE_ROW = re.compile(r"^\| (V-\d+) +\| (Covered|Not covered) +\|", re.MULTILINE)


def _stig_requirements(rule) -> set[str]:
    return {
        framework.requirement.upper()
        for framework in rule.frameworks
        if framework.short_name == "stig"
    }


def _coverage_table() -> dict[str, str]:
    return dict(COVERAGE_ROW.findall(okta_stig.__doc__ or ""))


def test_rules_registered_and_metadata():
    assert len(OKTA_STIG_RULES) == 26
    for rule in OKTA_STIG_RULES:
        assert RULES[rule.id] is rule
        assert rule.version == "1.0.0"
        assert rule.modules == {Module.OKTA}
        assert rule.has_framework("stig", "okta", "v1r2")
        assert len(_stig_requirements(rule)) == 1
        assert rule.has_framework("iso", "27001", "2022")
        assert rule.has_framework("soc2", "tsc", "2022")
        assert rule.references


def test_rule_names_are_security_names():
    for rule in OKTA_STIG_RULES:
        assert not rule.name.startswith("STIG")
        assert "V-" not in rule.name
        assert ":" not in rule.name


def test_facts_have_expected_structure():
    fact_ids = [fact.id for rule in OKTA_STIG_RULES for fact in rule.facts]
    assert len(fact_ids) == len(set(fact_ids))

    for rule in OKTA_STIG_RULES:
        assert len(rule.facts) == 1
        fact = rule.facts[0]
        assert fact.module == Module.OKTA
        assert fact.maturity == Maturity.EXPERIMENTAL
        assert "MATCH" in fact.cypher_query
        assert "RETURN" in fact.cypher_query
        assert fact.cypher_visual_query.strip().split()[0] in {"MATCH", "WITH"}
        assert "COUNT" in fact.cypher_count_query


def test_phase_one_output_models_are_distinct():
    assert (
        okta_inactive_users_not_disabled.output_model
        is not okta_verify_fips_compliance_not_required.output_model
    )


def test_coverage_table_lists_every_stig_check_once():
    rows = COVERAGE_ROW.findall(okta_stig.__doc__ or "")

    assert len(rows) == len(OKTA_STIG_V1R2_VULN_IDS)
    assert {vuln_id for vuln_id, _ in rows} == OKTA_STIG_V1R2_VULN_IDS


def test_coverage_table_matches_mapped_rules():
    """A V-ID marked Covered must have a rule, and every mapped V-ID must be Covered."""
    table = _coverage_table()
    covered = {vuln_id for vuln_id, status in table.items() if status == "Covered"}
    mapped = {
        requirement
        for rule in RULES.values()
        for requirement in _stig_requirements(rule)
    }

    assert covered == mapped
    assert set(STIG_OKTA_CONTROL_TITLES) == mapped
    assert {
        vuln_id for vuln_id, status in table.items() if status == "Not covered"
    } == DOD_ONLY_VULN_IDS


def test_each_stig_check_maps_to_one_rule():
    requirements = [
        requirement
        for rule in OKTA_STIG_RULES
        for requirement in _stig_requirements(rule)
    ]
    assert len(requirements) == len(set(requirements))


def test_coverage_table_is_in_the_module_source():
    # Guard against the table moving out of the module docstring, which the
    # tests above parse.
    source = Path(okta_stig.__file__).read_text()
    assert source.lstrip().startswith('"""')
    assert "STIG coverage (V1R2, 29 checks)" in source


def test_inactive_user_fact_uses_35_day_window_and_enabled_states():
    fact = okta_inactive_users_not_disabled.facts[0]

    for query in (fact.cypher_query, fact.cypher_visual_query):
        assert "duration('P35D')" in query
        assert "coalesce(u.last_login, u.created)" in query
    for query in (fact.cypher_query, fact.cypher_visual_query, fact.cypher_count_query):
        assert "'ACTIVE'" in query
        assert "'SUSPENDED'" not in query
        assert "'DEPROVISIONED'" not in query


def test_fips_fact_only_evaluates_active_okta_verify():
    fact = okta_verify_fips_compliance_not_required.facts[0]

    for query in (fact.cypher_query, fact.cypher_visual_query, fact.cypher_count_query):
        assert "a.key = 'okta_verify'" in query
        assert "a.status = 'ACTIVE'" in query
    assert '"REQUIRED"' in fact.cypher_query
    assert '"REQUIRED"' in fact.cypher_visual_query


def test_password_facts_skip_directory_sourced_policies():
    password_rules = [
        rule
        for rule in OKTA_STIG_RULES
        if rule.output_model is okta_stig.OktaPasswordPolicyOutput
    ]

    assert len(password_rules) == 10
    for rule in password_rules:
        fact = rule.facts[0]
        for query in (
            fact.cypher_query,
            fact.cypher_visual_query,
            fact.cypher_count_query,
        ):
            assert "coalesce(p.auth_provider, 'OKTA') = 'OKTA'" in query
