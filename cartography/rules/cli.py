"""
Cartography RunRules CLI

Execute security frameworks and present facts about your environment.
"""

import argparse
import getpass
import logging
import os
import sys

from cartography.rules.data.frameworks import FRAMEWORKS
from cartography.rules.runners import run_frameworks


class CLI:
    """
    Command line interface for Cartography security framework execution.
    """

    def __init__(self, prog=None):
        self.prog = prog
        self.parser = self._build_parser()

    def _build_parser(self):
        """
        Build the argument parser for the rules CLI.

        :rtype: argparse.ArgumentParser
        :return: A rules argument parser.
        """
        parser = argparse.ArgumentParser(
            prog=self.prog,
            description="Execute Cartography security frameworks",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="For more documentation please visit: https://github.com/cartography-cncf/cartography",
        )

        available_frameworks = list(FRAMEWORKS.keys()) + ["all"]
        parser.add_argument(
            "framework",
            nargs="?",
            choices=available_frameworks,
            help='Security framework to execute (or "all" to execute all frameworks)',
        )

        parser.add_argument(
            "--list", action="store_true", help="List available frameworks and exit"
        )

        parser.add_argument(
            "--uri",
            default=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            help="Neo4j URI (default: bolt://localhost:7687)",
        )

        parser.add_argument(
            "--user",
            default=os.getenv("NEO4J_USER", "neo4j"),
            help="Neo4j username (default: neo4j)",
        )

        parser.add_argument(
            "--neo4j-password-env-var",
            type=str,
            default=None,
            help="The name of an environment variable containing a password with which to authenticate to Neo4j.",
        )

        parser.add_argument(
            "--neo4j-password-prompt",
            action="store_true",
            help=(
                "Present an interactive prompt for a password with which to authenticate to Neo4j. This parameter "
                "supersedes other methods of supplying a Neo4j password."
            ),
        )

        parser.add_argument(
            "--database",
            default=os.getenv("NEO4J_DATABASE", "neo4j"),
            help="Neo4j database name (default: neo4j)",
        )

        parser.add_argument(
            "--output",
            choices=["text", "json"],
            default="text",
            help="Output format (default: text)",
        )

        return parser

    def main(self, argv):
        """
        Entrypoint for the command line interface.

        :type argv: List of strings
        :param argv: The parameters supplied to the command line program.
        :return: Exit code
        """
        args = self.parser.parse_args(argv)

        # Handle --list option
        if args.list:
            print("Available frameworks:")
            for framework_name, framework in FRAMEWORKS.items():
                print(f"  {framework_name:15} - {framework.name} v{framework.version}")
            print(f"  {'all':15} - Run all frameworks")
            return 0

        # Framework is required if not using --list
        if not args.framework:
            self.parser.error(
                "framework is required (or use --list to see available frameworks)"
            )

        # Get password
        password = None
        if args.neo4j_password_prompt:
            password = getpass.getpass("Enter Neo4j password: ")
        elif args.neo4j_password_env_var:
            password = os.environ.get(args.neo4j_password_env_var)
        else:
            # Fall back to NEO4J_PASSWORD for backward compatibility
            password = os.getenv("NEO4J_PASSWORD")
            if not password:
                password = getpass.getpass("Enter Neo4j password: ")

        # Determine which frameworks to run
        if args.framework == "all":
            frameworks_to_run = list(FRAMEWORKS.keys())
        else:
            frameworks_to_run = [args.framework]

        # Execute framework(s)
        try:
            return run_frameworks(
                frameworks_to_run,
                args.uri,
                args.user,
                password,
                args.database,
                args.output,
            )
        except KeyboardInterrupt:
            return 130


def main(argv=None):
    """
    Entrypoint for the default rules command line interface.

    :rtype: int
    :return: The return code.
    """
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("neo4j").setLevel(logging.ERROR)

    argv = argv if argv is not None else sys.argv[1:]
    return CLI(prog="cartography-runrules").main(argv)


if __name__ == "__main__":
    sys.exit(main())
