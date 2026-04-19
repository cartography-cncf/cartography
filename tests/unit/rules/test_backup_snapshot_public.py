from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.backup_snapshot_public import backup_snapshot_public
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module


def test_backup_snapshot_public_rule_registered():
    assert backup_snapshot_public.id in RULES
    assert RULES[backup_snapshot_public.id] is backup_snapshot_public


def test_backup_snapshot_public_rule_metadata():
    assert backup_snapshot_public.output_model is not None
    assert len(backup_snapshot_public.facts) == 2
    for fact in backup_snapshot_public.facts:
        assert fact.module == Module.AWS
        assert fact.maturity == Maturity.EXPERIMENTAL
        assert fact.cypher_query.strip()
        assert fact.cypher_visual_query.strip()
        assert "COUNT" in fact.cypher_count_query
