import re
from pathlib import Path

import pytest

from cartography.intel.bloodhound import EDGE_KINDS

DOCS = Path(__file__).parents[5] / "docs/root/modules/bloodhound/index.md"


def upper_snake(bloodhound_name: str) -> str:
    """BloodHound edge name in UPPER_SNAKE, keeping acronyms whole: GPLink -> GP_LINK."""
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z][a-z]+", bloodhound_name)
    assert "".join(words) == bloodhound_name, bloodhound_name
    return "_".join(word.upper() for word in words)


@pytest.mark.parametrize(
    ("bloodhound_name", "expected"),
    [
        ("MemberOf", "MEMBER_OF"),
        ("GPLink", "GP_LINK"),
        ("DCSync", "DC_SYNC"),
        ("CanPSRemote", "CAN_PS_REMOTE"),
        ("ReadGMSAPassword", "READ_GMSA_PASSWORD"),
        ("HasSIDHistory", "HAS_SID_HISTORY"),
        ("WriteSPN", "WRITE_SPN"),
    ],
)
def test_upper_snake(bloodhound_name, expected):
    assert upper_snake(bloodhound_name) == expected


def test_relationship_types_are_bloodhound_names_in_upper_snake():
    for kind, edge_kind in EDGE_KINDS.items():
        assert edge_kind.schema.rel_label == kind
        assert kind == upper_snake(edge_kind.bloodhound_name)


def test_docs_mapping_table_lists_every_imported_edge():
    rows = re.findall(
        r"^\| `(\w+)` \| `\(:\w+\)-\[:(\w+)\]->\(:\w+\)` \|$",
        DOCS.read_text(),
        flags=re.MULTILINE,
    )
    assert set(rows) == {
        (edge_kind.bloodhound_name, kind) for kind, edge_kind in EDGE_KINDS.items()
    }
