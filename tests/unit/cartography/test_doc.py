import re
from pathlib import Path

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


def test_cli_doc():
    """Test that every user-visible CLI flag is documented.

    This test checks that each non-hidden CLI flag defined in cartography/cli.py
    appears somewhere in the docs, ensuring that the documentation is up-to-date
    with the current CLI surface. Flags declared with `hidden=True` and
    experimental flags are excluded.
    """
    flag_regex = re.compile(r'"(--[a-z0-9-]+)"')

    with open("./cartography/cli.py") as f:
        cli_source = f.read()

    # Map each flag to its typer.Option block (up to the next flag literal) so
    # we can detect statically hidden flags.
    matches = list(flag_regex.finditer(cli_source))
    undocumented = []
    docs_content = ""
    for path in Path("./docs/root").rglob("*.md"):
        docs_content += path.read_text()

    for i, match in enumerate(matches):
        flag = match.group(1)
        if flag.startswith("--experimental-"):
            continue
        block_end = matches[i + 1].start() if i + 1 < len(matches) else len(cli_source)
        block = cli_source[match.start() : block_end]
        if "hidden=True" in block:
            continue
        if flag not in docs_content:
            undocumented.append(flag)

    assert not undocumented, (
        f"The following CLI flags are not documented anywhere under docs/root; "
        f"please add them to the relevant module config page or docs/root/usage/cli.md: "
        f"{sorted(set(undocumented))}"
    )
