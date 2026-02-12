import getpass
import logging
import os
import sys
from typing import TYPE_CHECKING

import typer
from typing_extensions import Annotated

from cartography.config import Config
from cartography.version import get_release_version_and_commit_revision

if TYPE_CHECKING:
    from cartography.sync import Sync

logger = logging.getLogger(__name__)

# Keep these local to avoid importing cartography.util (and its heavy deps) on --help/--version paths.
STATUS_SUCCESS = 0
STATUS_FAILURE = 1
STATUS_KEYBOARD_INTERRUPT = 130

# Help Panel Names - Used to organize options in --help output
PANEL_CORE = "Core Options"
PANEL_NEO4J = "Neo4j Connection"
PANEL_AWS = "AWS Options"
PANEL_AZURE = "Azure Options"
PANEL_ENTRA = "Entra ID Options"
PANEL_GCP = "GCP Options"
PANEL_OCI = "OCI Options"
PANEL_OKTA = "Okta Options"
PANEL_GITHUB = "GitHub Options"
PANEL_GITLAB = "GitLab Options"
PANEL_GSUITE = "GSuite Options"
PANEL_GOOGLE_WORKSPACE = "Google Workspace Options"
PANEL_DIGITALOCEAN = "DigitalOcean Options"
PANEL_CROWDSTRIKE = "CrowdStrike Options"
PANEL_JAMF = "Jamf Options"
PANEL_KANDJI = "Kandji Options"
PANEL_KUBERNETES = "Kubernetes Options"
PANEL_CVE = "CVE Options"
PANEL_PAGERDUTY = "PagerDuty Options"
PANEL_LASTPASS = "LastPass Options"
PANEL_BIGFIX = "BigFix Options"
PANEL_DUO = "Duo Options"
PANEL_WORKDAY = "Workday Options"
PANEL_SEMGREP = "Semgrep Options"
PANEL_SNIPEIT = "SnipeIT Options"
PANEL_CLOUDFLARE = "Cloudflare Options"
PANEL_TAILSCALE = "Tailscale Options"
PANEL_OPENAI = "OpenAI Options"
PANEL_ANTHROPIC = "Anthropic Options"
PANEL_AIRBYTE = "Airbyte Options"
PANEL_TRIVY = "Trivy Options"
PANEL_ONTOLOGY = "Ontology Options"
PANEL_SCALEWAY = "Scaleway Options"
PANEL_SENTINELONE = "SentinelOne Options"
PANEL_KEYCLOAK = "Keycloak Options"
PANEL_SLACK = "Slack Options"
PANEL_SPACELIFT = "Spacelift Options"
PANEL_STATSD = "StatsD Metrics"
PANEL_ANALYSIS = "Analysis Options"

# Mapping of module names to their help panels
MODULE_PANELS = {
    "aws": PANEL_AWS,
    "azure": PANEL_AZURE,
    "entra": PANEL_ENTRA,
    "gcp": PANEL_GCP,
    "oci": PANEL_OCI,
    "okta": PANEL_OKTA,
    "github": PANEL_GITHUB,
    "gitlab": PANEL_GITLAB,
    "gsuite": PANEL_GSUITE,
    "googleworkspace": PANEL_GOOGLE_WORKSPACE,
    "digitalocean": PANEL_DIGITALOCEAN,
    "crowdstrike": PANEL_CROWDSTRIKE,
    "jamf": PANEL_JAMF,
    "kandji": PANEL_KANDJI,
    "kubernetes": PANEL_KUBERNETES,
    "cve": PANEL_CVE,
    "pagerduty": PANEL_PAGERDUTY,
    "lastpass": PANEL_LASTPASS,
    "bigfix": PANEL_BIGFIX,
    "duo": PANEL_DUO,
    "workday": PANEL_WORKDAY,
    "semgrep": PANEL_SEMGREP,
    "snipeit": PANEL_SNIPEIT,
    "cloudflare": PANEL_CLOUDFLARE,
    "tailscale": PANEL_TAILSCALE,
    "openai": PANEL_OPENAI,
    "anthropic": PANEL_ANTHROPIC,
    "airbyte": PANEL_AIRBYTE,
    "trivy": PANEL_TRIVY,
    "ontology": PANEL_ONTOLOGY,
    "scaleway": PANEL_SCALEWAY,
    "sentinelone": PANEL_SENTINELONE,
    "keycloak": PANEL_KEYCLOAK,
    "slack": PANEL_SLACK,
    "spacelift": PANEL_SPACELIFT,
    "analysis": PANEL_ANALYSIS,
}

# Panels that should always be shown (not module-specific)
ALWAYS_SHOW_PANELS = {PANEL_CORE, PANEL_NEO4J, PANEL_STATSD, PANEL_ANALYSIS}


def _version_callback(value: bool) -> None:
    """
    Handle eager --version processing before command execution.
    """
    if not value:
        return

    release_version, commit_revision = get_release_version_and_commit_revision()
    typer.echo(
        f"cartography release {release_version}, commit revision {commit_revision}"
    )
    raise typer.Exit(code=0)


def _parse_selected_modules_from_argv(argv: list[str]) -> set[str]:
    """
    Pre-parse argv to extract --selected-modules value for dynamic help visibility.

    Returns:
        Set of visible panel names. If no modules specified, returns all panels.
    """
    # We pre-parse argv to extract --selected-modules BEFORE building the Typer app.
    # This allows us to show only relevant options in --help output.
    # Example: `cartography --selected-modules aws --help` shows only AWS options.

    # Why pre-parse? Typer generates help BEFORE parsing arguments, so we need to
    # know selected modules earlier. Hidden options still work (backward compat),
    # they just don't clutter --help.
    selected_modules: str | None = None

    for i, arg in enumerate(argv):
        if arg == "--selected-modules" and i + 1 < len(argv):
            selected_modules = argv[i + 1]
            break
        elif arg.startswith("--selected-modules="):
            selected_modules = arg.split("=", 1)[1]
            break

    if not selected_modules:
        # No filter: show all panels
        return set(MODULE_PANELS.values()) | ALWAYS_SHOW_PANELS

    # Build set of visible panels from selected modules
    visible_panels = set(ALWAYS_SHOW_PANELS)
    for module in selected_modules.split(","):
        module = module.strip().lower()
        if module in MODULE_PANELS:
            visible_panels.add(MODULE_PANELS[module])

    return visible_panels


class CLI:
    """
    Command Line Interface for cartography using Typer.

    This class provides the main command line interface for cartography, handling
    argument parsing, configuration, and execution of sync operations.

    Note:
        We maintain this class-based structure (rather than using module-level Typer
        functions like cartography-rules does) for backward compatibility. The existing
        codebase and tests rely on being able to:

        1. Inject a custom Sync object: `CLI(sync=my_custom_sync)`
        2. Set a custom program name: `CLI(prog="my-cartography")`
        3. Call main() with explicit argv: `cli.main(["--neo4j-uri", "..."])`

        This allows users to create custom sync configurations and test the CLI
        with mock objects. See tests/integration/cartography/test_cli.py for examples.

    Attributes:
        sync: A cartography.sync.Sync object for executing sync operations.
        prog: The name of the command line program for display in help output.

    Example:
        >>> sync = cartography.sync.build_default_sync()
        >>> cli = CLI(sync=sync, prog="cartography")
        >>> exit_code = cli.main(["--neo4j-uri", "bolt://localhost:7687"])
    """

    def __init__(
        self,
        sync: "Sync | None" = None,
        prog: str | None = None,
    ):
        # Defer default sync construction until command execution to keep --help fast.
        self.sync = sync
        self.prog = prog

    def main(self, argv: list[str]) -> int:
        """
        Main entrypoint for the command line interface.

        This method parses command line arguments, configures logging and various
        service connections, validates input parameters, and executes the cartography
        sync operation with the provided configuration.

        Args:
            argv: The command line arguments to parse. Should be a list of strings
                  representing the command line parameters (excluding the program name).

        Returns:
            An integer exit code. Returns 0 for successful execution, or a non-zero
            value for errors or keyboard interruption.
        """
        # Pre-parse argv to determine which help panels to show
        visible_panels = _parse_selected_modules_from_argv(argv)

        # Build the Typer app with our sync object in closure
        app = self._build_app(visible_panels)

        # Typer doesn't return exit codes directly, so we catch SystemExit
        try:
            app(argv, standalone_mode=False)
            return STATUS_SUCCESS
        except typer.Exit as e:
            if e.exit_code is None:
                return STATUS_SUCCESS
            return e.exit_code
        except SystemExit as e:
            if e.code is None:
                return STATUS_SUCCESS
            elif isinstance(e.code, int):
                return e.code
            else:
                # e.code can be a string message in some cases
                return STATUS_FAILURE
        except KeyboardInterrupt:
            return STATUS_KEYBOARD_INTERRUPT
        except Exception as e:
            logger.error("Cartography failed: %s", e)
            return STATUS_FAILURE

    def _build_app(self, visible_panels: set[str]) -> typer.Typer:
        """
        Build the Typer application with all CLI options.

        Args:
            visible_panels: Set of panel names to show in help. Options in other
                panels are hidden but still functional (backward compatibility).

        Returns:
            A configured Typer application.
        """
        app = typer.Typer(
            name=self.prog,
            help=(
                "Cartography consolidates infrastructure assets and the relationships "
                "between them in an intuitive graph view. This application can be used "
                "to pull configuration data from multiple sources, load it into Neo4j, "
                "and run arbitrary enrichment and analysis on that data."
            ),
            epilog="For more documentation please visit: https://github.com/cartography-cncf/cartography",
            no_args_is_help=False,
            add_completion=True,
            context_settings={"help_option_names": ["-h", "--help"]},
        )

        # Store reference to self for use in the command function
        cli_instance = self

        @app.command()  # type: ignore[misc]
        def run(
            # =================================================================
            # Core Options
            # =================================================================
            # DEPRECATED: `--verbose` will be removed in v1.0.0. Use `--debug` instead.
            verbose: Annotated[
                bool,
                typer.Option(
                    "--verbose",
                    "-v",
                    "--debug",
                    "-d",
                    help=(
                        "Enable verbose logging for cartography. "
                        "DEPRECATED: --verbose will be removed in v1.0.0; use --debug instead."
                    ),
                    rich_help_panel=PANEL_CORE,
                ),
            ] = False,
            show_version: Annotated[
                bool,
                typer.Option(
                    "--version",
                    callback=_version_callback,
                    is_eager=True,
                    help="Show cartography release version and commit revision, then exit.",
                    rich_help_panel=PANEL_CORE,
                ),
            ] = False,
            quiet: Annotated[
                bool,
                typer.Option(
                    "--quiet",
                    "-q",
                    help="Restrict cartography logging to warnings and errors only.",
                    rich_help_panel=PANEL_CORE,
                ),
            ] = False,
            selected_modules: Annotated[
                str | None,
                typer.Option(
                    "--selected-modules",
                    help=(
                        "Comma-separated list of cartography top-level modules to sync. "
                        'Example: "aws,gcp" to run AWS and GCP modules. '
                        "If not specified, cartography will run all available modules. "
                        'We recommend including "create-indexes" first and "analysis" last.'
                    ),
                    rich_help_panel=PANEL_CORE,
                ),
            ] = None,
            update_tag: Annotated[
                int | None,
                typer.Option(
                    "--update-tag",
                    help=(
                        "A unique tag to apply to all Neo4j nodes and relationships created "
                        "or updated during the sync run. Used by cleanup jobs to identify stale data. "
                        "By default, cartography will use a UNIX timestamp."
                    ),
                    rich_help_panel=PANEL_CORE,
                ),
            ] = None,
            # =================================================================
            # Neo4j Connection Options
            # =================================================================
            neo4j_uri: Annotated[
                str,
                typer.Option(
                    "--neo4j-uri",
                    help=(
                        "A valid Neo4j URI to sync against. See "
                        "https://neo4j.com/docs/browser-manual/current/operations/dbms-connection/#uri-scheme"
                    ),
                    rich_help_panel=PANEL_NEO4J,
                ),
            ] = "bolt://localhost:7687",
            neo4j_user: Annotated[
                str | None,
                typer.Option(
                    "--neo4j-user",
                    help="A username with which to authenticate to Neo4j.",
                    rich_help_panel=PANEL_NEO4J,
                ),
            ] = None,
            neo4j_password_env_var: Annotated[
                str | None,
                typer.Option(
                    "--neo4j-password-env-var",
                    help="The name of an environment variable containing the Neo4j password.",
                    rich_help_panel=PANEL_NEO4J,
                ),
            ] = None,
            neo4j_password_prompt: Annotated[
                bool,
                typer.Option(
                    "--neo4j-password-prompt",
                    help="Present an interactive prompt for the Neo4j password. Supersedes other password methods.",
                    rich_help_panel=PANEL_NEO4J,
                ),
            ] = False,
            neo4j_max_connection_lifetime: Annotated[
                int,
                typer.Option(
                    "--neo4j-max-connection-lifetime",
                    help="Time in seconds for the Neo4j driver to consider a TCP connection alive. Default: 3600.",
                    rich_help_panel=PANEL_NEO4J,
                ),
            ] = 3600,
            neo4j_database: Annotated[
                str | None,
                typer.Option(
                    "--neo4j-database",
                    help="The name of the database in Neo4j to connect to. Uses Neo4j default if not specified.",
                    rich_help_panel=PANEL_NEO4J,
                ),
            ] = None,
            # =================================================================
            # AWS Options
            # =================================================================
            aws_sync_all_profiles: Annotated[
                bool,
                typer.Option(
                    "--aws-sync-all-profiles",
                    help=(
                        "Enable AWS sync for all discovered named profiles. "
                        "Cartography will discover all configured AWS named profiles and run the AWS sync "
                        'for each profile not named "default".'
                    ),
                    rich_help_panel=PANEL_AWS,
                    hidden=PANEL_AWS not in visible_panels,
                ),
            ] = False,
            aws_regions: Annotated[
                str | None,
                typer.Option(
                    "--aws-regions",
                    help=(
                        "[EXPERIMENTAL] Comma-separated list of AWS regions to sync. "
                        'Example: "us-east-1,us-east-2". '
                        "CAUTION: Previously synced regions not in this list will have their assets deleted."
                    ),
                    rich_help_panel=PANEL_AWS,
                    hidden=PANEL_AWS not in visible_panels,
                ),
            ] = None,
            aws_best_effort_mode: Annotated[
                bool,
                typer.Option(
                    "--aws-best-effort-mode",
                    help="Continue syncing other accounts if one fails, raising exceptions at the end.",
                    rich_help_panel=PANEL_AWS,
                    hidden=PANEL_AWS not in visible_panels,
                ),
            ] = False,
            aws_cloudtrail_management_events_lookback_hours: Annotated[
                int | None,
                typer.Option(
                    "--aws-cloudtrail-management-events-lookback-hours",
                    help="Number of hours back to retrieve CloudTrail management events. Not retrieved if not specified.",
                    rich_help_panel=PANEL_AWS,
                    hidden=PANEL_AWS not in visible_panels,
                ),
            ] = None,
            aws_requested_syncs: Annotated[
                str | None,
                typer.Option(
                    "--aws-requested-syncs",
                    help=(
                        "Comma-separated list of AWS resources to sync. "
                        'Example: "ecr,s3,ec2:instance". See cartography.intel.aws.resources for full list.'
                    ),
                    rich_help_panel=PANEL_AWS,
                    hidden=PANEL_AWS not in visible_panels,
                ),
            ] = None,
            aws_guardduty_severity_threshold: Annotated[
                str | None,
                typer.Option(
                    "--aws-guardduty-severity-threshold",
                    help="GuardDuty severity threshold. Valid values: LOW, MEDIUM, HIGH, CRITICAL.",
                    rich_help_panel=PANEL_AWS,
                    hidden=PANEL_AWS not in visible_panels,
                ),
            ] = None,
            experimental_aws_inspector_batch: Annotated[
                int,
                typer.Option(
                    "--experimental-aws-inspector-batch",
                    help="[EXPERIMENTAL] Batch size for AWS Inspector findings sync. Default: 1000.",
                    rich_help_panel=PANEL_AWS,
                    hidden=PANEL_AWS not in visible_panels,
                ),
            ] = 1000,
            permission_relationships_file: Annotated[
                str,
                typer.Option(
                    "--permission-relationships-file",
                    help="Path to the AWS permission relationships mapping file.",
                    rich_help_panel=PANEL_AWS,
                    hidden=PANEL_AWS not in visible_panels,
                ),
            ] = "cartography/data/permission_relationships.yaml",
            # =================================================================
            # Azure Options
            # =================================================================
            azure_sync_all_subscriptions: Annotated[
                bool,
                typer.Option(
                    "--azure-sync-all-subscriptions",
                    help="Enable Azure sync for all discovered subscriptions.",
                    rich_help_panel=PANEL_AZURE,
                    hidden=PANEL_AZURE not in visible_panels,
                ),
            ] = False,
            azure_sp_auth: Annotated[
                bool,
                typer.Option(
                    "--azure-sp-auth",
                    help="Use Service Principal authentication for Azure sync.",
                    rich_help_panel=PANEL_AZURE,
                    hidden=PANEL_AZURE not in visible_panels,
                ),
            ] = False,
            azure_tenant_id: Annotated[
                str | None,
                typer.Option(
                    "--azure-tenant-id",
                    help="Azure Tenant ID for Service Principal Authentication.",
                    rich_help_panel=PANEL_AZURE,
                    hidden=PANEL_AZURE not in visible_panels,
                ),
            ] = None,
            azure_client_id: Annotated[
                str | None,
                typer.Option(
                    "--azure-client-id",
                    help="Azure Client ID for Service Principal Authentication.",
                    rich_help_panel=PANEL_AZURE,
                    hidden=PANEL_AZURE not in visible_panels,
                ),
            ] = None,
            azure_client_secret_env_var: Annotated[
                str | None,
                typer.Option(
                    "--azure-client-secret-env-var",
                    help="Environment variable name containing Azure Client Secret.",
                    rich_help_panel=PANEL_AZURE,
                    hidden=PANEL_AZURE not in visible_panels,
                ),
            ] = None,
            azure_subscription_id: Annotated[
                str | None,
                typer.Option(
                    "--azure-subscription-id",
                    help="The Azure Subscription ID to sync.",
                    rich_help_panel=PANEL_AZURE,
                    hidden=PANEL_AZURE not in visible_panels,
                ),
            ] = None,
            azure_permission_relationships_file: Annotated[
                str,
                typer.Option(
                    "--azure-permission-relationships-file",
                    help="Path to the Azure permission relationships mapping file.",
                    rich_help_panel=PANEL_AZURE,
                    hidden=PANEL_AZURE not in visible_panels,
                ),
            ] = "cartography/data/azure_permission_relationships.yaml",
            # =================================================================
            # Entra ID Options
            # =================================================================
            entra_tenant_id: Annotated[
                str | None,
                typer.Option(
                    "--entra-tenant-id",
                    help="Entra Tenant ID for Service Principal Authentication.",
                    rich_help_panel=PANEL_ENTRA,
                    hidden=PANEL_ENTRA not in visible_panels,
                ),
            ] = None,
            entra_client_id: Annotated[
                str | None,
                typer.Option(
                    "--entra-client-id",
                    help="Entra Client ID for Service Principal Authentication.",
                    rich_help_panel=PANEL_ENTRA,
                    hidden=PANEL_ENTRA not in visible_panels,
                ),
            ] = None,
            entra_client_secret_env_var: Annotated[
                str | None,
                typer.Option(
                    "--entra-client-secret-env-var",
                    help="Environment variable name containing Entra Client Secret.",
                    rich_help_panel=PANEL_ENTRA,
                    hidden=PANEL_ENTRA not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # GCP Options
            # =================================================================
            gcp_permission_relationships_file: Annotated[
                str,
                typer.Option(
                    "--gcp-permission-relationships-file",
                    help="Path to the GCP permission relationships mapping file.",
                    rich_help_panel=PANEL_GCP,
                    hidden=PANEL_GCP not in visible_panels,
                ),
            ] = "cartography/data/gcp_permission_relationships.yaml",
            # =================================================================
            # OCI Options
            # =================================================================
            oci_sync_all_profiles: Annotated[
                bool,
                typer.Option(
                    "--oci-sync-all-profiles",
                    help='Enable OCI sync for all discovered named profiles (excluding "DEFAULT").',
                    rich_help_panel=PANEL_OCI,
                    hidden=PANEL_OCI not in visible_panels,
                ),
            ] = False,
            # =================================================================
            # Okta Options
            # =================================================================
            okta_org_id: Annotated[
                str | None,
                typer.Option(
                    "--okta-org-id",
                    help="Okta organizational ID to sync. Required for Okta module.",
                    rich_help_panel=PANEL_OKTA,
                    hidden=PANEL_OKTA not in visible_panels,
                ),
            ] = None,
            okta_api_key_env_var: Annotated[
                str | None,
                typer.Option(
                    "--okta-api-key-env-var",
                    help="Environment variable name containing Okta API key.",
                    rich_help_panel=PANEL_OKTA,
                    hidden=PANEL_OKTA not in visible_panels,
                ),
            ] = None,
            okta_saml_role_regex: Annotated[
                str,
                typer.Option(
                    "--okta-saml-role-regex",
                    help="Regex to map Okta groups to AWS roles. Must contain {{role}} and {{accountid}} tags.",
                    rich_help_panel=PANEL_OKTA,
                    hidden=PANEL_OKTA not in visible_panels,
                ),
            ] = r"^aws\#\S+\#(?{{role}}[\w\-]+)\#(?{{accountid}}\d+)$",
            # =================================================================
            # GitHub Options
            # =================================================================
            github_config_env_var: Annotated[
                str | None,
                typer.Option(
                    "--github-config-env-var",
                    help="Environment variable name containing Base64 encoded GitHub config.",
                    rich_help_panel=PANEL_GITHUB,
                    hidden=PANEL_GITHUB not in visible_panels,
                ),
            ] = None,
            github_commit_lookback_days: Annotated[
                int,
                typer.Option(
                    "--github-commit-lookback-days",
                    help="Number of days to look back for GitHub commit tracking. Default: 30.",
                    rich_help_panel=PANEL_GITHUB,
                    hidden=PANEL_GITHUB not in visible_panels,
                ),
            ] = 30,
            # =================================================================
            # GitLab Options
            # =================================================================
            gitlab_url: Annotated[
                str,
                typer.Option(
                    "--gitlab-url",
                    help="GitLab instance URL. Defaults to https://gitlab.com.",
                    rich_help_panel=PANEL_GITLAB,
                    hidden=PANEL_GITLAB not in visible_panels,
                ),
            ] = "https://gitlab.com",
            gitlab_token_env_var: Annotated[
                str | None,
                typer.Option(
                    "--gitlab-token-env-var",
                    help="Environment variable name containing GitLab personal access token.",
                    rich_help_panel=PANEL_GITLAB,
                    hidden=PANEL_GITLAB not in visible_panels,
                ),
            ] = None,
            gitlab_organization_id: Annotated[
                int | None,
                typer.Option(
                    "--gitlab-organization-id",
                    help="GitLab organization (top-level group) ID to sync.",
                    rich_help_panel=PANEL_GITLAB,
                    hidden=PANEL_GITLAB not in visible_panels,
                ),
            ] = None,
            gitlab_commits_since_days: Annotated[
                int,
                typer.Option(
                    "--gitlab-commits-since-days",
                    help="Number of days of commit history to fetch. Default: 90.",
                    rich_help_panel=PANEL_GITLAB,
                    hidden=PANEL_GITLAB not in visible_panels,
                ),
            ] = 90,
            # =================================================================
            # DigitalOcean Options
            # =================================================================
            digitalocean_token_env_var: Annotated[
                str | None,
                typer.Option(
                    "--digitalocean-token-env-var",
                    help="Environment variable name containing DigitalOcean access token.",
                    rich_help_panel=PANEL_DIGITALOCEAN,
                    hidden=PANEL_DIGITALOCEAN not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # CrowdStrike Options
            # =================================================================
            crowdstrike_client_id_env_var: Annotated[
                str | None,
                typer.Option(
                    "--crowdstrike-client-id-env-var",
                    help="Environment variable name containing CrowdStrike client ID.",
                    rich_help_panel=PANEL_CROWDSTRIKE,
                    hidden=PANEL_CROWDSTRIKE not in visible_panels,
                ),
            ] = None,
            crowdstrike_client_secret_env_var: Annotated[
                str | None,
                typer.Option(
                    "--crowdstrike-client-secret-env-var",
                    help="Environment variable name containing CrowdStrike client secret.",
                    rich_help_panel=PANEL_CROWDSTRIKE,
                    hidden=PANEL_CROWDSTRIKE not in visible_panels,
                ),
            ] = None,
            crowdstrike_api_url: Annotated[
                str | None,
                typer.Option(
                    "--crowdstrike-api-url",
                    help="CrowdStrike API URL for self-hosted instances.",
                    rich_help_panel=PANEL_CROWDSTRIKE,
                    hidden=PANEL_CROWDSTRIKE not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # Jamf Options
            # =================================================================
            jamf_base_uri: Annotated[
                str | None,
                typer.Option(
                    "--jamf-base-uri",
                    help="Jamf base URI, e.g. https://hostname.com/JSSResource.",
                    rich_help_panel=PANEL_JAMF,
                    hidden=PANEL_JAMF not in visible_panels,
                ),
            ] = None,
            jamf_user: Annotated[
                str | None,
                typer.Option(
                    "--jamf-user",
                    help="Username to authenticate to Jamf.",
                    rich_help_panel=PANEL_JAMF,
                    hidden=PANEL_JAMF not in visible_panels,
                ),
            ] = None,
            jamf_password_env_var: Annotated[
                str | None,
                typer.Option(
                    "--jamf-password-env-var",
                    help="Environment variable name containing Jamf password.",
                    rich_help_panel=PANEL_JAMF,
                    hidden=PANEL_JAMF not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # Kandji Options
            # =================================================================
            kandji_base_uri: Annotated[
                str | None,
                typer.Option(
                    "--kandji-base-uri",
                    help="Kandji base URI, e.g. https://company.api.kandji.io.",
                    rich_help_panel=PANEL_KANDJI,
                    hidden=PANEL_KANDJI not in visible_panels,
                ),
            ] = None,
            kandji_tenant_id: Annotated[
                str | None,
                typer.Option(
                    "--kandji-tenant-id",
                    help="Kandji tenant ID.",
                    rich_help_panel=PANEL_KANDJI,
                    hidden=PANEL_KANDJI not in visible_panels,
                ),
            ] = None,
            kandji_token_env_var: Annotated[
                str | None,
                typer.Option(
                    "--kandji-token-env-var",
                    help="Environment variable name containing Kandji API token.",
                    rich_help_panel=PANEL_KANDJI,
                    hidden=PANEL_KANDJI not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # Kubernetes Options
            # =================================================================
            k8s_kubeconfig: Annotated[
                str | None,
                typer.Option(
                    "--k8s-kubeconfig",
                    help="Path to kubeconfig file for K8s cluster(s).",
                    rich_help_panel=PANEL_KUBERNETES,
                    hidden=PANEL_KUBERNETES not in visible_panels,
                ),
            ] = None,
            managed_kubernetes: Annotated[
                str | None,
                typer.Option(
                    "--managed-kubernetes",
                    help="Type of managed Kubernetes service (e.g., 'eks').",
                    rich_help_panel=PANEL_KUBERNETES,
                    hidden=PANEL_KUBERNETES not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # CVE Options
            # =================================================================
            nist_cve_url: Annotated[
                str,
                typer.Option(
                    "--nist-cve-url",
                    help="Base URL for NIST CVE data.",
                    rich_help_panel=PANEL_CVE,
                    hidden=PANEL_CVE not in visible_panels,
                ),
            ] = "https://services.nvd.nist.gov/rest/json/cves/2.0/",
            cve_enabled: Annotated[
                bool,
                typer.Option(
                    "--cve-enabled",
                    help="Enable CVE data sync from NIST.",
                    rich_help_panel=PANEL_CVE,
                    hidden=PANEL_CVE not in visible_panels,
                ),
            ] = False,
            cve_api_key_env_var: Annotated[
                str | None,
                typer.Option(
                    "--cve-api-key-env-var",
                    help="Environment variable name containing NIST NVD API v2.0 key.",
                    rich_help_panel=PANEL_CVE,
                    hidden=PANEL_CVE not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # PagerDuty Options
            # =================================================================
            pagerduty_api_key_env_var: Annotated[
                str | None,
                typer.Option(
                    "--pagerduty-api-key-env-var",
                    help="Environment variable name containing PagerDuty API key.",
                    rich_help_panel=PANEL_PAGERDUTY,
                    hidden=PANEL_PAGERDUTY not in visible_panels,
                ),
            ] = None,
            pagerduty_request_timeout: Annotated[
                int | None,
                typer.Option(
                    "--pagerduty-request-timeout",
                    help="Timeout in seconds for PagerDuty API requests.",
                    rich_help_panel=PANEL_PAGERDUTY,
                    hidden=PANEL_PAGERDUTY not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # GSuite Options
            # =================================================================
            gsuite_auth_method: Annotated[
                str,
                typer.Option(
                    "--gsuite-auth-method",
                    help='GSuite authentication method: "delegated", "oauth", or "default".',
                    rich_help_panel=PANEL_GSUITE,
                    hidden=PANEL_GSUITE not in visible_panels,
                ),
            ] = "delegated",
            gsuite_tokens_env_var: Annotated[
                str,
                typer.Option(
                    "--gsuite-tokens-env-var",
                    help="Environment variable name containing GSuite credentials.",
                    rich_help_panel=PANEL_GSUITE,
                    hidden=PANEL_GSUITE not in visible_panels,
                ),
            ] = "GSUITE_GOOGLE_APPLICATION_CREDENTIALS",
            # =================================================================
            # Google Workspace Options
            # =================================================================
            googleworkspace_auth_method: Annotated[
                str,
                typer.Option(
                    "--googleworkspace-auth-method",
                    help='Google Workspace authentication method: "delegated", "oauth", or "default".',
                    rich_help_panel=PANEL_GOOGLE_WORKSPACE,
                    hidden=PANEL_GOOGLE_WORKSPACE not in visible_panels,
                ),
            ] = "delegated",
            googleworkspace_tokens_env_var: Annotated[
                str,
                typer.Option(
                    "--googleworkspace-tokens-env-var",
                    help="Environment variable name containing Google Workspace credentials.",
                    rich_help_panel=PANEL_GOOGLE_WORKSPACE,
                    hidden=PANEL_GOOGLE_WORKSPACE not in visible_panels,
                ),
            ] = "GOOGLEWORKSPACE_GOOGLE_APPLICATION_CREDENTIALS",
            # =================================================================
            # LastPass Options
            # =================================================================
            lastpass_cid_env_var: Annotated[
                str | None,
                typer.Option(
                    "--lastpass-cid-env-var",
                    help="Environment variable name containing LastPass CID.",
                    rich_help_panel=PANEL_LASTPASS,
                    hidden=PANEL_LASTPASS not in visible_panels,
                ),
            ] = None,
            lastpass_provhash_env_var: Annotated[
                str | None,
                typer.Option(
                    "--lastpass-provhash-env-var",
                    help="Environment variable name containing LastPass provhash.",
                    rich_help_panel=PANEL_LASTPASS,
                    hidden=PANEL_LASTPASS not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # BigFix Options
            # =================================================================
            bigfix_username: Annotated[
                str | None,
                typer.Option(
                    "--bigfix-username",
                    help="BigFix username for authentication.",
                    rich_help_panel=PANEL_BIGFIX,
                    hidden=PANEL_BIGFIX not in visible_panels,
                ),
            ] = None,
            bigfix_password_env_var: Annotated[
                str | None,
                typer.Option(
                    "--bigfix-password-env-var",
                    help="Environment variable name containing BigFix password.",
                    rich_help_panel=PANEL_BIGFIX,
                    hidden=PANEL_BIGFIX not in visible_panels,
                ),
            ] = None,
            bigfix_root_url: Annotated[
                str | None,
                typer.Option(
                    "--bigfix-root-url",
                    help="BigFix API URL.",
                    rich_help_panel=PANEL_BIGFIX,
                    hidden=PANEL_BIGFIX not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # Duo Options
            # =================================================================
            duo_api_key_env_var: Annotated[
                str | None,
                typer.Option(
                    "--duo-api-key-env-var",
                    help="Environment variable name containing Duo API key.",
                    rich_help_panel=PANEL_DUO,
                    hidden=PANEL_DUO not in visible_panels,
                ),
            ] = None,
            duo_api_secret_env_var: Annotated[
                str | None,
                typer.Option(
                    "--duo-api-secret-env-var",
                    help="Environment variable name containing Duo API secret.",
                    rich_help_panel=PANEL_DUO,
                    hidden=PANEL_DUO not in visible_panels,
                ),
            ] = None,
            duo_api_hostname: Annotated[
                str | None,
                typer.Option(
                    "--duo-api-hostname",
                    help="Duo API hostname.",
                    rich_help_panel=PANEL_DUO,
                    hidden=PANEL_DUO not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # Workday Options
            # =================================================================
            workday_api_url: Annotated[
                str | None,
                typer.Option(
                    "--workday-api-url",
                    help="Workday API URL.",
                    rich_help_panel=PANEL_WORKDAY,
                    hidden=PANEL_WORKDAY not in visible_panels,
                ),
            ] = None,
            workday_api_login: Annotated[
                str | None,
                typer.Option(
                    "--workday-api-login",
                    help="Workday API login username.",
                    rich_help_panel=PANEL_WORKDAY,
                    hidden=PANEL_WORKDAY not in visible_panels,
                ),
            ] = None,
            workday_api_password_env_var: Annotated[
                str | None,
                typer.Option(
                    "--workday-api-password-env-var",
                    help="Environment variable name containing Workday API password.",
                    rich_help_panel=PANEL_WORKDAY,
                    hidden=PANEL_WORKDAY not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # Semgrep Options
            # =================================================================
            semgrep_app_token_env_var: Annotated[
                str | None,
                typer.Option(
                    "--semgrep-app-token-env-var",
                    help="Environment variable name containing Semgrep app token.",
                    rich_help_panel=PANEL_SEMGREP,
                    hidden=PANEL_SEMGREP not in visible_panels,
                ),
            ] = None,
            semgrep_dependency_ecosystems: Annotated[
                str | None,
                typer.Option(
                    "--semgrep-dependency-ecosystems",
                    help='Comma-separated list of ecosystems for Semgrep dependencies. Example: "gomod,npm".',
                    rich_help_panel=PANEL_SEMGREP,
                    hidden=PANEL_SEMGREP not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # SnipeIT Options
            # =================================================================
            snipeit_base_uri: Annotated[
                str | None,
                typer.Option(
                    "--snipeit-base-uri",
                    help="SnipeIT base URI.",
                    rich_help_panel=PANEL_SNIPEIT,
                    hidden=PANEL_SNIPEIT not in visible_panels,
                ),
            ] = None,
            snipeit_token_env_var: Annotated[
                str | None,
                typer.Option(
                    "--snipeit-token-env-var",
                    help="Environment variable name containing SnipeIT API token.",
                    rich_help_panel=PANEL_SNIPEIT,
                    hidden=PANEL_SNIPEIT not in visible_panels,
                ),
            ] = None,
            snipeit_tenant_id: Annotated[
                str | None,
                typer.Option(
                    "--snipeit-tenant-id",
                    help="SnipeIT tenant ID.",
                    rich_help_panel=PANEL_SNIPEIT,
                    hidden=PANEL_SNIPEIT not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # Cloudflare Options
            # =================================================================
            cloudflare_token_env_var: Annotated[
                str | None,
                typer.Option(
                    "--cloudflare-token-env-var",
                    help="Environment variable name containing Cloudflare API key.",
                    rich_help_panel=PANEL_CLOUDFLARE,
                    hidden=PANEL_CLOUDFLARE not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # Tailscale Options
            # =================================================================
            tailscale_token_env_var: Annotated[
                str | None,
                typer.Option(
                    "--tailscale-token-env-var",
                    help="Environment variable name containing Tailscale API token.",
                    rich_help_panel=PANEL_TAILSCALE,
                    hidden=PANEL_TAILSCALE not in visible_panels,
                ),
            ] = None,
            tailscale_org: Annotated[
                str | None,
                typer.Option(
                    "--tailscale-org",
                    help="Tailscale organization name to sync.",
                    rich_help_panel=PANEL_TAILSCALE,
                    hidden=PANEL_TAILSCALE not in visible_panels,
                ),
            ] = None,
            tailscale_base_url: Annotated[
                str,
                typer.Option(
                    "--tailscale-base-url",
                    help="Tailscale API base URL.",
                    rich_help_panel=PANEL_TAILSCALE,
                    hidden=PANEL_TAILSCALE not in visible_panels,
                ),
            ] = "https://api.tailscale.com/api/v2",
            # =================================================================
            # OpenAI Options
            # =================================================================
            openai_apikey_env_var: Annotated[
                str | None,
                typer.Option(
                    "--openai-apikey-env-var",
                    help="Environment variable name containing OpenAI API key.",
                    rich_help_panel=PANEL_OPENAI,
                    hidden=PANEL_OPENAI not in visible_panels,
                ),
            ] = None,
            openai_org_id: Annotated[
                str | None,
                typer.Option(
                    "--openai-org-id",
                    help="OpenAI organization ID to sync.",
                    rich_help_panel=PANEL_OPENAI,
                    hidden=PANEL_OPENAI not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # Anthropic Options
            # =================================================================
            anthropic_apikey_env_var: Annotated[
                str | None,
                typer.Option(
                    "--anthropic-apikey-env-var",
                    help="Environment variable name containing Anthropic API key.",
                    rich_help_panel=PANEL_ANTHROPIC,
                    hidden=PANEL_ANTHROPIC not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # Airbyte Options
            # =================================================================
            airbyte_client_id: Annotated[
                str | None,
                typer.Option(
                    "--airbyte-client-id",
                    help="Airbyte client ID for authentication.",
                    rich_help_panel=PANEL_AIRBYTE,
                    hidden=PANEL_AIRBYTE not in visible_panels,
                ),
            ] = None,
            airbyte_client_secret_env_var: Annotated[
                str | None,
                typer.Option(
                    "--airbyte-client-secret-env-var",
                    help="Environment variable name containing Airbyte client secret.",
                    rich_help_panel=PANEL_AIRBYTE,
                    hidden=PANEL_AIRBYTE not in visible_panels,
                ),
            ] = None,
            airbyte_api_url: Annotated[
                str,
                typer.Option(
                    "--airbyte-api-url",
                    help="Airbyte API base URL.",
                    rich_help_panel=PANEL_AIRBYTE,
                    hidden=PANEL_AIRBYTE not in visible_panels,
                ),
            ] = "https://api.airbyte.com/v1",
            # =================================================================
            # Trivy Options
            # =================================================================
            trivy_s3_bucket: Annotated[
                str | None,
                typer.Option(
                    "--trivy-s3-bucket",
                    help="S3 bucket name containing Trivy scan results.",
                    rich_help_panel=PANEL_TRIVY,
                    hidden=PANEL_TRIVY not in visible_panels,
                ),
            ] = None,
            trivy_s3_prefix: Annotated[
                str | None,
                typer.Option(
                    "--trivy-s3-prefix",
                    help="S3 prefix path for Trivy scan results.",
                    rich_help_panel=PANEL_TRIVY,
                    hidden=PANEL_TRIVY not in visible_panels,
                ),
            ] = None,
            trivy_results_dir: Annotated[
                str | None,
                typer.Option(
                    "--trivy-results-dir",
                    help="Local directory containing Trivy JSON results.",
                    rich_help_panel=PANEL_TRIVY,
                    hidden=PANEL_TRIVY not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # Ontology Options
            # =================================================================
            ontology_users_source: Annotated[
                str | None,
                typer.Option(
                    "--ontology-users-source",
                    help="Comma-separated list of sources of truth for user data in the ontology.",
                    rich_help_panel=PANEL_ONTOLOGY,
                    hidden=PANEL_ONTOLOGY not in visible_panels,
                ),
            ] = None,
            ontology_devices_source: Annotated[
                str | None,
                typer.Option(
                    "--ontology-devices-source",
                    help="Comma-separated list of sources of truth for device data in the ontology.",
                    rich_help_panel=PANEL_ONTOLOGY,
                    hidden=PANEL_ONTOLOGY not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # Scaleway Options
            # =================================================================
            scaleway_org: Annotated[
                str | None,
                typer.Option(
                    "--scaleway-org",
                    help="Scaleway organization ID to sync.",
                    rich_help_panel=PANEL_SCALEWAY,
                    hidden=PANEL_SCALEWAY not in visible_panels,
                ),
            ] = None,
            scaleway_access_key: Annotated[
                str | None,
                typer.Option(
                    "--scaleway-access-key",
                    help="Scaleway access key for authentication.",
                    rich_help_panel=PANEL_SCALEWAY,
                    hidden=PANEL_SCALEWAY not in visible_panels,
                ),
            ] = None,
            scaleway_secret_key_env_var: Annotated[
                str | None,
                typer.Option(
                    "--scaleway-secret-key-env-var",
                    help="Environment variable name containing Scaleway secret key.",
                    rich_help_panel=PANEL_SCALEWAY,
                    hidden=PANEL_SCALEWAY not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # SentinelOne Options
            # =================================================================
            sentinelone_account_ids: Annotated[
                str | None,
                typer.Option(
                    "--sentinelone-account-ids",
                    help="Comma-separated list of SentinelOne account IDs to sync.",
                    rich_help_panel=PANEL_SENTINELONE,
                    hidden=PANEL_SENTINELONE not in visible_panels,
                ),
            ] = None,
            sentinelone_api_url: Annotated[
                str | None,
                typer.Option(
                    "--sentinelone-api-url",
                    help="SentinelOne API URL.",
                    rich_help_panel=PANEL_SENTINELONE,
                    hidden=PANEL_SENTINELONE not in visible_panels,
                ),
            ] = None,
            sentinelone_api_token_env_var: Annotated[
                str,
                typer.Option(
                    "--sentinelone-api-token-env-var",
                    help="Environment variable name containing SentinelOne API token.",
                    rich_help_panel=PANEL_SENTINELONE,
                    hidden=PANEL_SENTINELONE not in visible_panels,
                ),
            ] = "SENTINELONE_API_TOKEN",
            # =================================================================
            # Keycloak Options
            # =================================================================
            keycloak_client_id: Annotated[
                str | None,
                typer.Option(
                    "--keycloak-client-id",
                    help="Keycloak client ID to sync.",
                    rich_help_panel=PANEL_KEYCLOAK,
                    hidden=PANEL_KEYCLOAK not in visible_panels,
                ),
            ] = None,
            keycloak_client_secret_env_var: Annotated[
                str,
                typer.Option(
                    "--keycloak-client-secret-env-var",
                    help="Environment variable name containing Keycloak client secret.",
                    rich_help_panel=PANEL_KEYCLOAK,
                    hidden=PANEL_KEYCLOAK not in visible_panels,
                ),
            ] = "KEYCLOAK_CLIENT_SECRET",
            keycloak_url: Annotated[
                str | None,
                typer.Option(
                    "--keycloak-url",
                    help="Keycloak base URL.",
                    rich_help_panel=PANEL_KEYCLOAK,
                    hidden=PANEL_KEYCLOAK not in visible_panels,
                ),
            ] = None,
            keycloak_realm: Annotated[
                str,
                typer.Option(
                    "--keycloak-realm",
                    help="Keycloak realm for authentication (all realms will be synced).",
                    rich_help_panel=PANEL_KEYCLOAK,
                    hidden=PANEL_KEYCLOAK not in visible_panels,
                ),
            ] = "master",
            # =================================================================
            # Slack Options
            # =================================================================
            slack_token_env_var: Annotated[
                str | None,
                typer.Option(
                    "--slack-token-env-var",
                    help="Environment variable name containing Slack token.",
                    rich_help_panel=PANEL_SLACK,
                    hidden=PANEL_SLACK not in visible_panels,
                ),
            ] = None,
            slack_teams: Annotated[
                str | None,
                typer.Option(
                    "--slack-teams",
                    help="Comma-separated list of Slack Team IDs to sync.",
                    rich_help_panel=PANEL_SLACK,
                    hidden=PANEL_SLACK not in visible_panels,
                ),
            ] = None,
            slack_channels_memberships: Annotated[
                bool,
                typer.Option(
                    "--slack-channels-memberships",
                    help="Pull memberships for Slack channels (can be time consuming).",
                    rich_help_panel=PANEL_SLACK,
                    hidden=PANEL_SLACK not in visible_panels,
                ),
            ] = False,
            # =================================================================
            # Spacelift Options
            # =================================================================
            spacelift_api_endpoint: Annotated[
                str | None,
                typer.Option(
                    "--spacelift-api-endpoint",
                    help="Spacelift GraphQL API endpoint.",
                    rich_help_panel=PANEL_SPACELIFT,
                    hidden=PANEL_SPACELIFT not in visible_panels,
                ),
            ] = None,
            spacelift_api_token_env_var: Annotated[
                str,
                typer.Option(
                    "--spacelift-api-token-env-var",
                    help="Environment variable name containing Spacelift API token.",
                    rich_help_panel=PANEL_SPACELIFT,
                    hidden=PANEL_SPACELIFT not in visible_panels,
                ),
            ] = "SPACELIFT_API_TOKEN",
            spacelift_api_key_id_env_var: Annotated[
                str,
                typer.Option(
                    "--spacelift-api-key-id-env-var",
                    help="Environment variable name containing Spacelift API key ID.",
                    rich_help_panel=PANEL_SPACELIFT,
                    hidden=PANEL_SPACELIFT not in visible_panels,
                ),
            ] = "SPACELIFT_API_KEY_ID",
            spacelift_api_key_secret_env_var: Annotated[
                str,
                typer.Option(
                    "--spacelift-api-key-secret-env-var",
                    help="Environment variable name containing Spacelift API key secret.",
                    rich_help_panel=PANEL_SPACELIFT,
                    hidden=PANEL_SPACELIFT not in visible_panels,
                ),
            ] = "SPACELIFT_API_KEY_SECRET",
            spacelift_ec2_ownership_aws_profile: Annotated[
                str | None,
                typer.Option(
                    "--spacelift-ec2-ownership-aws-profile",
                    help="AWS profile for fetching EC2 ownership data from S3.",
                    rich_help_panel=PANEL_SPACELIFT,
                    hidden=PANEL_SPACELIFT not in visible_panels,
                ),
            ] = None,
            spacelift_ec2_ownership_s3_bucket: Annotated[
                str | None,
                typer.Option(
                    "--spacelift-ec2-ownership-s3-bucket",
                    help="S3 bucket for EC2 ownership CloudTrail data.",
                    rich_help_panel=PANEL_SPACELIFT,
                    hidden=PANEL_SPACELIFT not in visible_panels,
                ),
            ] = None,
            spacelift_ec2_ownership_s3_prefix: Annotated[
                str | None,
                typer.Option(
                    "--spacelift-ec2-ownership-s3-prefix",
                    help="S3 prefix for EC2 ownership CloudTrail data.",
                    rich_help_panel=PANEL_SPACELIFT,
                    hidden=PANEL_SPACELIFT not in visible_panels,
                ),
            ] = None,
            # =================================================================
            # StatsD Metrics Options
            # =================================================================
            statsd_enabled: Annotated[
                bool,
                typer.Option(
                    "--statsd-enabled",
                    help="Enable sending metrics using statsd.",
                    rich_help_panel=PANEL_STATSD,
                ),
            ] = False,
            statsd_prefix: Annotated[
                str,
                typer.Option(
                    "--statsd-prefix",
                    help="Prefix for statsd metrics.",
                    rich_help_panel=PANEL_STATSD,
                ),
            ] = "",
            statsd_host: Annotated[
                str,
                typer.Option(
                    "--statsd-host",
                    help="StatsD server IP address.",
                    rich_help_panel=PANEL_STATSD,
                ),
            ] = "127.0.0.1",
            statsd_port: Annotated[
                int,
                typer.Option(
                    "--statsd-port",
                    help="StatsD server port.",
                    rich_help_panel=PANEL_STATSD,
                ),
            ] = 8125,
            # =================================================================
            # Analysis Options
            # =================================================================
            analysis_job_directory: Annotated[
                str | None,
                typer.Option(
                    "--analysis-job-directory",
                    help="Path to directory containing analysis jobs to run at sync conclusion.",
                    rich_help_panel=PANEL_ANALYSIS,
                ),
            ] = None,
        ) -> None:
            """
            Run cartography sync to pull infrastructure data into Neo4j.

            This command pulls configuration data from multiple sources, loads it
            into Neo4j, and runs arbitrary enrichment and analysis on that data.
            """
            # Configure logging based on verbosity
            if verbose:
                logging.getLogger("cartography").setLevel(logging.DEBUG)
            elif quiet:
                logging.getLogger("cartography").setLevel(logging.WARNING)
            else:
                logging.getLogger("cartography").setLevel(logging.INFO)

            logger.debug("Launching cartography with CLI configuration")

            # Handle Neo4j password
            neo4j_password = None
            if neo4j_user:
                if neo4j_password_prompt:
                    logger.info(
                        "Reading password for Neo4j user '%s' interactively.",
                        neo4j_user,
                    )
                    neo4j_password = getpass.getpass()
                elif neo4j_password_env_var:
                    logger.debug(
                        "Reading password for Neo4j user '%s' from environment variable '%s'.",
                        neo4j_user,
                        neo4j_password_env_var,
                    )
                    neo4j_password = os.environ.get(neo4j_password_env_var)
                if not neo4j_password:
                    logger.warning(
                        "Neo4j username was provided but a password could not be found.",
                    )

            # Load sync helpers lazily so --help/--version don't import all intel modules.
            import cartography.sync

            # Update sync if selected_modules specified
            sync = cli_instance.sync
            if selected_modules:
                sync = cartography.sync.build_sync(selected_modules)
            elif sync is None:
                sync = cartography.sync.build_default_sync()

            # Validate AWS options
            if aws_requested_syncs:
                from cartography.intel.aws.util.common import (
                    parse_and_validate_aws_requested_syncs,
                )

                parse_and_validate_aws_requested_syncs(aws_requested_syncs)
            if aws_regions:
                from cartography.intel.aws.util.common import (
                    parse_and_validate_aws_regions,
                )

                parse_and_validate_aws_regions(aws_regions)

            # Read Azure client secret
            azure_client_secret = None
            if azure_sp_auth and azure_client_secret_env_var:
                logger.debug(
                    "Reading Client Secret for Azure from environment variable %s",
                    azure_client_secret_env_var,
                )
                azure_client_secret = os.environ.get(azure_client_secret_env_var)

            # Read Entra client secret
            entra_client_secret = None
            if entra_tenant_id and entra_client_id and entra_client_secret_env_var:
                logger.debug(
                    "Reading Client Secret for Entra from environment variable %s",
                    entra_client_secret_env_var,
                )
                entra_client_secret = os.environ.get(entra_client_secret_env_var)

            # Read Okta API key
            okta_api_key = None
            if okta_org_id and okta_api_key_env_var:
                logger.debug(
                    "Reading API key for Okta from environment variable %s",
                    okta_api_key_env_var,
                )
                okta_api_key = os.environ.get(okta_api_key_env_var)

            # Read GitHub config
            github_config = None
            if github_config_env_var:
                logger.debug(
                    "Reading config for GitHub from environment variable %s",
                    github_config_env_var,
                )
                github_config = os.environ.get(github_config_env_var)

            # Read DigitalOcean token
            digitalocean_token = None
            if digitalocean_token_env_var:
                logger.debug(
                    "Reading token for DigitalOcean from environment variable %s",
                    digitalocean_token_env_var,
                )
                digitalocean_token = os.environ.get(digitalocean_token_env_var)

            # Read Jamf password
            jamf_password = None
            if jamf_base_uri:
                if jamf_user and jamf_password_env_var:
                    logger.debug(
                        "Reading password for Jamf from environment variable %s",
                        jamf_password_env_var,
                    )
                    jamf_password = os.environ.get(jamf_password_env_var)
                if not jamf_user:
                    logger.warning("A Jamf base URI was provided but a user was not.")
                if jamf_user and not jamf_password:
                    logger.warning("A Jamf password could not be found.")

            # Read Kandji token
            kandji_token = None
            if kandji_base_uri:
                if kandji_token_env_var:
                    logger.debug(
                        "Reading Kandji API token from environment variable %s",
                        kandji_token_env_var,
                    )
                    kandji_token = os.environ.get(kandji_token_env_var)
                elif os.environ.get("KANDJI_TOKEN"):
                    logger.debug(
                        "Reading Kandji API token from environment variable KANDJI_TOKEN",
                    )
                    kandji_token = os.environ.get("KANDJI_TOKEN")
                else:
                    logger.warning(
                        "A Kandji base URI was provided but a token was not."
                    )

            if statsd_enabled:
                logger.debug(
                    "statsd enabled. Sending metrics to server %s:%d. Metrics have prefix '%s'.",
                    statsd_host,
                    statsd_port,
                    statsd_prefix,
                )

            # Read PagerDuty API key
            pagerduty_api_key = None
            if pagerduty_api_key_env_var:
                logger.debug(
                    "Reading API key for PagerDuty from environment variable %s",
                    pagerduty_api_key_env_var,
                )
                pagerduty_api_key = os.environ.get(pagerduty_api_key_env_var)

            # Read CrowdStrike credentials
            crowdstrike_client_id = None
            if crowdstrike_client_id_env_var:
                logger.debug(
                    "Reading client ID for CrowdStrike from environment variable %s",
                    crowdstrike_client_id_env_var,
                )
                crowdstrike_client_id = os.environ.get(crowdstrike_client_id_env_var)

            crowdstrike_client_secret = None
            if crowdstrike_client_secret_env_var:
                logger.debug(
                    "Reading client secret for CrowdStrike from environment variable %s",
                    crowdstrike_client_secret_env_var,
                )
                crowdstrike_client_secret = os.environ.get(
                    crowdstrike_client_secret_env_var
                )

            # Read GSuite config
            gsuite_config = None
            if gsuite_tokens_env_var:
                logger.debug(
                    "Reading config for GSuite from environment variable %s",
                    gsuite_tokens_env_var,
                )
                gsuite_config = os.environ.get(gsuite_tokens_env_var)

            # Read Google Workspace config
            googleworkspace_config = None
            if googleworkspace_tokens_env_var:
                logger.debug(
                    "Reading config for Google Workspace from environment variable %s",
                    googleworkspace_tokens_env_var,
                )
                googleworkspace_config = os.environ.get(googleworkspace_tokens_env_var)

            # Read LastPass credentials
            lastpass_cid = None
            if lastpass_cid_env_var:
                logger.debug(
                    "Reading CID for LastPass from environment variable %s",
                    lastpass_cid_env_var,
                )
                lastpass_cid = os.environ.get(lastpass_cid_env_var)

            lastpass_provhash = None
            if lastpass_provhash_env_var:
                logger.debug(
                    "Reading provhash for LastPass from environment variable %s",
                    lastpass_provhash_env_var,
                )
                lastpass_provhash = os.environ.get(lastpass_provhash_env_var)

            # Read BigFix password
            bigfix_password = None
            if bigfix_username and bigfix_password_env_var and bigfix_root_url:
                logger.debug(
                    "Reading BigFix password from environment variable %s",
                    bigfix_password_env_var,
                )
                bigfix_password = os.environ.get(bigfix_password_env_var)

            # Read Duo credentials
            duo_api_key = None
            duo_api_secret = None
            if duo_api_key_env_var and duo_api_secret_env_var and duo_api_hostname:
                logger.debug(
                    "Reading Duo credentials from environment variables %s, %s",
                    duo_api_key_env_var,
                    duo_api_secret_env_var,
                )
                duo_api_key = os.environ.get(duo_api_key_env_var)
                duo_api_secret = os.environ.get(duo_api_secret_env_var)

            # Read GitLab token
            gitlab_token = None
            if gitlab_url and gitlab_token_env_var:
                logger.debug(
                    "Reading GitLab token from environment variable %s",
                    gitlab_token_env_var,
                )
                gitlab_token = os.environ.get(gitlab_token_env_var)

            # Read Workday password
            workday_api_password = None
            if workday_api_url and workday_api_login and workday_api_password_env_var:
                logger.debug(
                    "Reading Workday API password from environment variable %s",
                    workday_api_password_env_var,
                )
                workday_api_password = os.environ.get(workday_api_password_env_var)

            # Read Semgrep token
            semgrep_app_token = None
            if semgrep_app_token_env_var:
                logger.debug(
                    "Reading Semgrep app token from environment variable %s",
                    semgrep_app_token_env_var,
                )
                semgrep_app_token = os.environ.get(semgrep_app_token_env_var)

            if semgrep_dependency_ecosystems:
                from cartography.intel.semgrep.dependencies import (
                    parse_and_validate_semgrep_ecosystems,
                )

                parse_and_validate_semgrep_ecosystems(semgrep_dependency_ecosystems)

            # Read CVE API key
            cve_api_key = None
            if cve_api_key_env_var:
                logger.debug(
                    "Reading CVE API key from environment variable %s",
                    cve_api_key_env_var,
                )
                cve_api_key = os.environ.get(cve_api_key_env_var)

            # Read SnipeIT token
            snipeit_token = None
            if snipeit_base_uri:
                if snipeit_token_env_var:
                    logger.debug(
                        "Reading SnipeIT API token from environment variable %s",
                        snipeit_token_env_var,
                    )
                    snipeit_token = os.environ.get(snipeit_token_env_var)
                elif os.environ.get("SNIPEIT_TOKEN"):
                    logger.debug(
                        "Reading SnipeIT API token from environment variable SNIPEIT_TOKEN",
                    )
                    snipeit_token = os.environ.get("SNIPEIT_TOKEN")
                else:
                    logger.warning(
                        "A SnipeIT base URI was provided but a token was not."
                    )

            # Read Tailscale token
            tailscale_token = None
            if tailscale_token_env_var:
                logger.debug(
                    "Reading Tailscale API token from environment variable %s",
                    tailscale_token_env_var,
                )
                tailscale_token = os.environ.get(tailscale_token_env_var)

            # Read Cloudflare token
            cloudflare_token = None
            if cloudflare_token_env_var:
                logger.debug(
                    "Reading Cloudflare API key from environment variable %s",
                    cloudflare_token_env_var,
                )
                cloudflare_token = os.environ.get(cloudflare_token_env_var)

            # Read OpenAI API key
            openai_apikey = None
            if openai_apikey_env_var:
                logger.debug(
                    "Reading OpenAI API key from environment variable %s",
                    openai_apikey_env_var,
                )
                openai_apikey = os.environ.get(openai_apikey_env_var)

            # Read Anthropic API key
            anthropic_apikey = None
            if anthropic_apikey_env_var:
                logger.debug(
                    "Reading Anthropic API key from environment variable %s",
                    anthropic_apikey_env_var,
                )
                anthropic_apikey = os.environ.get(anthropic_apikey_env_var)

            # Read Airbyte client secret
            airbyte_client_secret = None
            if airbyte_client_id and airbyte_client_secret_env_var:
                logger.debug(
                    "Reading Airbyte client secret from environment variable %s",
                    airbyte_client_secret_env_var,
                )
                airbyte_client_secret = os.environ.get(airbyte_client_secret_env_var)

            # Log Trivy config
            if trivy_s3_bucket:
                logger.debug("Trivy S3 bucket: %s", trivy_s3_bucket)
            if trivy_s3_prefix:
                logger.debug("Trivy S3 prefix: %s", trivy_s3_prefix)
            if trivy_results_dir:
                logger.debug("Trivy results dir: %s", trivy_results_dir)

            # Read Scaleway secret key
            scaleway_secret_key = None
            if scaleway_secret_key_env_var:
                logger.debug(
                    "Reading Scaleway secret key from environment variable %s",
                    scaleway_secret_key_env_var,
                )
                scaleway_secret_key = os.environ.get(scaleway_secret_key_env_var)

            # Parse SentinelOne account IDs
            sentinelone_account_ids_list = None
            if sentinelone_account_ids:
                sentinelone_account_ids_list = [
                    id.strip() for id in sentinelone_account_ids.split(",")
                ]
                logger.debug(
                    "Parsed %d SentinelOne account IDs to sync",
                    len(sentinelone_account_ids_list),
                )

            # Read SentinelOne API token
            sentinelone_api_token = None
            if sentinelone_api_url and sentinelone_api_token_env_var:
                logger.debug(
                    "Reading SentinelOne API token from environment variable %s",
                    sentinelone_api_token_env_var,
                )
                sentinelone_api_token = os.environ.get(sentinelone_api_token_env_var)

            # Read Keycloak client secret
            keycloak_client_secret = None
            if keycloak_client_secret_env_var:
                logger.debug(
                    "Reading Keycloak client secret from environment variable %s",
                    keycloak_client_secret_env_var,
                )
                keycloak_client_secret = os.environ.get(keycloak_client_secret_env_var)

            # Read Slack token
            slack_token = None
            if slack_token_env_var:
                logger.debug(
                    "Reading Slack token from environment variable %s",
                    slack_token_env_var,
                )
                slack_token = os.environ.get(slack_token_env_var)

            # Read Spacelift credentials
            spacelift_api_endpoint_resolved = spacelift_api_endpoint
            if not spacelift_api_endpoint_resolved:
                spacelift_api_endpoint_resolved = os.environ.get(
                    "SPACELIFT_API_ENDPOINT"
                )

            spacelift_api_token = None
            spacelift_api_key_id = None
            spacelift_api_key_secret = None

            if spacelift_api_endpoint_resolved:
                if spacelift_api_token_env_var:
                    logger.debug(
                        "Reading Spacelift API token from environment variable %s",
                        spacelift_api_token_env_var,
                    )
                    spacelift_api_token = os.environ.get(spacelift_api_token_env_var)

                if spacelift_api_key_id_env_var:
                    logger.debug(
                        "Reading Spacelift API key ID from environment variable %s",
                        spacelift_api_key_id_env_var,
                    )
                    spacelift_api_key_id = os.environ.get(spacelift_api_key_id_env_var)

                if spacelift_api_key_secret_env_var:
                    logger.debug(
                        "Reading Spacelift API key secret from environment variable %s",
                        spacelift_api_key_secret_env_var,
                    )
                    spacelift_api_key_secret = os.environ.get(
                        spacelift_api_key_secret_env_var
                    )

            # Build the Config object
            config = Config(
                neo4j_uri=neo4j_uri,
                neo4j_user=neo4j_user,
                neo4j_password=neo4j_password,
                neo4j_max_connection_lifetime=neo4j_max_connection_lifetime,
                neo4j_database=neo4j_database,
                selected_modules=selected_modules,
                update_tag=update_tag,
                aws_sync_all_profiles=aws_sync_all_profiles,
                aws_regions=aws_regions,
                aws_best_effort_mode=aws_best_effort_mode,
                aws_cloudtrail_management_events_lookback_hours=aws_cloudtrail_management_events_lookback_hours,
                experimental_aws_inspector_batch=experimental_aws_inspector_batch,
                azure_sync_all_subscriptions=azure_sync_all_subscriptions,
                azure_sp_auth=azure_sp_auth,
                azure_tenant_id=azure_tenant_id,
                azure_client_id=azure_client_id,
                azure_client_secret=azure_client_secret,
                azure_subscription_id=azure_subscription_id,
                entra_tenant_id=entra_tenant_id,
                entra_client_id=entra_client_id,
                entra_client_secret=entra_client_secret,
                aws_requested_syncs=aws_requested_syncs,
                aws_guardduty_severity_threshold=aws_guardduty_severity_threshold,
                analysis_job_directory=analysis_job_directory,
                oci_sync_all_profiles=oci_sync_all_profiles,
                okta_org_id=okta_org_id,
                okta_api_key=okta_api_key,
                okta_saml_role_regex=okta_saml_role_regex,
                github_config=github_config,
                github_commit_lookback_days=github_commit_lookback_days,
                digitalocean_token=digitalocean_token,
                permission_relationships_file=permission_relationships_file,
                azure_permission_relationships_file=azure_permission_relationships_file,
                gcp_permission_relationships_file=gcp_permission_relationships_file,
                jamf_base_uri=jamf_base_uri,
                jamf_user=jamf_user,
                jamf_password=jamf_password,
                kandji_base_uri=kandji_base_uri,
                kandji_tenant_id=kandji_tenant_id,
                kandji_token=kandji_token,
                k8s_kubeconfig=k8s_kubeconfig,
                managed_kubernetes=managed_kubernetes,
                statsd_enabled=statsd_enabled,
                statsd_prefix=statsd_prefix,
                statsd_host=statsd_host,
                statsd_port=statsd_port,
                pagerduty_api_key=pagerduty_api_key,
                pagerduty_request_timeout=pagerduty_request_timeout,
                nist_cve_url=nist_cve_url,
                cve_enabled=cve_enabled,
                cve_api_key=cve_api_key,
                crowdstrike_client_id=crowdstrike_client_id,
                crowdstrike_client_secret=crowdstrike_client_secret,
                crowdstrike_api_url=crowdstrike_api_url,
                gsuite_auth_method=gsuite_auth_method,
                gsuite_config=gsuite_config,
                googleworkspace_auth_method=googleworkspace_auth_method,
                googleworkspace_config=googleworkspace_config,
                lastpass_cid=lastpass_cid,
                lastpass_provhash=lastpass_provhash,
                bigfix_username=bigfix_username,
                bigfix_password=bigfix_password,
                bigfix_root_url=bigfix_root_url,
                duo_api_key=duo_api_key,
                duo_api_secret=duo_api_secret,
                duo_api_hostname=duo_api_hostname,
                workday_api_url=workday_api_url,
                workday_api_login=workday_api_login,
                workday_api_password=workday_api_password,
                gitlab_url=gitlab_url,
                gitlab_token=gitlab_token,
                gitlab_organization_id=gitlab_organization_id,
                gitlab_commits_since_days=gitlab_commits_since_days,
                semgrep_app_token=semgrep_app_token,
                semgrep_dependency_ecosystems=semgrep_dependency_ecosystems,
                snipeit_base_uri=snipeit_base_uri,
                snipeit_token=snipeit_token,
                snipeit_tenant_id=snipeit_tenant_id,
                tailscale_token=tailscale_token,
                tailscale_org=tailscale_org,
                tailscale_base_url=tailscale_base_url,
                cloudflare_token=cloudflare_token,
                openai_apikey=openai_apikey,
                openai_org_id=openai_org_id,
                anthropic_apikey=anthropic_apikey,
                airbyte_client_id=airbyte_client_id,
                airbyte_client_secret=airbyte_client_secret,
                airbyte_api_url=airbyte_api_url,
                trivy_s3_bucket=trivy_s3_bucket,
                trivy_s3_prefix=trivy_s3_prefix,
                ontology_users_source=ontology_users_source,
                ontology_devices_source=ontology_devices_source,
                trivy_results_dir=trivy_results_dir,
                scaleway_access_key=scaleway_access_key,
                scaleway_secret_key=scaleway_secret_key,
                scaleway_org=scaleway_org,
                sentinelone_api_url=sentinelone_api_url,
                sentinelone_api_token=sentinelone_api_token,
                sentinelone_account_ids=sentinelone_account_ids_list,
                spacelift_api_endpoint=spacelift_api_endpoint_resolved,
                spacelift_api_token=spacelift_api_token,
                spacelift_api_key_id=spacelift_api_key_id,
                spacelift_api_key_secret=spacelift_api_key_secret,
                spacelift_ec2_ownership_aws_profile=spacelift_ec2_ownership_aws_profile,
                spacelift_ec2_ownership_s3_bucket=spacelift_ec2_ownership_s3_bucket,
                spacelift_ec2_ownership_s3_prefix=spacelift_ec2_ownership_s3_prefix,
                keycloak_client_id=keycloak_client_id,
                keycloak_client_secret=keycloak_client_secret,
                keycloak_realm=keycloak_realm,
                keycloak_url=keycloak_url,
                slack_token=slack_token,
                slack_teams=slack_teams,
                slack_channels_memberships=slack_channels_memberships,
            )

            # Run the sync
            cartography.sync.run_with_config(sync, config)

        return app


def main(argv=None):
    """
    Default entrypoint for the cartography command line interface.

    This function sets up basic logging configuration and creates a CLI instance
    with the default cartography sync configuration. It serves as the main entry
    point when cartography is executed as a command line tool.

    Args:
        argv: Optional command line arguments. If None, uses sys.argv[1:].
              Should be a list of strings representing command line parameters.

    Returns:
        Does not return - calls sys.exit() with the appropriate exit code.
        Exit code 0 indicates successful execution, non-zero indicates errors.
    """
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("azure.identity").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("slack_sdk").setLevel(logging.WARNING)
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
        logging.WARNING
    )

    argv = argv if argv is not None else sys.argv[1:]
    sys.exit(CLI(prog="cartography").main(argv))
