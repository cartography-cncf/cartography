from cartography.intel.entra.groups import transform_groups
from tests.data.entra.groups import MOCK_ENTRA_GROUPS
from tests.data.entra.groups import MOCK_GROUP_MEMBERS
from tests.data.entra.groups import MOCK_GROUP_OWNERS


def test_transform_groups():
    result = transform_groups(
        MOCK_ENTRA_GROUPS,
        {
            gid: [u.id for u in members if u.odata_type == "#microsoft.graph.user"]
            for gid, members in MOCK_GROUP_MEMBERS.items()
        },
        {
            gid: [g.id for g in members if g.odata_type == "#microsoft.graph.group"]
            for gid, members in MOCK_GROUP_MEMBERS.items()
        },
        {
            gid: [o.id for o in owners if o.odata_type == "#microsoft.graph.user"]
            for gid, owners in MOCK_GROUP_OWNERS.items()
        },
    )
    assert len(result) == 2
    group1 = next(
        g for g in result if g["id"] == "11111111-1111-1111-1111-111111111111"
    )
    assert group1["display_name"] == "Security Team"
    assert group1["member_ids"] == [
        "ae4ac864-4433-4ba6-96a6-20f8cffdadcb",
        "11dca63b-cb03-4e53-bb75-fa8060285550",
    ]
    assert group1["member_group_ids"] == ["22222222-2222-2222-2222-222222222222"]
    assert group1["owner_ids"] == ["ae4ac864-4433-4ba6-96a6-20f8cffdadcb"]

    group2 = next(
        g for g in result if g["id"] == "22222222-2222-2222-2222-222222222222"
    )
    assert group2["display_name"] == "Developers"
    assert group2["member_ids"] == []
    assert group2["member_group_ids"] == []
    assert group2["owner_ids"] == ["11dca63b-cb03-4e53-bb75-fa8060285550"]
