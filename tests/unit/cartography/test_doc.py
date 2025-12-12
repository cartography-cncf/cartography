import re

from cartography.sync import Sync


def test_schema_doc():
    """Test that the schema documentation includes all modules.
    This test checks that the schema documentation file includes all modules
    that are present in the codebase, ensuring that the documentation is up-to-date
    with the current implementation of the modules.
    """
    include_regex = re.compile(r"{include} ../modules/(\w+)/schema.md")

    with open("./docs/root/usage/schema.md") as f:
        content = f.read()

    included_modules = include_regex.findall(content)
    existing_modules = []
    for m in Sync.list_intel_modules():
        if m in (
            "analysis",
            "create-indexes",
        ):
            continue
        existing_modules.append(m)

    assert sorted(included_modules) == sorted(existing_modules)
