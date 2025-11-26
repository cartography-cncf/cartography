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
    """Autocomplete rules names."""
    for name in RULES.keys():
        if name.startswith(incomplete):
            yield name


def complete_rules_with_all(incomplete: str) -> Generator[str, None, None]:
    """Autocomplete rules names plus 'all'."""
    for name in builtins.list(RULES.keys()) + ["all"]:
        if name.startswith(incomplete):
            yield name


def complete_facts(
    ctx: typer.Context, incomplete: str
) -> Generator[tuple[str, str], None, None]:
    """Autocomplete facts IDs with descriptions based on selected rule."""
    rule = ctx.params.get("rule")
    if not rule or rule not in RULES:
        return

    for fact in RULES[rule].facts:
        if fact.id.lower().startswith(incomplete.lower()):
            yield (fact.id, fact.name)


# ----------------------------
# CLI Commands
# ----------------------------


@app.command(name="list")  # type: ignore[misc]
def list_cmd(
    rule: Annotated[
        str | None,
        typer.Argument(
            help="Rule name (e.g., mfa-missing)",
            autocompletion=complete_rules,
        ),
    ] = None,
) -> None:
    """
    List available rules and facts.

    \b
    Examples:
        cartography-rules list
        cartography-rules list mfa-missing
        cartography-rules list mfa-missing missing-mfa-cloudflare
    """
    # List all frameworks
    if not rule:
        typer.secho("\nAvailable Rules\n", bold=True)
        for rule_name, rule_obj in RULES.items():
            typer.secho(f"{rule_name}", fg=typer.colors.CYAN)
            typer.echo(f"  Name:         {rule_obj.name}")
            typer.echo(f"  Version:      {rule_obj.version}")
            typer.echo(f"  Facts:        {len(rule_obj.facts)}")
            if rule_obj.references:
                typer.echo("  References:")
                for ref in rule_obj.references:
                    typer.echo(f"    - [{ref.text}]({ref.url})")
            typer.echo()
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
) -> None:
    """
    Execute a security framework.

    \b
    Examples:
        cartography-rules run all
        cartography-rules run mfa-missing
        cartography-rules run mfa-missing missing-mfa-cloudflare
    """
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
        )
        raise typer.Exit(exit_code)
    except KeyboardInterrupt:
        raise typer.Exit(130)


def main():
    """Entrypoint for cartography-rules CLI."""
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("neo4j").setLevel(logging.ERROR)
    app()


if __name__ == "__main__":
    main()
