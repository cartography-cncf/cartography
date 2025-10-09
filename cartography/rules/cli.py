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

from cartography.rules.data.frameworks import FRAMEWORKS
from cartography.rules.runners import run_frameworks
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Requirement

app = typer.Typer(
    help="Execute Cartography security frameworks",
    no_args_is_help=True,
)


class OutputFormat(str, Enum):
    """Output format options."""

    text = "text"
    json = "json"


def complete_frameworks(incomplete: str) -> Generator[str, None, None]:
    """Autocomplete framework names."""
    for name in FRAMEWORKS.keys():
        if name.startswith(incomplete):
            yield name


def complete_frameworks_with_all(incomplete: str) -> Generator[str, None, None]:
    """Autocomplete framework names plus 'all'."""
    for name in builtins.list(FRAMEWORKS.keys()) + ["all"]:
        if name.startswith(incomplete):
            yield name


def complete_requirements(
    ctx: typer.Context, incomplete: str
) -> Generator[tuple[str, str], None, None]:
    """Autocomplete requirement IDs with descriptions based on selected framework."""
    framework = ctx.params.get("framework")
    if not framework or framework not in FRAMEWORKS:
        return

    for req in FRAMEWORKS[framework].requirements:
        if req.id.lower().startswith(incomplete.lower()):
            yield (req.id, req.name)


def complete_facts(
    ctx: typer.Context, incomplete: str
) -> Generator[tuple[str, str], None, None]:
    """Autocomplete fact IDs with descriptions based on selected framework and requirement."""
    framework = ctx.params.get("framework")
    requirement_id = ctx.params.get("requirement")

    if not framework or framework not in FRAMEWORKS:
        return
    if not requirement_id:
        return

    # Find the requirement
    for req in FRAMEWORKS[framework].requirements:
        if req.id.lower() == requirement_id.lower():
            for fact in req.facts:
                if fact.id.lower().startswith(incomplete.lower()):
                    yield (fact.id, fact.name)
            break


@app.command()  # type: ignore[misc]
def list(
    framework: Annotated[
        str | None,
        typer.Argument(
            help="Framework name (e.g., mitre-attack)",
            autocompletion=complete_frameworks,
        ),
    ] = None,
    requirement: Annotated[
        str | None,
        typer.Argument(
            help="Requirement ID (e.g., T1190)",
            autocompletion=complete_requirements,
        ),
    ] = None,
) -> None:
    """
    List available frameworks, requirements, and facts.

    \b
    Examples:
        cartography-rules list
        cartography-rules list mitre-attack
        cartography-rules list mitre-attack T1190
    """
    # List all frameworks
    if not framework:
        typer.secho("\nAvailable Frameworks\n", bold=True)
        for fw_name, fw in FRAMEWORKS.items():
            typer.secho(f"{fw_name}", fg=typer.colors.CYAN)
            typer.echo(f"  Name:         {fw.name}")
            typer.echo(f"  Version:      {fw.version}")
            typer.echo(f"  Requirements: {len(fw.requirements)}")
            total_facts = sum(len(req.facts) for req in fw.requirements)
            typer.echo(f"  Total Facts:  {total_facts}")
            if fw.source_url:
                typer.echo(f"  Source:       {fw.source_url}")
            typer.echo()
        return

    # Validate framework
    if framework not in FRAMEWORKS:
        typer.secho(
            f"Error: Unknown framework '{framework}'", fg=typer.colors.RED, err=True
        )
        typer.echo(f"Available: {', '.join(FRAMEWORKS.keys())}", err=True)
        raise typer.Exit(1)

    fw = FRAMEWORKS[framework]

    # List all requirements in framework
    if not requirement:
        typer.secho(f"\n{fw.name}", bold=True)
        typer.echo(f"Version: {fw.version}\n")
        for r in fw.requirements:
            typer.secho(f"{r.id}", fg=typer.colors.CYAN)
            typer.echo(f"  Name:  {r.name}")
            typer.echo(f"  Facts: {len(r.facts)}")
            if r.requirement_url:
                typer.echo(f"  URL:   {r.requirement_url}")
            typer.echo()
        return

    # Find and list facts in requirement
    req: Requirement | None = None
    for r in fw.requirements:
        if r.id.lower() == requirement.lower():
            req = r
            break

    if not req:
        typer.secho(
            f"Error: Requirement '{requirement}' not found",
            fg=typer.colors.RED,
            err=True,
        )
        typer.echo("\nAvailable requirements:", err=True)
        for r in fw.requirements:
            typer.echo(f"  {r.id}", err=True)
        raise typer.Exit(1)

    typer.secho(f"\n{req.name}\n", bold=True)
    typer.echo(f"ID:  {req.id}")
    if req.requirement_url:
        typer.echo(f"URL: {req.requirement_url}")
    typer.secho(f"\nFacts ({len(req.facts)})\n", bold=True)

    for fact in req.facts:
        typer.secho(f"{fact.id}", fg=typer.colors.CYAN)
        typer.echo(f"  Name:        {fact.name}")
        typer.echo(f"  Description: {fact.description}")
        typer.echo(f"  Provider:    {fact.module.value}")
        typer.echo()


@app.command()  # type: ignore[misc]
def run(
    framework: Annotated[
        str,
        typer.Argument(
            help="Framework to execute (or 'all' for all frameworks)",
            autocompletion=complete_frameworks_with_all,
        ),
    ],
    requirement: Annotated[
        str | None,
        typer.Argument(
            help="Specific requirement ID to run",
            autocompletion=complete_requirements,
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
) -> None:
    """
    Execute a security framework.

    \b
    Examples:
        cartography-rules run all
        cartography-rules run mitre-attack
        cartography-rules run mitre-attack T1190
        cartography-rules run mitre-attack T1190 aws_rds_public_access
    """
    # Validate framework
    valid_frameworks = builtins.list(FRAMEWORKS.keys()) + ["all"]
    if framework not in valid_frameworks:
        typer.secho(
            f"Error: Unknown framework '{framework}'", fg=typer.colors.RED, err=True
        )
        typer.echo(f"Available: {', '.join(valid_frameworks)}", err=True)
        raise typer.Exit(1)

    # Validate fact requires requirement
    if fact and not requirement:
        typer.secho(
            "Error: Cannot specify fact without requirement",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Validate filtering with 'all'
    if framework == "all" and (requirement or fact):
        typer.secho(
            "Error: Cannot filter by requirement/fact when running all frameworks",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Validate requirement exists
    if requirement and framework != "all":
        fw = FRAMEWORKS[framework]
        req: Requirement | None = None
        for r in fw.requirements:
            if r.id.lower() == requirement.lower():
                req = r
                break

        if not req:
            typer.secho(
                f"Error: Requirement '{requirement}' not found",
                fg=typer.colors.RED,
                err=True,
            )
            typer.echo("\nAvailable requirements:", err=True)
            for r in fw.requirements:
                typer.echo(f"  {r.id}", err=True)
            raise typer.Exit(1)

        # Validate fact exists
        if fact:
            fact_found: Fact | None = None
            for f in req.facts:
                if f.id.lower() == fact.lower():
                    fact_found = f
                    break

            if not fact_found:
                typer.secho(
                    f"Error: Fact '{fact}' not found in requirement '{requirement}'",
                    fg=typer.colors.RED,
                    err=True,
                )
                typer.echo("\nAvailable facts:", err=True)
                for f in req.facts:
                    typer.echo(f"  {f.id}", err=True)
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

    # Determine frameworks to run
    if framework == "all":
        frameworks_to_run = builtins.list(FRAMEWORKS.keys())
    else:
        frameworks_to_run = [framework]

    # Execute
    try:
        exit_code = run_frameworks(
            frameworks_to_run,
            uri,
            user,
            password,
            database,
            output.value,
            requirement_filter=requirement,
            fact_filter=fact,
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
