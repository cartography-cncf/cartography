from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.scaleway.instances import flexibleips
from cartography.intel.scaleway.instances import instances
from cartography.intel.scaleway.instances import securitygroups
from cartography.intel.scaleway.storage import snapshots
from cartography.intel.scaleway.storage import volumes
from cartography.intel.scaleway.utils import DEFAULT_ZONES

ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


@pytest.mark.parametrize(
    "module,list_method",
    [
        (instances, "list_servers_all"),
        (flexibleips, "list_ips_all"),
        (volumes, "list_volumes_all"),
        (snapshots, "list_snapshots_all"),
    ],
)
def test_get_lists_every_zone(module, list_method):
    """Instance API lists are zone-scoped: resources outside the first zone
    must not be dropped."""
    with patch.object(module, "InstanceV1API") as api_cls:
        fetcher = getattr(api_cls.return_value, list_method)
        fetcher.side_effect = lambda zone, **_: [f"item-{zone}"]

        result = module.get(MagicMock(), ORG_ID)

    assert result == [f"item-{zone}" for zone in DEFAULT_ZONES]
    assert [call.kwargs for call in fetcher.call_args_list] == [
        {"organization": ORG_ID, "zone": zone} for zone in DEFAULT_ZONES
    ]


def test_get_security_groups_fetches_rules_in_the_group_zone():
    groups_by_zone = {
        "fr-par-1": [SimpleNamespace(id="sg-par1", zone="fr-par-1")],
        "fr-par-2": [SimpleNamespace(id="sg-par2", zone="fr-par-2")],
    }

    def list_rules(security_group_id, zone, per_page, page):
        rule = f"rule-{security_group_id}-{zone}"
        return SimpleNamespace(rules=[rule], total_count=1)

    with patch.object(securitygroups, "InstanceV1API") as api_cls:
        api = api_cls.return_value
        api.list_security_groups_all.side_effect = lambda zone, **_: groups_by_zone.get(
            zone, []
        )
        api.list_security_group_rules.side_effect = list_rules

        groups, rules_by_group = securitygroups.get(MagicMock(), ORG_ID)

    assert [group.id for group in groups] == ["sg-par1", "sg-par2"]
    assert rules_by_group == {
        "sg-par1": ["rule-sg-par1-fr-par-1"],
        "sg-par2": ["rule-sg-par2-fr-par-2"],
    }
