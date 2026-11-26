import re
from pathlib import Path

import typer

from cartography.cli import ALWAYS_SHOW_PANELS
from cartography.cli import CLI
from cartography.cli import MODULE_PANELS
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


def test_cli_doc():
    """Test that every user-visible CLI flag is documented.

    Introspect the actual Typer/Click command instead of parsing cli.py
    source, so the check reflects the real CLI surface (including generated
    options) and honours each option's real ``hidden`` state. Hidden flags,
    experimental flags, and Typer's built-in completion/help options are
    excluded.
    """
    # Build with every panel visible so module-specific flags are not hidden
    # (each flag is hidden when its panel is not in visible_panels); otherwise
    # the test would silently skip all module flags and only check core ones.
    all_panels = set(MODULE_PANELS.values()) | ALWAYS_SHOW_PANELS
    command = typer.main.get_command(CLI()._build_app(all_panels))

    # Typer/Click built-ins, not part of cartography's own CLI surface.
    builtin_flags = {"--help", "--install-completion", "--show-completion"}

    docs_content = ""
    for path in (REPOSITORY_ROOT / "docs/root").rglob("*.md"):
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
