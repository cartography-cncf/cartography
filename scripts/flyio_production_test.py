#!/usr/bin/env python3
"""Run a live Fly.io Cartography sync and print proof counts.

This script intentionally derives its result from the sync logs and Neo4j
queries for the current update tag. It does not use fixtures or hard-coded
expected counts.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass

from neo4j import GraphDatabase

from cartography.config import Config
from cartography.sync import build_sync
from cartography.sync import run_with_config

NODE_LABELS = (
    "FlyOrganization",
    "FlyApp",
    "FlyMachine",
    "FlyMachineService",
    "FlyMachineServicePort",
    "FlyVolume",
    "FlySecret",
    "FlyCertificate",
)


@dataclass(frozen=True)
class RelCount:
    source: str
    rel: str
    target: str


RELATIONSHIPS = (
    RelCount("FlyOrganization", "RESOURCE", "FlyApp"),
    RelCount("FlyApp", "RESOURCE", "FlyMachine"),
    RelCount("FlyApp", "RESOURCE", "FlyMachineService"),
    RelCount("FlyApp", "RESOURCE", "FlyMachineServicePort"),
    RelCount("FlyApp", "RESOURCE", "FlyVolume"),
    RelCount("FlyApp", "RESOURCE", "FlySecret"),
    RelCount("FlyApp", "RESOURCE", "FlyCertificate"),
    RelCount("FlyMachine", "EXPOSE", "FlyMachineService"),
    RelCount("FlyMachineService", "EXPOSE", "FlyMachineServicePort"),
    RelCount("FlyMachine", "MOUNTS", "FlyVolume"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Fly.io intel module against a real Fly.io org.",
    )
    parser.add_argument(
        "--neo4j-uri",
        default=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        help="Neo4j URI. Defaults to NEO4J_URI or bolt://localhost:7687.",
    )
    parser.add_argument(
        "--neo4j-user",
        default=os.getenv("NEO4J_USER"),
        help="Neo4j username. Defaults to NEO4J_USER.",
    )
    parser.add_argument(
        "--neo4j-password",
        default=os.getenv("NEO4J_PASSWORD"),
        help="Neo4j password. Defaults to NEO4J_PASSWORD.",
    )
    parser.add_argument(
        "--flyio-token-env-var",
        default="FLY_API_TOKEN",
        help="Environment variable containing the Fly.io API token.",
    )
    parser.add_argument(
        "--flyio-org-slug",
        default=os.getenv("FLYIO_ORG_SLUG") or os.getenv("FLY_ORG"),
        help="Fly.io org slug. Defaults to FLYIO_ORG_SLUG or FLY_ORG.",
    )
    parser.add_argument(
        "--flyio-base-url",
        default=os.getenv("FLY_API_HOSTNAME", "https://api.machines.dev"),
        help="Fly.io Machines API base URL.",
    )
    parser.add_argument(
        "--update-tag",
        type=int,
        default=int(time.time()),
        help="Update tag to stamp and query. Defaults to the current Unix time.",
    )
    return parser.parse_args()


def require_config(args: argparse.Namespace) -> str:
    token = os.getenv(args.flyio_token_env_var)
    missing = []
    if not token:
        missing.append(args.flyio_token_env_var)
    if not args.flyio_org_slug:
        missing.append("FLYIO_ORG_SLUG or FLY_ORG")
    if missing:
        print(
            "Missing required configuration: " + ", ".join(missing),
            file=sys.stderr,
        )
        return ""
    return token


def build_config(args: argparse.Namespace, token: str) -> Config:
    return Config(
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password,
        update_tag=args.update_tag,
        flyio_token=token,
        flyio_org_slug=args.flyio_org_slug,
        flyio_base_url=args.flyio_base_url,
    )


def print_node_counts(session, update_tag: int) -> None:
    print(f"\nProduction graph node counts for update tag {update_tag}:")
    for label in NODE_LABELS:
        row = session.run(
            f"MATCH (n:{label}) WHERE n.lastupdated = $update_tag "
            "RETURN count(n) AS count",
            update_tag=update_tag,
        ).single()
        print(f"{label}: {row['count']}")


def print_relationship_counts(session, update_tag: int) -> None:
    print(f"\nProduction graph relationship counts for update tag {update_tag}:")
    for rel_count in RELATIONSHIPS:
        row = session.run(
            f"MATCH (:{rel_count.source})-[r:{rel_count.rel}]->"
            f"(:{rel_count.target}) "
            "WHERE r.lastupdated = $update_tag "
            "RETURN count(r) AS count",
            update_tag=update_tag,
        ).single()
        print(
            f"{rel_count.source}-[:{rel_count.rel}]->"
            f"{rel_count.target}: {row['count']}",
        )


def print_certificate_details(session, update_tag: int) -> None:
    print(f"\nFlyCertificate details for update tag {update_tag}:")
    rows = session.run(
        """
        MATCH (c:FlyCertificate)
        WHERE c.lastupdated = $update_tag
        RETURN c.hostname AS hostname, c.status AS status,
               c.configured AS configured,
               c.ownership_txt_configured AS ownership_txt_configured,
               c.acme_dns_configured AS acme_dns_configured
        ORDER BY hostname
        """,
        update_tag=update_tag,
    )
    count = 0
    for row in rows:
        count += 1
        print(
            "- "
            f"hostname={row['hostname']}, "
            f"status={row['status']}, "
            f"configured={row['configured']}, "
            f"ownership_txt_configured={row['ownership_txt_configured']}, "
            f"acme_dns_configured={row['acme_dns_configured']}",
        )
    if count == 0:
        print("- none returned by the Fly.io certificates API")


def print_secret_leak_check(session, update_tag: int) -> None:
    row = session.run(
        """
        MATCH (s:FlySecret)
        WHERE s.lastupdated = $update_tag
          AND any(k IN keys(s) WHERE toLower(k) CONTAINS 'value')
        RETURN count(s) AS count
        """,
        update_tag=update_tag,
    ).single()
    print("\nSecret value leak check:")
    print(f"FlySecret nodes with value-like property keys: {row['count']}")


def print_proof_counts(args: argparse.Namespace) -> None:
    auth = None
    if args.neo4j_user or args.neo4j_password:
        auth = (args.neo4j_user, args.neo4j_password)
    driver = GraphDatabase.driver(args.neo4j_uri, auth=auth)
    try:
        with driver.session() as session:
            print_node_counts(session, args.update_tag)
            print_relationship_counts(session, args.update_tag)
            print_certificate_details(session, args.update_tag)
            print_secret_leak_check(session, args.update_tag)
    finally:
        driver.close()


def main() -> int:
    args = parse_args()
    token = require_config(args)
    if not token:
        return 2

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
    )
    logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)

    print(
        "Running Fly.io production sync "
        f"for org '{args.flyio_org_slug}' with update tag '{args.update_tag}'.",
    )
    config = build_config(args, token)
    exit_code = run_with_config(build_sync("flyio"), config)
    if exit_code != 0:
        return exit_code

    print_proof_counts(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
