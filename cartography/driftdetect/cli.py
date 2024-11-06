import argparse
import getpass
import logging
import os
import sys

from cartography.driftdetect.add_shortcut import run_add_shortcut
from cartography.driftdetect.detect_deviations import run_drift_detection
from cartography.driftdetect.get_states import run_get_states


logger = logging.getLogger(__name__)


class CLI:
    def __init__(self, prog=None):
        self.prog = prog
        self.parser = self._build_parser()

    def _build_parser(self):
        """
        :rtype: argparse.ArgumentParser
        :return: A drift-detection argument parser. Calling parse_args on the argument parser will return an object
                 which implements the driftdetect.config.Config interface.
        """
        parser = argparse.ArgumentParser(
            prog=self.prog,
            description=(
                'drift-detection takes database queries along with their expected states in the cartography-generated '
                'graph database and reports the deviations.'
            ),
            epilog='For more documentation please visit: '
                   'https://cartography-cncf.github.io/cartography/usage/drift-detect.html',
        )
        parser.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            help='Enable verbose logging for drift-detection.',
        )
        parser.add_argument(
            '-q',
            '--quiet',
            action='store_true',
            help='Restrict drift-detection logging to warnings and errors only.',
        )
        subparsers = parser.add_subparsers(
            dest='command',
            help='To get the current drift state, use the command `cartography-detectdrift get-state --neo4j_uri <your '
                 'neo4j_uri> --drift-detection-directory <your drift detection directory>` \n'
                 'To get drift between two state files, use the command `cartography-detectdrift get-drift'
                 '--query-directory <path to query directory> --start-state <beginning drift state file> --end-state '
                 '<final drift state file>'
                 'To add a shortcut between two state files, use the command `cartography-detectdrift add-shortcut'
                 '--query-directory <path to query directory> --shortcut <shortcut name> --file <driftstate filename>',
        )
        parser_get_state = subparsers.add_parser(
            name='get-state',
            help='generates new drift state for each query with the current status of the neo4j database',
        )
        parser_get_state.add_argument(
            '--neo4j-uri',
            type=str,
            default='bolt://localhost:7687',
            help=(
                'A valid Neo4j URI to sync against. See '
                'https://neo4j.com/docs/api/python-driver/current/driver.html#uri for complete documentation on the '
                'structure of a Neo4j URI.'
            ),
        )
        parser_get_state.add_argument(
            '--neo4j-user',
            type=str,
            default=None,
            help='A username with which to authenticate to Neo4j.',
        )
        parser_get_state.add_argument(
            '--neo4j-password-env-var',
            type=str,
            default=None,
            help='The name of an environment variable containing a password with which to authenticate to Neo4j.',
        )
        parser_get_state.add_argument(
            '--neo4j-password-prompt',
            action='store_true',
            help=(
                'Present an interactive prompt for a password with which to authenticate to Neo4j. This parameter '
                'supersedes other methods of supplying a Neo4j password.'
            ),
        )
        parser_get_state.add_argument(
            '--drift-detection-directory',
            type=str,
            default=None,
            help=(
                'A path to a directory containing drift-states to build. Drift-detection will discover all JSON'
                'files in the given directory (and its subdirectories) and construct detectors from'
                'them. Drift-detection does not guarantee the order in which the detector jobs are executed.'
            ),
        )
        parser_get_drift = subparsers.add_parser(
            name='get-drift',
            help=(
                'gets drift between two drift states. Must be between the same detection directory'
            ),
        )
        parser_get_drift.add_argument(
            '--query-directory',
            type=str,
            default=None,
            help=(
                'A path to a directory containing drift-states for a specific query. Drift-detection will read in the'
                'report_info file and specified drift-states from the directory to report the differences between files'
            ),
        )
        parser_get_drift.add_argument(
            '--start-state',
            type=str,
            default=None,
            help=(
                'The filename of the earlier state chronologically to be compared to.'
            ),
        )
        parser_get_drift.add_argument(
            '--end-state',
            type=str,
            default=None,
            help=(
                'The filename of the later state chronologically to be compared to.'
            ),
        )
        parser_add_shortcut = subparsers.add_parser(
            name='add-shortcut',
            help=(
                'Adds a shortcut to a specific file in a query directory.'
            ),
        )
        parser_add_shortcut.add_argument(
            '--query-directory',
            type=str,
            default=None,
            help=(
                'A path to a directory containing drift-states for a specific query.'
            ),
        )
        parser_add_shortcut.add_argument(
            '--shortcut',
            type=str,
            default=None,
            help=(
                'The desired alias for the filename.'
            ),
        )
        parser_add_shortcut.add_argument(
            '--filename',
            type=str,
            default=None,
            help=(
                'The desired name of the file to be replaced.'
            ),
        )
        return parser

    def configure(self, argv):
        """
        Configures logging options for Drift-Detection

        :type argv: string
        :param argv: The parameters supplied to the command line program.
        """
        # TODO support parameter lookup in environment variables if not present on command line
        config = self.parser.parse_args(argv)
        if config.verbose:
            logging.getLogger('driftdetect').setLevel(logging.DEBUG)
        elif config.quiet:
            logging.getLogger('driftdetect').setLevel(logging.WARNING)
        else:
            logging.getLogger('driftdetect').setLevel(logging.INFO)
        logger.debug("Launching driftdetect with CLI configuration: %r", vars(config))
        if config.command == 'get-state':
            config = configure_get_state_neo4j(config)
        return config

    def main(self, argv):
        """
        Entrypoint for the command line interface.

        :type argv: List of strings
        :param argv: The parameters supplied to the command line program.
        """
        config = self.configure(argv)
        try:
            if config.command == 'get-state':
                run_get_states(config)
            elif config.command == 'get-drift':
                run_drift_detection(config)
            elif config.command == 'add-shortcut':
                run_add_shortcut(config)
            else:
                msg = "No command detected. Try --help."
                logger.error(msg)
        except KeyboardInterrupt:
            return 130


def configure_get_state_neo4j(config):
    """
    Extra configuration options for neo4j interaction.

    :type config: Config Object
    :param config:
    :rtype: Config Object
    :return: The config object.
    """
    if config.neo4j_user:
        config.neo4j_password = None
        if config.neo4j_password_prompt:
            logger.info("Reading password for Neo4j user '%s' interactively.", config.neo4j_user)
            config.neo4j_password = getpass.getpass()
        elif config.neo4j_password_env_var:
            logger.debug(
                "Reading password for Neo4j user '%s' from environment variable '%s'.",
                config.neo4j_user,
                config.neo4j_password_env_var,
            )
            config.neo4j_password = os.environ.get(config.neo4j_password_env_var)
        if not config.neo4j_password:
            logger.warning("Neo4j username was provided but a password could not be found.")
    else:
        config.neo4j_password = None
    return config


def main(argv=None):
    """
    Entrypoint for the default cartography command line interface.

    :rtype: int
    :return: The return code.
    """
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('neo4j').setLevel(logging.WARNING)
    argv = argv if argv is not None else sys.argv[1:]
    return CLI(prog="cartography-detectdrift").main(argv)
