import argparse
import logging
import time
from collections import OrderedDict
from typing import Callable
from typing import List
from typing import Tuple
from typing import Union

import neo4j.exceptions
from neo4j import GraphDatabase
from statsd import StatsClient

import cartography.intel.analysis
import cartography.intel.aws
import cartography.intel.azure
import cartography.intel.bigfix
import cartography.intel.create_indexes
import cartography.intel.crowdstrike
import cartography.intel.cve
import cartography.intel.digitalocean
import cartography.intel.duo
import cartography.intel.gcp
import cartography.intel.github
import cartography.intel.gsuite
import cartography.intel.kandji
import cartography.intel.kubernetes
import cartography.intel.lastpass
import cartography.intel.oci
import cartography.intel.okta
import cartography.intel.semgrep
import cartography.intel.snipeit
from cartography.config import Config
from cartography.stats import set_stats_client
from cartography.util import STATUS_FAILURE
from cartography.util import STATUS_SUCCESS

logger = logging.getLogger(__name__)


TOP_LEVEL_MODULES = OrderedDict({  # preserve order so that the default sync always runs `analysis` at the very end
    'create-indexes': cartography.intel.create_indexes.run,
    'aws': cartography.intel.aws.start_aws_ingestion,
    'azure': cartography.intel.azure.start_azure_ingestion,
    'crowdstrike': cartography.intel.crowdstrike.start_crowdstrike_ingestion,
    'gcp': cartography.intel.gcp.start_gcp_ingestion,
    'gsuite': cartography.intel.gsuite.start_gsuite_ingestion,
    'cve': cartography.intel.cve.start_cve_ingestion,
    'oci': cartography.intel.oci.start_oci_ingestion,
    'okta': cartography.intel.okta.start_okta_ingestion,
    'github': cartography.intel.github.start_github_ingestion,
    'digitalocean': cartography.intel.digitalocean.start_digitalocean_ingestion,
    'kandji': cartography.intel.kandji.start_kandji_ingestion,
    'kubernetes': cartography.intel.kubernetes.start_k8s_ingestion,
    'lastpass': cartography.intel.lastpass.start_lastpass_ingestion,
    'bigfix': cartography.intel.bigfix.start_bigfix_ingestion,
    'duo': cartography.intel.duo.start_duo_ingestion,
    'semgrep': cartography.intel.semgrep.start_semgrep_ingestion,
    'snipeit': cartography.intel.snipeit.start_snipeit_ingestion,
    'analysis': cartography.intel.analysis.run,
})


class Sync:
    """
    A cartography sync task.

    The role of the sync task is to ensure the data in the graph database represents reality. It does this by executing
    a sequence of sync "stages" which are responsible for retrieving data from various sources (APIs, files, etc.),
    pushing that data to Neo4j, and removing now-invalid nodes and relationships from the graph. An instance of this
    class can be configured to run any number of stages in a specific order.
    """

    def __init__(self):
        # NOTE we may need meta-stages at some point to allow hooking into pre-sync, sync, and post-sync
        self._stages = OrderedDict()

    def add_stage(self, name: str, func: Callable) -> None:
        """
        Add one stage to the sync task.

        :type name: string
        :param name: The name of the stage.
        :type func: Callable
        :param func: The object to call when the stage is executed.
        """
        self._stages[name] = func

    def add_stages(self, stages: List[Tuple[str, Callable]]) -> None:
        """
        Add multiple stages to the sync task.

        :type stages: List[Tuple[string, Callable]]
        :param stages: A list of stage names and stage callable pairs.
        """
        for name, func in stages:
            self.add_stage(name, func)

    def run(self, neo4j_driver: neo4j.Driver, config: Union[Config, argparse.Namespace]) -> int:
        """
        Execute all stages in the sync task in sequence.

        :type neo4j_driver: neo4j.Driver
        :param neo4j_driver: Neo4j driver object.
        :type config: cartography.config.Config
        :param config: Configuration for the sync run.
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
                    logger.exception("Unhandled exception during sync stage '%s'", stage_name)
                    raise  # TODO this should be configurable
                logger.info("Finishing sync stage '%s'", stage_name)
        logger.info("Finishing sync with update tag '%d'", config.update_tag)
        return STATUS_SUCCESS


def run_with_config(sync: Sync, config: Union[Config, argparse.Namespace]) -> int:
    """
    Execute the cartography.sync.Sync.run method with parameters built from the given configuration object.

    This function will create a Neo4j driver object from the given Neo4j configuration options (URI, auth, etc.) and
    will choose a sensible update tag if one is not specified in the given configuration.

    :type sync: cartography.sync.Sync
    :param sync: A sync task to run.
    :type config: cartography.config.Config
    :param config: The configuration to use to run the sync task.
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
    Build the default cartography sync, which runs all intelligence modules shipped with the cartography package.

    :rtype: cartography.sync.Sync
    :return: The default cartography sync object.
    """
    sync = Sync()
    sync.add_stages([
        (stage_name, stage_func) for stage_name, stage_func in TOP_LEVEL_MODULES.items()
    ])
    return sync


def parse_and_validate_selected_modules(selected_modules: str) -> List[str]:
    """
    Ensures that user-selected modules passed through the CLI are valid and parses them to a list of str.
    :param selected_modules: comma separated string of module names provided by user
    :return: A validated list of module names that we will run
    """
    validated_modules: List[str] = []
    for module in selected_modules.split(','):
        module = module.strip()

        if module in TOP_LEVEL_MODULES.keys():
            validated_modules.append(module)
        else:
            valid_modules = ', '.join(TOP_LEVEL_MODULES.keys())
            raise ValueError(
                f'Error parsing `selected_modules`. You specified "{selected_modules}". '
                f'Please check that your string is formatted properly. '
                f'Example valid input looks like "aws,gcp,analysis" or "azure, oci, crowdstrike". '
                f'Our full list of valid values is: {valid_modules}.',
            )
    return validated_modules


def build_sync(selected_modules_as_str: str) -> Sync:
    """
    Returns a cartography sync object where all the sync stages are from the user-specified comma separated list of
    modules to run.
    """
    selected_modules = parse_and_validate_selected_modules(selected_modules_as_str)
    sync = Sync()
    sync.add_stages(
        [(sync_name, TOP_LEVEL_MODULES[sync_name]) for sync_name in selected_modules],
    )
    return sync
