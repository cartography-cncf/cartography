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

from cartography.rules.data.findings import FINDINGS
from cartography.rules.runners import run_findings

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


def complete_findings(incomplete: str) -> Generator[str, None, None]:
    """Autocomplete findings names."""
    for name in FINDINGS.keys():
        if name.startswith(incomplete):
            yield name


def complete_findings_with_all(incomplete: str) -> Generator[str, None, None]:
    """Autocomplete findings names plus 'all'."""
    for name in builtins.list(FINDINGS.keys()) + ["all"]:
        if name.startswith(incomplete):
            yield name


def complete_facts(
    ctx: typer.Context, incomplete: str
) -> Generator[tuple[str, str], None, None]:
    """Autocomplete facts IDs with descriptions based on selected finding."""
    finding = ctx.params.get("finding")
    if not finding or finding not in FINDINGS:
        return

    for fact in FINDINGS[finding].facts:
        if fact.id.lower().startswith(incomplete.lower()):
            yield (fact.id, fact.name)


# ----------------------------
# CLI Commands
# ----------------------------


@app.command(name="list")  # type: ignore[misc]
def list_cmd(
    finding: Annotated[
        str | None,
        typer.Argument(
            help="Finding name (e.g., mfa-missing)",
            autocompletion=complete_findings,
        ),
    ] = None,
) -> None:
    """
    List available findings and facts.

    \b
    Examples:
        cartography-rules list
        cartography-rules list mfa-missing
        cartography-rules list mfa-missing missing-mfa-cloudflare
    """
    # List all frameworks
    if not finding:
        typer.secho("\nAvailable Findings\n", bold=True)
        for finding_name, finding_obj in FINDINGS.items():
            typer.secho(f"{finding_name}", fg=typer.colors.CYAN)
            typer.echo(f"  Name:         {finding_obj.name}")
            typer.echo(f"  Version:      {finding_obj.version}")
            typer.echo(f"  Facts:        {len(finding_obj.facts)}")
            if finding_obj.references:
                typer.echo("  References:")
                for ref in finding_obj.references:
                    typer.echo(f"    - {ref}")
            typer.echo()
        return

    # Validate finding
    if finding not in FINDINGS:
        typer.secho(
            f"Error: Unknown finding '{finding}'", fg=typer.colors.RED, err=True
        )
        typer.echo(f"Available: {', '.join(FINDINGS.keys())}", err=True)
        raise typer.Exit(1)

    finding_obj = FINDINGS[finding]

    typer.secho(f"\n{finding_obj.name}", bold=True)
    typer.echo(f"ID:  {finding_obj.id}")
    typer.secho(f"\nFacts ({len(finding_obj.facts)})\n", bold=True)

    for fact in finding_obj.facts:
        typer.secho(f"{fact.id}", fg=typer.colors.CYAN)
        typer.echo(f"  Name:        {fact.name}")
        typer.echo(f"  Description: {fact.description}")
        typer.echo(f"  Maturity:    {fact.maturity.value}")
        typer.echo(f"  Provider:    {fact.module.value}")
        typer.echo()


@app.command(name="run")  # type: ignore[misc]
def run_cmd(
    finding: Annotated[
        str | None,
        typer.Argument(
            help="Specific finding ID to run",
            autocompletion=complete_findings_with_all,
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
    # Validate finding
    valid_findings = builtins.list(FINDINGS.keys()) + ["all"]
    if finding not in valid_findings:
        typer.secho(
            f"Error: Unknown finding '{finding}'", fg=typer.colors.RED, err=True
        )
        typer.echo(f"Available: {', '.join(valid_findings)}", err=True)
        raise typer.Exit(1)

    # Validate fact requires finding
    if fact and not finding:
        typer.secho(
            "Error: Cannot specify fact without finding",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Validate filtering with 'all'
    if finding == "all" and fact:
        typer.secho(
            "Error: Cannot filter by fact when running all findings",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Validate fact exists
    if fact and finding != "all":
        finding_obj = FINDINGS[finding]
        fact_obj = finding_obj.get_fact_by_id(fact)
        if not fact_obj:
            typer.secho(
                f"Error: Fact '{fact}' not found in finding '{finding}'",
                fg=typer.colors.RED,
                err=True,
            )
            typer.echo("\nAvailable facts:", err=True)
            for fa in finding_obj.facts:
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

    # Determine findings to run
    if finding == "all":
        findings_to_run = builtins.list(FINDINGS.keys())
    else:
        findings_to_run = [finding]

    # Execute
    try:
        exit_code = run_findings(
            findings_to_run,
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
