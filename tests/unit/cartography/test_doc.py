import re
from pathlib import Path

import typer

from cartography.cli import CLI
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

    Introspect the actual Typer/Click command instead of parsing cli.py
    source, so the check reflects the real CLI surface (including generated
    options) and honours each option's real ``hidden`` state. Hidden flags,
    experimental flags, and Typer's built-in completion/help options are
    excluded.
    """
    command = typer.main.get_command(CLI()._build_app(set()))

    # Typer/Click built-ins, not part of cartography's own CLI surface.
    builtin_flags = {"--help", "--install-completion", "--show-completion"}

    docs_content = ""
    for path in Path("./docs/root").rglob("*.md"):
        docs_content += path.read_text()

    undocumented = []
    for param in command.params:
        if getattr(param, "hidden", False):
            continue
        for opt in param.opts:
            if not opt.startswith("--"):
                continue
            if opt in builtin_flags or opt.startswith("--experimental-"):
                continue
            if opt not in docs_content:
                undocumented.append(opt)

    assert not undocumented, (
        "The following CLI flags are not documented anywhere under docs/root; "
        "please add them to the relevant module config page or "
        "docs/root/usage/cli.md: "
        f"{sorted(set(undocumented))}"
    )
