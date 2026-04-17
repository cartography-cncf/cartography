"""
Cartography RunRules CLI

Execute security frameworks and present facts about your environment.
"""

import builtins
import logging
import os
from enum import Enum
from typing import Generator

import typer
from typing_extensions import Annotated

from cartography.rules.data.rules import RULES
from cartography.rules.runners import get_all_frameworks
from cartography.rules.runners import run_rules

app = typer.Typer(
    help="Execute Cartography security frameworks",
    no_args_is_help=True,
)


class OutputFormat(str, Enum):
    """Output format options."""

    text = "text"
    json = "json"


# ----------------------------
# Autocompletion functions
# ----------------------------


def complete_rules(incomplete: str) -> Generator[str, None, None]:
    """
    Autocomplete rule names for CLI tab completion.

    Args:
        incomplete (str): The partial rule name typed by the user.

    Yields:
        str: Rule names that start with the incomplete string.
    """
    for name in RULES.keys():
        if name.startswith(incomplete):
            yield name


def complete_rules_with_all(incomplete: str) -> Generator[str, None, None]:
    """
    Autocomplete rule names plus 'all' for CLI tab completion.

    Args:
        incomplete (str): The partial rule name typed by the user.

    Yields:
        str: Rule names (plus 'all') that start with the incomplete string.
    """
    for name in builtins.list(RULES.keys()) + ["all"]:
        if name.startswith(incomplete):
            yield name


def complete_facts(
    ctx: typer.Context, incomplete: str
) -> Generator[tuple[str, str], None, None]:
    """
    Autocomplete fact IDs with descriptions based on the selected rule.

    Args:
        ctx (typer.Context): The Typer context containing parsed parameters.
        incomplete (str): The partial fact ID typed by the user.

    Yields:
        tuple[str, str]: A tuple of (fact_id, fact_name) for matching facts.
    """
    rule = ctx.params.get("rule")
    if not rule or rule not in RULES:
        return

    for fact in RULES[rule].facts:
        if fact.id.lower().startswith(incomplete.lower()):
            yield (fact.id, fact.name)


def complete_frameworks(incomplete: str) -> Generator[str, None, None]:
    """
    Autocomplete framework filters for CLI tab completion.

    Supports formats: "CIS", "CIS:aws", "CIS:aws:5.0"

    Args:
        incomplete (str): The partial framework filter typed by the user.

    Yields:
        str: Framework filter strings that start with the incomplete string.
    """
    frameworks = get_all_frameworks()
    incomplete_lower = incomplete.lower()

    # Generate completion options
    for short_name, fws in frameworks.items():
        # Short name only (e.g., "cis")
        if short_name.startswith(incomplete_lower):
            yield short_name

        # Short name + scope (e.g., "cis:aws") - only for frameworks with scope
        scopes = sorted({fw.scope for fw in fws if fw.scope is not None})
        for scope in scopes:
            option = f"{short_name}:{scope}"
            if option.startswith(incomplete_lower):
                yield option

            # Short name + scope + revision (e.g., "cis:aws:5.0")
            revisions = sorted(
                {
                    fw.revision
                    for fw in fws
                    if fw.scope == scope and fw.revision is not None
                }
            )
            for revision in revisions:
                full_option = f"{short_name}:{scope}:{revision}"
                if full_option.startswith(incomplete_lower):
                    yield full_option


# ----------------------------
# CLI Commands
# ----------------------------


@app.command(name="frameworks")  # type: ignore[misc]
def frameworks_cmd() -> None:
    """
    List all compliance frameworks referenced by rules.

    \b
    Examples:
        cartography-rules frameworks
    """
    frameworks = get_all_frameworks()

    if not frameworks:
        typer.echo("No frameworks found in rules.")
        return

    typer.secho("\nCompliance Frameworks\n", bold=True)

    for short_name, fws in frameworks.items():
        # Get unique scopes and their revisions
        scopes: dict[str | None, set[str | None]] = {}
        for fw in fws:
            if fw.scope not in scopes:
                scopes[fw.scope] = set()
            scopes[fw.scope].add(fw.revision)

        typer.secho(f"{short_name.upper()}", fg=typer.colors.CYAN)
        if fws:
            typer.echo(f"  Name: {fws[0].name}")
        for scope, revisions in sorted(scopes.items(), key=lambda x: x[0] or ""):
            rev_list = [r for r in revisions if r is not None]
            if scope is not None:
                if rev_list:
                    rev_str = ", ".join(sorted(rev_list))
                    typer.echo(f"  Scope: {scope} (revisions: {rev_str})")
                else:
                    typer.echo(f"  Scope: {scope}")
            elif rev_list:
                rev_str = ", ".join(sorted(rev_list))
                typer.echo(f"  Revisions: {rev_str}")

        # Count rules using this framework
        rule_count = sum(1 for rule in RULES.values() if rule.has_framework(short_name))
        typer.echo(f"  Rules: {rule_count}")
        typer.echo()


@app.command(name="list")  # type: ignore[misc]
def list_cmd(
    rule: Annotated[
        str | None,
        typer.Argument(
            help="Rule name (e.g., mfa-missing)",
            autocompletion=complete_rules,
        ),
    ] = None,
    framework: Annotated[
        str | None,
        typer.Option(
            "--framework",
            "-f",
            help="Filter by framework (e.g., CIS, CIS:aws, CIS:aws:5.0)",
            autocompletion=complete_frameworks,
        ),
    ] = None,
) -> None:
    """
    List available rules and facts.

    \b
    Examples:
        cartography-rules list
        cartography-rules list --framework CIS
        cartography-rules list --framework CIS:aws
        cartography-rules list mfa-missing
    """
    # List all rules (optionally filtered by framework)
    if not rule:
        # Parse framework filter
        fw_short_name = None
        fw_scope = None
        fw_revision = None
        if framework:
            parts = framework.split(":")
            fw_short_name = parts[0] if len(parts) >= 1 else None
            fw_scope = parts[1] if len(parts) >= 2 else None
            fw_revision = parts[2] if len(parts) >= 3 else None

        if framework:
            typer.secho(f"\nRules matching framework: {framework}\n", bold=True)
        else:
            typer.secho("\nAvailable Rules\n", bold=True)

        found_rules = False
        for rule_name, rule_obj in RULES.items():
            # Apply framework filter
            if framework and not rule_obj.has_framework(
                fw_short_name, fw_scope, fw_revision
            ):
                continue

            found_rules = True
            typer.secho(f"{rule_name}", fg=typer.colors.CYAN)
            typer.echo(f"  Name:         {rule_obj.name}")
            typer.echo(f"  Version:      {rule_obj.version}")
            typer.echo(f"  Facts:        {len(rule_obj.facts)}")
            if rule_obj.frameworks:
                typer.echo("  Frameworks:")
                for fw in rule_obj.frameworks:
                    # Build framework string with optional parts
                    fw_parts = [fw.short_name]
                    if fw.scope:
                        fw_parts.append(fw.scope)
                    if fw.revision:
                        fw_parts.append(fw.revision)
                    fw_str = ":".join(fw_parts)
                    typer.echo(f"    - {fw_str} ({fw.requirement})")
            if rule_obj.references:
                typer.echo("  References:")
                for ref in rule_obj.references:
                    typer.echo(f"    - [{ref.text}]({ref.url})")
            typer.echo()

        if not found_rules:
            typer.echo("No rules found matching the filter.", err=True)
        return

    # Validate rule
    if rule not in RULES:
        typer.secho(f"Error: Unknown rule '{rule}'", fg=typer.colors.RED, err=True)
        typer.echo(f"Available: {', '.join(RULES.keys())}", err=True)
        raise typer.Exit(1)

    rule_obj = RULES[rule]

    typer.secho(f"\n{rule_obj.name}", bold=True)
    typer.echo(f"ID:  {rule_obj.id}")
    typer.secho(f"\nFacts ({len(rule_obj.facts)})\n", bold=True)

    for fact in rule_obj.facts:
        typer.secho(f"{fact.id}", fg=typer.colors.CYAN)
        typer.echo(f"  Name:        {fact.name}")
        typer.echo(f"  Description: {fact.description}")
        typer.echo(f"  Maturity:    {fact.maturity.value}")
        typer.echo(f"  Provider:    {fact.module.value}")
        typer.echo()


@app.command(name="run")  # type: ignore[misc]
def run_cmd(
    rule: Annotated[
        str | None,
        typer.Argument(
            help="Specific rule ID to run",
            autocompletion=complete_rules_with_all,
        ),
    ] = None,
    fact: Annotated[
        str | None,
        typer.Argument(
            help="Specific fact ID to run",
            autocompletion=complete_facts,
        ),
    ] = None,
    uri: Annotated[
        str,
        typer.Option(help="Neo4j URI", envvar="NEO4J_URI"),
    ] = "bolt://localhost:7687",
    user: Annotated[
        str,
        typer.Option(help="Neo4j username", envvar="NEO4J_USER"),
    ] = "neo4j",
    database: Annotated[
        str,
        typer.Option(help="Neo4j database name", envvar="NEO4J_DATABASE"),
    ] = "neo4j",
    neo4j_password_env_var: Annotated[
        str | None,
        typer.Option(help="Environment variable containing Neo4j password"),
    ] = None,
    neo4j_password_prompt: Annotated[
        bool,
        typer.Option(help="Prompt for Neo4j password interactively"),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option(help="Output format"),
    ] = OutputFormat.text,
    experimental: bool = typer.Option(
        True,
        "--experimental/--no-experimental",
        help="Enable or disable experimental facts.",
    ),
    framework: Annotated[
        str | None,
        typer.Option(
            "--framework",
            "-f",
            help="Filter by framework (e.g., CIS, CIS:aws, CIS:aws:5.0)",
            autocompletion=complete_frameworks,
        ),
    ] = None,
) -> None:
    """
    Execute a security framework.

    \b
    Examples:
        cartography-rules run all
        cartography-rules run all --framework CIS
        cartography-rules run all --framework CIS:aws:5.0
        cartography-rules run mfa-missing
        cartography-rules run mfa-missing missing-mfa-cloudflare
    """
    # If no rule specified but framework filter provided, run all rules
    if rule is None and framework:
        rule = "all"

    # Validate rule
    valid_rules = builtins.list(RULES.keys()) + ["all"]
    if rule not in valid_rules:
        typer.secho(f"Error: Unknown rule '{rule}'", fg=typer.colors.RED, err=True)
        typer.echo(f"Available: {', '.join(valid_rules)}", err=True)
        raise typer.Exit(1)

    # Validate fact requires rule
    if fact and not rule:
        typer.secho(
            "Error: Cannot specify fact without rule",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Validate filtering with 'all'
    if rule == "all" and fact:
        typer.secho(
            "Error: Cannot filter by fact when running all rules",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Validate fact exists
    if fact and rule != "all":
        rule_obj = RULES[rule]
        fact_obj = rule_obj.get_fact_by_id(fact)
        if not fact_obj:
            typer.secho(
                f"Error: Fact '{fact}' not found in rule '{rule}'",
                fg=typer.colors.RED,
                err=True,
            )
            typer.echo("\nAvailable facts:", err=True)
            for fa in rule_obj.facts:
                typer.echo(f"  {fa.id}", err=True)
            raise typer.Exit(1)

    # Get password
    password = None
    if neo4j_password_prompt:
        password = typer.prompt("Neo4j password", hide_input=True)
    elif neo4j_password_env_var:
        password = os.environ.get(neo4j_password_env_var)
    else:
        password = os.getenv("NEO4J_PASSWORD")
        if not password:
            password = typer.prompt("Neo4j password", hide_input=True)

    # Determine rules to run
    if rule == "all":
        rules_to_run = builtins.list(RULES.keys())
    else:
        rules_to_run = [rule]

    # Execute
    try:
        exit_code = run_rules(
            rules_to_run,
            uri,
            user,
            password,
            database,
            output.value,
            fact_filter=fact,
            exclude_experimental=not experimental,
            framework_filter=framework,
        )
        raise typer.Exit(exit_code)
    except KeyboardInterrupt:
        raise typer.Exit(130)


def main():
    """
    Entrypoint for the cartography-rules CLI.

    This function initializes logging and launches the Typer application.
    It is the main entry point when running ``cartography-rules`` from the command line.
    """
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("neo4j").setLevel(logging.ERROR)
    app()


if __name__ == "__main__":
    main()
