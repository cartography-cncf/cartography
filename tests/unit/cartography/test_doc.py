import re
from pathlib import Path

from cartography.models.introspection import inspect_data_model
from cartography.models.schema_docs import generated_schema_modules
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
    # Include generated shared models that are written by provider modules but are not
    # independently selectable intel modules.
    existing_modules = set(MANUAL_SCHEMA_MODULES)
    existing_modules.update(generated_schema_modules(inspect_data_model()))
    for m in Sync.list_intel_modules():
        if m in (
            "analysis",
            "create-indexes",
        ):
            continue
        existing_modules.add(m)

    assert sorted(linked_modules) == sorted(existing_modules)
