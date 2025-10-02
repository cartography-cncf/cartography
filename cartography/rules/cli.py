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

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # List command
        list_parser = subparsers.add_parser(
            "list",
            help="List available frameworks, requirements, and facts",
        )
        list_parser.add_argument(
            "framework",
            nargs="?",
            help="Framework to inspect (e.g., mitre-attack)",
        )
        list_parser.add_argument(
            "requirement",
            nargs="?",
            help="Requirement ID to inspect (e.g., T1190)",
        )

        # Run command
        run_parser = subparsers.add_parser(
            "run",
            help="Execute a security framework",
        )
        available_frameworks = list(FRAMEWORKS.keys()) + ["all"]
        run_parser.add_argument(
            "framework",
            choices=available_frameworks,
            help='Security framework to execute (or "all" to execute all frameworks)',
        )
        run_parser.add_argument(
            "--uri",
            default=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            help="Neo4j URI (default: bolt://localhost:7687)",
        )
        run_parser.add_argument(
            "--user",
            default=os.getenv("NEO4J_USER", "neo4j"),
            help="Neo4j username (default: neo4j)",
        )
        run_parser.add_argument(
            "--neo4j-password-env-var",
            type=str,
            default=None,
            help="The name of an environment variable containing a password with which to authenticate to Neo4j.",
        )
        run_parser.add_argument(
            "--neo4j-password-prompt",
            action="store_true",
            help=(
                "Present an interactive prompt for a password with which to authenticate to Neo4j. This parameter "
                "supersedes other methods of supplying a Neo4j password."
            ),
        )
        run_parser.add_argument(
            "--database",
            default=os.getenv("NEO4J_DATABASE", "neo4j"),
            help="Neo4j database name (default: neo4j)",
        )
        run_parser.add_argument(
            "--output",
            choices=["text", "json"],
            default="text",
            help="Output format (default: text)",
        )

        return parser

    def _list_all_frameworks(self):
        """List all available frameworks."""
        print("\n\033[1mAvailable Frameworks\033[0m\n")
        for framework_name, framework in FRAMEWORKS.items():
            print(f"\033[36m{framework_name}\033[0m")
            print(f"  Name:         {framework.name}")
            print(f"  Version:      {framework.version}")
            print(f"  Requirements: {len(framework.requirements)}")
            total_facts = sum(len(req.facts) for req in framework.requirements)
            print(f"  Total Facts:  {total_facts}")
            if framework.source_url:
                print(f"  Source:       {framework.source_url}")
            print()

    def _list_framework_requirements(self, framework_name: str):
        """List all requirements in a framework."""
        if framework_name not in FRAMEWORKS:
            print(f"Error: Unknown framework '{framework_name}'")
            print(f"Available frameworks: {', '.join(FRAMEWORKS.keys())}")
            return 1

        framework = FRAMEWORKS[framework_name]
        print(f"\n\033[1m{framework.name}\033[0m (v{framework.version})\n")

        for requirement in framework.requirements:
            print(f"\033[36m{requirement.id}\033[0m - {requirement.name}")
            print(f"  Facts: {len(requirement.facts)}")
            if requirement.requirement_url:
                print(f"  URL:   {requirement.requirement_url}")
            print()
        return 0

    def _list_requirement_facts(self, framework_name: str, requirement_id: str):
        """List all facts in a requirement."""
        if framework_name not in FRAMEWORKS:
            print(f"Error: Unknown framework '{framework_name}'")
            print(f"Available frameworks: {', '.join(FRAMEWORKS.keys())}")
            return 1

        framework = FRAMEWORKS[framework_name]

        # Find the requirement (case-insensitive match)
        requirement = None
        for req in framework.requirements:
            if req.id.lower() == requirement_id.lower():
                requirement = req
                break

        if not requirement:
            print(
                f"Error: Requirement '{requirement_id}' not found in framework '{framework_name}'"
            )
            print("\nAvailable requirements:")
            for req in framework.requirements:
                print(f"  {req.id}")
            return 1

        print(f"\n\033[1m{requirement.name}\033[0m\n")
        print(f"ID:  {requirement.id}")
        if requirement.requirement_url:
            print(f"URL: {requirement.requirement_url}")
        print(f"\n\033[1mFacts ({len(requirement.facts)})\033[0m\n")

        for fact in requirement.facts:
            print(f"\033[36m{fact.id}\033[0m")
            print(f"  Name:        {fact.name}")
            print(f"  Description: {fact.description}")
            print(f"  Provider:    {fact.module.value}")
            print()
        return 0

    def main(self, argv):
        """
        Entrypoint for the command line interface.

        :type argv: List of strings
        :param argv: The parameters supplied to the command line program.
        :return: Exit code
        """
        args = self.parser.parse_args(argv)

        # Handle no command
        if not args.command:
            self.parser.print_help()
            return 1

        # Handle list command
        if args.command == "list":
            if args.requirement:
                # List facts in a requirement
                return self._list_requirement_facts(args.framework, args.requirement)
            elif args.framework:
                # List requirements in a framework
                return self._list_framework_requirements(args.framework)
            else:
                # List all frameworks
                self._list_all_frameworks()
                return 0

        # Handle run command
        if args.command == "run":
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

        return 1


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
