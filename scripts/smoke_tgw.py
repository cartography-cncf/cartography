#!/usr/bin/env python3
"""
Smoke test script: sync Transit Gateways and Transit Gateway Route Tables into a local Neo4j.

Usage (from repo root, with .venv activated):
  python3 scripts/smoke_tgw.py --regions us-east-1

Notes:
- Requires boto3 and neo4j Python packages available in the active Python environment.
- Requires a local Neo4j instance running on bolt://localhost:7687 (this script uses auth=None).
- The script performs read-only AWS Describe calls and writes nodes to Neo4j.
"""
import argparse
import time
import boto3
from neo4j import GraphDatabase

from cartography.intel.aws.ec2 import tgw, tgw_route_tables


def main(regions: list[str]):
    boto3_session = boto3.Session()
    acct = boto3_session.client("sts").get_caller_identity()["Account"]
    print("AWS account:", acct)

    driver = GraphDatabase.driver("bolt://localhost:7687", auth=None)
    try:
        with driver.session() as session:
            update_tag = int(time.time())
            common = {"AWS_ID": acct, "UPDATE_TAG": update_tag}

            print("Sync TGWs...")
            tgw.sync_transit_gateways(
                session,
                boto3_session,
                regions=regions,
                current_aws_account_id=acct,
                update_tag=update_tag,
                common_job_parameters=common,
            )

            print("Sync TGW route tables...")
            tgw_route_tables.sync_transit_gateway_route_tables(
                session,
                boto3_session,
                regions=regions,
                current_aws_account_id=acct,
                update_tag=update_tag,
                common_job_parameters=common,
            )

    finally:
        driver.close()

    print("Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smoke test: sync TGW and TGW route tables into local Neo4j")
    parser.add_argument("--regions", nargs="+", default=["us-east-1"], help="Regions to sync")
    args = parser.parse_args()
    main(args.regions)
