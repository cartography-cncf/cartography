import argparse
import logging
import re
import time
from collections import OrderedDict
from pkgutil import iter_modules
from typing import Callable
from typing import List
from typing import Tuple
from typing import Union

import neo4j.exceptions
from neo4j import GraphDatabase
from statsd import StatsClient

import cartography.intel.airbyte
import cartography.intel.analysis
import cartography.intel.anthropic
import cartography.intel.aws
import cartography.intel.azure
import cartography.intel.bigfix
import cartography.intel.cloudflare
import cartography.intel.create_indexes
import cartography.intel.crowdstrike
import cartography.intel.cve
import cartography.intel.digitalocean
import cartography.intel.duo
import cartography.intel.entra
import cartography.intel.gcp
import cartography.intel.github
import cartography.intel.gitlab
import cartography.intel.googleworkspace
import cartography.intel.gsuite
import cartography.intel.jamf
import cartography.intel.kandji
import cartography.intel.keycloak
import cartography.intel.kubernetes
import cartography.intel.lastpass
import cartography.intel.oci
import cartography.intel.okta
import cartography.intel.ontology
import cartography.intel.openai
import cartography.intel.pagerduty
import cartography.intel.scaleway
import cartography.intel.semgrep
import cartography.intel.sentinelone
import cartography.intel.slack
import cartography.intel.snipeit
import cartography.intel.spacelift
import cartography.intel.tailscale
import cartography.intel.trivy
import cartography.intel.workday
from cartography.config import Config
from cartography.stats import set_stats_client
from cartography.util import STATUS_FAILURE
from cartography.util import STATUS_SUCCESS

logger = logging.getLogger(__name__)


TOP_LEVEL_MODULES: OrderedDict[str, Callable[..., None]] = OrderedDict(
    {  # preserve order so that the default sync always runs `analysis` at the very end
        "create-indexes": cartography.intel.create_indexes.run,
        "airbyte": cartography.intel.airbyte.start_airbyte_ingestion,
        "anthropic": cartography.intel.anthropic.start_anthropic_ingestion,
        "aws": cartography.intel.aws.start_aws_ingestion,
        "azure": cartography.intel.azure.start_azure_ingestion,
        "entra": cartography.intel.entra.start_entra_ingestion,
        "cloudflare": cartography.intel.cloudflare.start_cloudflare_ingestion,
        "crowdstrike": cartography.intel.crowdstrike.start_crowdstrike_ingestion,
        "gcp": cartography.intel.gcp.start_gcp_ingestion,
        "googleworkspace": cartography.intel.googleworkspace.start_googleworkspace_ingestion,
        "gsuite": cartography.intel.gsuite.start_gsuite_ingestion,
        "cve": cartography.intel.cve.start_cve_ingestion,
        "oci": cartography.intel.oci.start_oci_ingestion,
        "okta": cartography.intel.okta.start_okta_ingestion,
        "openai": cartography.intel.openai.start_openai_ingestion,
        "github": cartography.intel.github.start_github_ingestion,
        "gitlab": cartography.intel.gitlab.start_gitlab_ingestion,
        "digitalocean": cartography.intel.digitalocean.start_digitalocean_ingestion,
        "kandji": cartography.intel.kandji.start_kandji_ingestion,
        "keycloak": cartography.intel.keycloak.start_keycloak_ingestion,
        "kubernetes": cartography.intel.kubernetes.start_k8s_ingestion,
        "lastpass": cartography.intel.lastpass.start_lastpass_ingestion,
        "bigfix": cartography.intel.bigfix.start_bigfix_ingestion,
        "duo": cartography.intel.duo.start_duo_ingestion,
        "workday": cartography.intel.workday.start_workday_ingestion,
        "scaleway": cartography.intel.scaleway.start_scaleway_ingestion,
        "semgrep": cartography.intel.semgrep.start_semgrep_ingestion,
        "snipeit": cartography.intel.snipeit.start_snipeit_ingestion,
        "tailscale": cartography.intel.tailscale.start_tailscale_ingestion,
        "jamf": cartography.intel.jamf.start_jamf_ingestion,
        "pagerduty": cartography.intel.pagerduty.start_pagerduty_ingestion,
        "trivy": cartography.intel.trivy.start_trivy_ingestion,
        "sentinelone": cartography.intel.sentinelone.start_sentinelone_ingestion,
        "slack": cartography.intel.slack.start_slack_ingestion,
        "spacelift": cartography.intel.spacelift.start_spacelift_ingestion,
        "ontology": cartography.intel.ontology.run,
        # Analysis should be the last stage
        "analysis": cartography.intel.analysis.run,
    }
)


class Sync:
    """
    A cartography synchronization task orchestrator.

    The Sync class is responsible for ensuring the data in the graph database
    accurately represents the current state of reality. It accomplishes this by
    executing a sequence of sync "modules" in a specific order. Each module is
    responsible for:

    - Retrieving data from various sources (APIs, files, etc.)
    - Pushing that data to Neo4j graph database
    - Removing stale nodes and relationships from the graph

    The Sync instance can be configured to run any combination of available
    modules in a user-defined order, providing flexibility for different
    deployment scenarios.

    Attributes:
        _stages: An OrderedDict containing module names mapped to their callable functions.

    Examples:
        Creating a custom sync with specific stages:
        >>> sync = Sync()
        >>> sync.add_stage('aws', cartography.intel.aws.start_aws_ingestion)
        >>> sync.add_stage('analysis', cartography.intel.analysis.run)

        Running multiple stages:
        >>> stages = [
        ...     ('create-indexes', cartography.intel.create_indexes.run),
        ...     ('aws', cartography.intel.aws.start_aws_ingestion),
        ...     ('analysis', cartography.intel.analysis.run)
        ... ]
        >>> sync.add_stages(stages)
        >>> exit_code = sync.run(neo4j_driver, config)

    Note:
        Stages are executed in the order they are added. The 'create-indexes'
        stage should typically be run first, and 'analysis' should be run last.
        Meta-stages for pre-sync, sync, and post-sync hooks may be added in
        future versions.
    """

    def __init__(self):
        # NOTE we may need meta-stages at some point to allow hooking into pre-sync, sync, and post-sync
        self._stages = OrderedDict()

    def add_stage(self, name: str, func: Callable) -> None:
        """
        Add a single stage to the sync task.

        This method registers a new stage with the sync task. Stages are executed
        in the order they are added, so the order of add_stage() calls determines
        the execution sequence.

        Args:
            name: The unique name identifier for the stage. This name is used
                 for logging and identification purposes.
            func: The callable function to execute when this stage runs.
                 The function should accept (neo4j_session, config) parameters.

        Note:
            The stage name should be unique within the sync task. If a stage
            with the same name already exists, it will be replaced. Stage
            functions must follow the standard signature (neo4j_session, config).
        """
        self._stages[name] = func

    def add_stages(self, stages: List[Tuple[str, Callable]]) -> None:
        """
        Add multiple stages to the sync task in batch.

        This method is a convenience function for adding multiple stages at once.
        It iterates through the provided list and calls add_stage() for each
        stage tuple.

        Args:
            stages: A list of tuples where each tuple contains (stage_name, stage_function).
                   The stage_name should be a unique string identifier, and stage_function
                   should be a callable that accepts (neo4j_session, config) parameters.

        Note:
            Stages are added in the order they appear in the list, which determines
            their execution order. This method is equivalent to calling add_stage()
            for each tuple individually.
        """
        for name, func in stages:
            self.add_stage(name, func)

    def run(
        self,
        neo4j_driver: neo4j.Driver,
        config: Union[Config, argparse.Namespace],
    ) -> int:
        """
        Execute all configured stages in the sync task sequentially.

        This method is the main execution entry point for the sync task. It creates
        a Neo4j session and executes each configured stage in order, providing
        comprehensive logging and error handling.

        Args:
            neo4j_driver: A Neo4j driver instance for database connectivity.
            config: Configuration object containing sync parameters including
                   update_tag, neo4j_database, and stage-specific settings.

        Returns:
            STATUS_SUCCESS (0) if all stages complete successfully.

        Raises:
            KeyboardInterrupt: If user interrupts execution during a stage.
            SystemExit: If system exit is triggered during a stage.
            Exception: Any unhandled exception from module execution.

        Examples:
            >>> sync = build_default_sync()
            >>> driver = GraphDatabase.driver("bolt://localhost:7687")
            >>> exit_code = sync.run(driver, config)
            >>> if exit_code == STATUS_SUCCESS:
            ...     print("Sync completed successfully")

        Note:
            Each stage is executed within the same Neo4j session to maintain
            transaction context. Stages are responsible for their own error
            handling, but unhandled exceptions will terminate the sync process.

            The method logs the start and completion of each module for monitoring
            and debugging purposes.
        """
        logger.info("Starting sync with update tag '%d'", config.update_tag)
        with neo4j_driver.session(database=config.neo4j_database) as neo4j_session:
            for stage_name, stage_func in self._stages.items():
                logger.info("Starting sync stage '%s'", stage_name)
                try:
                    stage_func(neo4j_session, config)
                except (KeyboardInterrupt, SystemExit):
                    logger.warning("Sync interrupted during stage '%s'.", stage_name)
                    raise
                except Exception:
                    logger.exception(
                        "Unhandled exception during sync stage '%s'",
                        stage_name,
                    )
                    raise  # TODO this should be configurable
                logger.info("Finishing sync stage '%s'", stage_name)
        logger.info("Finishing sync with update tag '%d'", config.update_tag)
        return STATUS_SUCCESS

    @classmethod
    def list_intel_modules(cls) -> OrderedDict:
        """
        Discover and list all available modules.

        This class method dynamically discovers all modules in the cartography.intel
        package and returns a dictionary mapping module names to their callable
        ingestion functions. It automatically handles module loading and function
        discovery using naming conventions.

        Returns:
            An OrderedDict where keys are module names and values are callable
            functions that follow the `start_{module}_ingestion` pattern.
            The 'create-indexes' module is always included first, and 'analysis'
            is always included last.

        Examples:
            Getting all available modules:
            >>> modules = Sync.list_intel_modules()
            >>> print(list(modules.keys()))
            ['create-indexes', 'aws', 'gcp', 'github', ..., 'analysis']

            Creating sync with discovered modules:
            >>> modules = Sync.list_intel_modules()
            >>> sync = Sync()
            >>> for name, func in modules.items():
            ...     sync.add_stage(name, func)

        Note:
            The method uses reflection to discover modules and their ingestion
            functions. It expects functions to follow the naming pattern
            `start_{module_name}_ingestion`. Modules that fail to import are
            logged as errors but don't prevent discovery of other modules.

            The 'create-indexes' and 'analysis' modules are handled specially
            to ensure consistent ordering regardless of discovery order.
        """
        available_modules = OrderedDict({})
        available_modules["create-indexes"] = cartography.intel.create_indexes.run
        callable_regex = re.compile(r"^start_(.+)_ingestion$")
        # Load built-in modules
        for intel_module_info in iter_modules(cartography.intel.__path__):
            if intel_module_info.name in ("analysis", "create_indexes"):
                continue
            try:
                logger.debug("Loading module: %s", intel_module_info.name)
                intel_module = __import__(
                    f"cartography.intel.{intel_module_info.name}",
                    fromlist=[""],
                )
            except ImportError as e:
                logger.error(
                    "Failed to import module '%s'. Error: %s",
                    intel_module_info.name,
                    e,
                )
                continue
            logger.debug("Loading module: %s", intel_module_info.name)
            intel_module = __import__(
                f"cartography.intel.{intel_module_info.name}",
                fromlist=[""],
            )
            for k, v in intel_module.__dict__.items():
                if not callable(v):
                    continue
                match_callable_name = callable_regex.match(k)
                if not match_callable_name:
                    continue
                callable_module_name = (
                    match_callable_name.group(1) if match_callable_name else None
                )
                if callable_module_name != intel_module_info.name:
                    logger.debug(
                        "Module name '%s' does not match intel module name '%s'.",
                        callable_module_name,
                        intel_module_info.name,
                    )
                available_modules[intel_module_info.name] = v
        available_modules["ontology"] = cartography.intel.ontology.run
        available_modules["analysis"] = cartography.intel.analysis.run
        return available_modules


def run_with_config(sync: Sync, config: Union[Config, argparse.Namespace]) -> int:
    """
    Execute a sync task with comprehensive configuration and error handling.

    This function serves as a high-level wrapper around Sync.run() that handles
    Neo4j driver creation, authentication, StatsD configuration, and provides
    comprehensive error handling for common connection and authentication issues.

    Args:
        sync: A configured Sync instance with stages to execute.
        config: Configuration object containing Neo4j connection settings,
               authentication credentials, StatsD settings, and other parameters.

    Returns:
        STATUS_SUCCESS (0) if sync completes successfully.
        STATUS_FAILURE (1) if Neo4j connection or authentication fails.
        Other exit codes may be returned by the sync.run() method.

    Examples:
        Running default sync with configuration:
        >>> sync = build_default_sync()
        >>> config.neo4j_uri = "bolt://localhost:7687"
        >>> config.neo4j_user = "neo4j"
        >>> config.neo4j_password = "password"
        >>> exit_code = run_with_config(sync, config)

        Running with StatsD enabled:
        >>> config.statsd_enabled = True
        >>> config.statsd_host = "localhost"
        >>> config.statsd_port = 8125
        >>> exit_code = run_with_config(sync, config)

    Note:
        The function automatically generates an update_tag based on current
        timestamp if one is not provided in the configuration. It handles
        Neo4j driver creation, authentication setup, and provides detailed
        error messages for connection and authentication failures.

        If StatsD is enabled in the configuration, it initializes the global
        StatsD client for metrics collection during the sync process.
    """
    # Initialize statsd client if enabled
    if config.statsd_enabled:
        set_stats_client(
            StatsClient(
                host=config.statsd_host,
                port=config.statsd_port,
                prefix=config.statsd_prefix,
            ),
        )

    neo4j_auth = None
    if config.neo4j_user or config.neo4j_password:
        neo4j_auth = (config.neo4j_user, config.neo4j_password)
    try:
        neo4j_driver = GraphDatabase.driver(
            config.neo4j_uri,
            auth=neo4j_auth,
            max_connection_lifetime=config.neo4j_max_connection_lifetime,
        )
    except neo4j.exceptions.ServiceUnavailable as e:
        logger.debug("Error occurred during Neo4j connect.", exc_info=True)
        logger.error(
            (
                "Unable to connect to Neo4j using the provided URI '%s', an error occurred: '%s'. Make sure the Neo4j "
                "server is running and accessible from your network."
            ),
            config.neo4j_uri,
            e,
        )
        return STATUS_FAILURE
    except neo4j.exceptions.AuthError as e:
        logger.debug("Error occurred during Neo4j auth.", exc_info=True)
        if not neo4j_auth:
            logger.error(
                (
                    "Unable to auth to Neo4j, an error occurred: '%s'. cartography attempted to connect to Neo4j "
                    "without any auth. Check your Neo4j server settings to see if auth is required and, if it is, "
                    "provide cartography with a valid username and password."
                ),
                e,
            )
        else:
            logger.error(
                (
                    "Unable to auth to Neo4j, an error occurred: '%s'. cartography attempted to connect to Neo4j with "
                    "a username and password. Check your Neo4j server settings to see if the username and password "
                    "provided to cartography are valid credentials."
                ),
                e,
            )
        return STATUS_FAILURE
    default_update_tag = int(time.time())
    if not config.update_tag:
        config.update_tag = default_update_tag
    return sync.run(neo4j_driver, config)


def build_default_sync() -> Sync:
    """
    Build the default cartography sync with all available intelligence modules.

    This function creates a Sync instance configured with all intelligence
    modules shipped with cartography. The modules are added in a specific
    order to ensure proper execution sequence, with 'create-indexes' first
    and 'analysis' last.

    Returns:
        A fully configured Sync instance with all available intelligence modules.

    Examples:
        Creating and running default sync:
        >>> sync = build_default_sync()
        >>> exit_code = run_with_config(sync, config)

        Inspecting default stages:
        >>> sync = build_default_sync()
        >>> stage_names = list(sync._stages.keys())
        >>> print(f"Default sync includes {len(stage_names)} stages")

    Note:
        The default sync includes all modules defined in TOP_LEVEL_MODULES,
        which encompasses cloud providers (AWS, GCP, Azure), security tools
        (CrowdStrike, Okta), development platforms (GitHub), and analysis
        capabilities. This provides comprehensive infrastructure mapping
        out of the box.

        For custom sync configurations with specific modules, use build_sync()
        with a selected modules string instead.
    """
    sync = Sync()
    sync.add_stages(
        [
            (stage_name, stage_func)
            for stage_name, stage_func in TOP_LEVEL_MODULES.items()
        ],
    )
    return sync


def parse_and_validate_selected_modules(selected_modules: str) -> List[str]:
    """
    Parse and validate user-selected modules from comma-separated string.

    This function takes a comma-separated string of module names provided by
    the user and validates that each module exists in the available modules.
    It returns a clean list of validated module names.

    Args:
        selected_modules: A comma-separated string of module names (e.g., "aws,gcp,analysis").
                         Module names will be stripped of whitespace.

    Returns:
        A list of validated module names that exist in TOP_LEVEL_MODULES.

    Raises:
        ValueError: If any specified module is not found in the available modules.
                   The error message includes the invalid input and lists all valid options.

    Note:
        Module names are case-sensitive and must exactly match those defined
        in TOP_LEVEL_MODULES. The function is tolerant of whitespace around
        commas but requires exact name matches for validation.
    """
    validated_modules: List[str] = []
    for module in selected_modules.split(","):
        module = module.strip()

        if module in TOP_LEVEL_MODULES.keys():
            validated_modules.append(module)
        else:
            valid_modules = ", ".join(TOP_LEVEL_MODULES.keys())
            raise ValueError(
                f'Error parsing `selected_modules`. You specified "{selected_modules}". '
                f"Please check that your string is formatted properly. "
                f'Example valid input looks like "aws,gcp,analysis" or "azure, oci, crowdstrike". '
                f"Our full list of valid values is: {valid_modules}.",
            )
    return validated_modules


def build_sync(selected_modules_as_str: str) -> Sync:
    """
    Build a custom sync with user-specified modules.

    This function creates a Sync instance configured only with the modules
    specified in the comma-separated string. It provides a way to run a
    subset of available intelligence modules rather than the full default set.

    Args:
        selected_modules_as_str: A comma-separated string of module names to include
                               in the sync (e.g., "aws,gcp,analysis").

    Returns:
        A Sync instance configured with only the specified modules in the order
        they appear in the input string.

    Raises:
        ValueError: If any specified module is invalid (propagated from
                   parse_and_validate_selected_modules).

    Examples:
        Building sync with specific cloud providers:
        >>> sync = build_sync("aws,gcp,azure")
        >>> # Only AWS, GCP, and Azure modules will run

        Building minimal sync with just analysis:
        >>> sync = build_sync("create-indexes,analysis")
        >>> # Only index creation and analysis will run

        Building security-focused sync:
        >>> sync = build_sync("create-indexes,okta,crowdstrike,analysis")
        >>> # Focus on identity and security platforms

    Note:
        The order of modules in the input string determines their execution
        order. It's recommended to include 'create-indexes' first and 'analysis'
        last for optimal results. The function validates all module names
        before creating the sync instance.
    """
    selected_modules = parse_and_validate_selected_modules(selected_modules_as_str)
    sync = Sync()
    sync.add_stages(
        [(sync_name, TOP_LEVEL_MODULES[sync_name]) for sync_name in selected_modules],
    )
    return sync
