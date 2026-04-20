from cartography.rules.data.rules.unmanaged_accounts import unmanaged_accounts


def test_unmanaged_account_rule_uses_normalized_activity_fields() -> None:
    fact = unmanaged_accounts.facts[0]

    assert "COALESCE(a._ont_active, true)" in fact.cypher_query
    assert "NOT COALESCE(a._ont_inactive, false)" in fact.cypher_query
    assert "COALESCE(a.active, true)" in fact.cypher_query


def test_unmanaged_account_count_query_excludes_normalized_inactive_accounts() -> None:
    fact = unmanaged_accounts.facts[0]

    assert "COALESCE(a._ont_active, true)" in fact.cypher_count_query
    assert "NOT COALESCE(a._ont_inactive, false)" in fact.cypher_count_query
