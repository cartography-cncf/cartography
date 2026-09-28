import re
from pathlib import Path

from cartography.models.schema_docs import MANUAL_SCHEMA_MODULES
from cartography.sync import Sync

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_schema_doc():
    """Test that the schema documentation links to all modules.
    This test checks that the schema documentation file links to all modules
    that are present in the codebase, ensuring that the documentation is up-to-date
    with the current implementation of the modules.
    """
    link_regex = re.compile(r"\]\(\.\./modules/([\w-]+)/schema\.md\)")

    content = (REPOSITORY_ROOT / "docs/root/usage/schema.md").read_text()

    linked_modules = link_regex.findall(content)
    # MANUAL_SCHEMA_MODULES also covers graph data written outside an intel module, which
    # the sync module list does not know about.
    existing_modules = set(MANUAL_SCHEMA_MODULES)
    for m in Sync.list_intel_modules():
        if m in (
            "analysis",
            "create-indexes",
        ):
            continue
        existing_modules.add(m)

    assert sorted(linked_modules) == sorted(existing_modules)
