import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.netlify.deploy import NetlifyDeploySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_netlify_deploys(
    neo4j_session: neo4j.Session,
    sites: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync the published deploy of every site.

    There is no get_* step: the published deploy is embedded in the site payload, so this costs
    no API request at all.
    """
    deploys = transform_netlify_deploys(sites)
    load_netlify_deploys(neo4j_session, deploys, account_id, update_tag)
    cleanup_netlify_deploys(neo4j_session, common_job_parameters)


def transform_netlify_deploys(sites: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Pull each site's published deploy out and flatten the nested secret-scan report.

    `skew_protection_token` is a bearer-equivalent secret and is dropped, as is the
    `secretsScanMatches` list, which contains the matched secret values themselves. Only the
    counts are kept, which is what a "this deploy shipped secrets" rule needs.
    """
    deploys = []
    for site in sites:
        deploy = site.get("published_deploy")
        if not deploy:
            # A site with no successful production deploy yet.
            continue
        report = deploy.get("deploy_validations_report") or {}
        scan = report.get("secret_scan_result") or {}
        matches = scan.get("secretsScanMatches") or []
        deploys.append(
            {
                **{k: v for k, v in deploy.items() if k != "skew_protection_token"},
                # The site payload nests the deploy, so fall back to the site id rather than
                # trusting the deploy to repeat it.
                "site_id": deploy.get("site_id") or site["id"],
                "secrets_scan_files_scanned": scan.get("scannedFilesCount"),
                "secrets_scan_matches_count": len(matches),
            },
        )
    return deploys


@timeit
def load_netlify_deploys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyDeploySchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_deploys(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(NetlifyDeploySchema(), common_job_parameters).run(
        neo4j_session,
    )
