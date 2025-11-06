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
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Requirement

app = typer.Typer(
    help="Execute Cartography security frameworks",
    no_args_is_help=True,
)


class OutputFormat(str, Enum):
    """Output format options."""

    text = "text"
    json = "json"


# Autocompletion functions


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


def complete_findings(
    ctx: typer.Context, incomplete: str
) -> Generator[tuple[str, str], None, None]:
    # TESTS
    """Autocomplete finding names."""
    framework = ctx.params.get("framework")
    requirement_id = ctx.params.get("requirement")
    if not framework or framework not in FRAMEWORKS:
        return
    if not requirement_id:
        return

    for finding in FRAMEWORKS[framework].get_findings_by_requirement(requirement_id):
        if finding.id.lower().startswith(incomplete.lower()):
            yield (finding.id, finding.name)


def complete_facts(
    ctx: typer.Context, incomplete: str
) -> Generator[tuple[str, str], None, None]:
    """Autocomplete fact IDs with descriptions based on selected framework, requirement or finding."""
    framework = ctx.params.get("framework")
    requirement_id = ctx.params.get("requirement")
    finding_id = ctx.params.get("finding")

    if not framework or framework not in FRAMEWORKS:
        return
    if not requirement_id:
        return
    if not finding_id:
        return

    # Find the finding
    for fact in FRAMEWORKS[framework].get_facts_by_finding(requirement_id, finding_id):
        if fact.id.lower().startswith(incomplete.lower()):
            yield (fact.id, fact.name)


# CLI Commands


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
    finding: Annotated[
        str | None,
        typer.Argument(
            help="Finding name (e.g., mfa-missing)",
            autocompletion=complete_findings,
        ),
    ] = None,
) -> None:
    """
    List available frameworks, requirements, findings and facts.

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
            all_findings = [f for req in fw.requirements for f in req.findings]
            all_facts = [fa for f in all_findings for fa in f.facts]
            typer.echo(f"  Findings:     {len(all_findings)}")
            typer.echo(f"  Total Facts:  {len(all_facts)}")
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
            typer.echo(f"  Findings: {len(r.findings)}")
            typer.echo(f"  Facts: {sum(len(f.facts) for f in r.findings)}")
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

    typer.secho(f"\n{req.name}", bold=True)
    typer.echo(f"ID:  {req.id}")
    if req.requirement_url:
        typer.echo(f"URL: {req.requirement_url}")

    # Find and list findings in requirement
    if not finding:
        typer.secho(f"\nFindings ({len(req.findings)})", bold=True)

        for f in req.findings:
            typer.secho(f"{f.id}", fg=typer.colors.CYAN)
            typer.echo(f"  Name:        {f.name}")
            typer.echo(f"  Description: {f.description}")
            typer.echo(f"  Tags:        {', '.join(f.tags)}")
            typer.echo(f"  Modules:     {', '.join(f.modules)}")
            typer.echo(f"  Total Facts: {len(f.facts)}")
            typer.echo()
        return

    # Find and list facts in finding
    finding_obj: Finding | None = fw.get_finding_by_id(req.id, finding)

    if not finding_obj:
        typer.secho(
            f"Error: Finding '{finding}' not found in requirement '{requirement}'",
            fg=typer.colors.RED,
            err=True,
        )
        typer.echo("\nAvailable findings:", err=True)
        for f in req.findings:
            typer.echo(f"  {f.id}", err=True)
        raise typer.Exit(1)

    typer.secho(f"\n{finding_obj.name}", bold=True)
    typer.echo(f"ID:  {finding_obj.id}")
    all_facts = [fa for f in req.findings for fa in f.facts]
    typer.secho(f"\nFacts ({len(all_facts)})\n", bold=True)

    for fact in finding_obj.facts:
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
    finding: Annotated[
        str | None,
        typer.Argument(
            help="Specific finding ID to run",
            autocompletion=complete_findings,
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
    if fact and (not requirement or not finding):
        typer.secho(
            "Error: Cannot specify fact without requirement and finding",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Validate finding requires requirement
    if finding and not requirement:
        typer.secho(
            "Error: Cannot specify finding without requirement",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Validate filtering with 'all'
    if framework == "all" and (requirement or fact or finding):
        typer.secho(
            "Error: Cannot filter by requirement/fact when running all frameworks",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Validate requirement exists
    if requirement and framework != "all":
        fw = FRAMEWORKS[framework]
        req = fw.get_requirement_by_id(requirement)
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

        # Validate finding exists
        if finding:
            finding_obj: Finding | None = fw.get_finding_by_id(requirement, finding)

            if not finding_obj:
                typer.secho(
                    f"Error: Finding '{finding}' not found in requirement '{requirement}'",
                    fg=typer.colors.RED,
                    err=True,
                )
                typer.echo("\nAvailable findings:", err=True)
                for f in req.findings:
                    typer.echo(f"  {f.id}", err=True)
                raise typer.Exit(1)

            # Validate fact exists
            if fact:
                fact_found: Fact | None = fw.get_fact_by_id(requirement, finding, fact)

                if not fact_found:
                    typer.secho(
                        f"Error: Fact '{fact}' not found in requirement '{requirement}'",
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
            finding_filter=finding,
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
