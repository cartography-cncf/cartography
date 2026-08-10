import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Literal

import neo4j
from cloudflare import APIError
from cloudflare import Cloudflare
from cloudflare import NotFoundError
from cloudflare import PermissionDeniedError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.cloudflare.r2bucket import CloudflareR2BucketSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Buckets per API page; the documented maximum is 1000 and the default is 20.
_PER_PAGE = 1000

Jurisdiction = Literal["default", "eu", "fedramp"]

# Every R2 call is scoped to a single jurisdiction through the
# `cf-r2-jurisdiction` header, which the SDK sets from its `jurisdiction`
# argument and defaults to `default`. Jurisdictions are separate namespaces, so
# one listing only reports the buckets of one of them and the same bucket name
# can exist in several. Each one is therefore listed on its own.
# See https://developers.cloudflare.com/r2/reference/data-location/
_DEFAULT_JURISDICTION: Jurisdiction = "default"
_JURISDICTIONS: tuple[Jurisdiction, ...] = ("default", "eu", "fedramp")


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Cloudflare,
    common_job_parameters: Dict[str, Any],
    account_id: str,
) -> None:
    buckets, listing_complete = get(client, account_id)
    if not buckets and not listing_complete:
        # No jurisdiction could be listed, so this run knows nothing about the
        # account's buckets. Skipping the load and the cleanup leaves the ones
        # from earlier runs in place instead of deleting the whole inventory on a
        # permission error.
        return
    exposure, exposure_complete = get_exposure(client, buckets, account_id)
    load_r2buckets(
        neo4j_session,
        transform_buckets(buckets, account_id, exposure),
        account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    if not listing_complete:
        # Cleanup deletes anything this run did not refresh, so running it while a
        # jurisdiction is unreadable would delete every bucket it holds.
        logger.warning(
            "Skipping the R2 cleanup for account %s: at least one jurisdiction could "
            "not be listed, and cleanup would delete the buckets it holds.",
            account_id,
        )
        return
    if not exposure_complete:
        # Same reasoning for the exposure: a partial read would drop the
        # HAS_R2_CUSTOM_DOMAIN edges of the buckets whose domains could not be
        # listed. The buckets are still ingested; only the deletion pass is held
        # back.
        logger.warning(
            "Skipping the R2 cleanup for account %s: at least one bucket's domains "
            "could not be read, and cleanup would delete the custom domain "
            "relationships this run knows nothing about.",
            account_id,
        )
        return
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: Cloudflare, account_id: str) -> tuple[List[Dict[str, Any]], bool]:
    """
    Return the account's R2 buckets across every jurisdiction, and whether all of
    them were listed.

    A token without the R2 scope must not abort the whole Cloudflare sync: the R2
    stage is skipped and the Workers and ruleset stages still run.
    """
    buckets: List[Dict[str, Any]] = []
    complete = True
    for jurisdiction in _JURISDICTIONS:
        jurisdiction_buckets = get_jurisdiction_buckets(
            client, account_id, jurisdiction
        )
        if jurisdiction_buckets is None:
            complete = False
            continue
        buckets.extend(jurisdiction_buckets)
    return buckets, complete


@timeit
def get_jurisdiction_buckets(
    client: Cloudflare, account_id: str, jurisdiction: Jurisdiction
) -> List[Dict[str, Any]] | None:
    """
    Return the buckets of one jurisdiction, or None if it could not be listed.

    The jurisdiction of the listing is recorded on every bucket: the API omits the
    field on the buckets of the default jurisdiction, and it is part of their
    identity.
    """
    # Unlike the other Cloudflare list endpoints, this one is not wrapped in an
    # SDK paginator and its response model drops the pagination cursor. Buckets
    # are ordered lexicographically by name, so `start_after` walks the pages.
    # See https://developers.cloudflare.com/api/resources/r2/subresources/buckets/methods/list/
    buckets: List[Dict[str, Any]] = []
    page_params: Dict[str, Any] = {
        "account_id": account_id,
        "per_page": _PER_PAGE,
        "jurisdiction": jurisdiction,
    }
    while True:
        try:
            page = client.r2.buckets.list(**page_params)
        except APIError as err:
            if jurisdiction != _DEFAULT_JURISDICTION and isinstance(
                err, (NotFoundError, PermissionDeniedError)
            ):
                # Jurisdictions other than the default one are granted on request,
                # so an account without the grant holds no bucket there. Reporting
                # that as a failed read would hold back the R2 cleanup of every
                # account that never asked for the grant.
                logger.debug(
                    "The %s R2 jurisdiction is not available to account %s; treating "
                    "it as holding no bucket.",
                    jurisdiction,
                    account_id,
                )
                return []
            logger.warning(
                "Unable to list the R2 buckets of account %s in the %s jurisdiction. "
                "Check that the token carries the Workers R2 Storage read scope.",
                account_id,
                jurisdiction,
                exc_info=True,
            )
            return None
        page_buckets = []
        for bucket in page.buckets or []:
            row = bucket.to_dict()
            row["jurisdiction"] = jurisdiction
            page_buckets.append(row)
        buckets.extend(page_buckets)
        if len(page_buckets) < _PER_PAGE:
            return buckets
        page_params["start_after"] = page_buckets[-1]["name"]


@timeit
def get_managed_domain(
    client: Cloudflare, account_id: str, bucket_name: str, jurisdiction: Jurisdiction
) -> Dict[str, Any] | None:
    """
    Return the bucket's managed r2.dev domain, or None if it could not be read.
    """
    try:
        return client.r2.buckets.domains.managed.list(
            bucket_name,
            account_id=account_id,
            jurisdiction=jurisdiction,
        ).to_dict()
    except APIError:
        # A token without the R2 domain scope must not abort the whole sync: the
        # bucket is still ingested, only its exposure stays unknown.
        logger.warning(
            "Unable to read the managed r2.dev domain of bucket %s in the %s "
            "jurisdiction of account %s; its public exposure will be incomplete.",
            bucket_name,
            jurisdiction,
            account_id,
            exc_info=True,
        )
        return None


@timeit
def get_custom_domains(
    client: Cloudflare, account_id: str, bucket_name: str, jurisdiction: Jurisdiction
) -> List[Dict[str, Any]] | None:
    """
    Return the bucket's custom domains, or None if they could not be read.
    """
    try:
        response = client.r2.buckets.domains.custom.list(
            bucket_name,
            account_id=account_id,
            jurisdiction=jurisdiction,
        )
    except APIError:
        logger.warning(
            "Unable to read the custom domains of bucket %s in the %s jurisdiction "
            "of account %s; its public exposure will be incomplete.",
            bucket_name,
            jurisdiction,
            account_id,
            exc_info=True,
        )
        return None
    # Like the bucket listing above, the SDK types `domains` as required but the
    # API omits it for a bucket without any custom domain.
    return [domain.to_dict() for domain in response.domains or []]


def bucket_id(account_id: str, jurisdiction: str, bucket_name: str) -> str:
    """
    Build the graph ID of a bucket.

    The R2 API does not assign bucket IDs, and a bucket name is only unique within
    one jurisdiction of one account, so both qualify the name.
    """
    return f"{account_id}/{jurisdiction}/{bucket_name}"


@timeit
def get_exposure(
    client: Cloudflare,
    buckets: List[Dict[str, Any]],
    account_id: str,
) -> tuple[Dict[str, Dict[str, Any]], bool]:
    """
    Resolve the internet exposure of each bucket from its managed and custom
    domains, keyed by bucket ID. R2 buckets are private by default: they are only
    reachable from the internet through their managed r2.dev domain or an enabled
    custom domain, neither of which the bucket listing reports.

    Also return whether every bucket's exposure was read in full. A bucket is only
    reported as private when *both* domain sources were read: either one on its
    own can hold the only enabled domain, so a partial read must not downgrade a
    publicly reachable bucket to `public=False`.
    """
    exposure: Dict[str, Dict[str, Any]] = {}
    all_complete = True
    for bucket in buckets:
        jurisdiction = bucket["jurisdiction"]
        managed_domain = get_managed_domain(
            client, account_id, bucket["name"], jurisdiction
        )
        custom_domains = get_custom_domains(
            client, account_id, bucket["name"], jurisdiction
        )
        complete = managed_domain is not None and custom_domains is not None
        all_complete = all_complete and complete

        public_domains: List[str] = []
        zone_ids: List[str] = []

        r2_dev_enabled: bool | None = None
        if managed_domain is not None:
            r2_dev_enabled = managed_domain["enabled"]
            if managed_domain["enabled"]:
                public_domains.append(managed_domain["domain"])

        if custom_domains is not None:
            for domain in custom_domains:
                if not domain["enabled"]:
                    continue
                public_domains.append(domain["domain"])
                if domain.get("zoneId"):
                    zone_ids.append(domain["zoneId"])

        exposure[bucket_id(account_id, jurisdiction, bucket["name"])] = {
            "public": bool(public_domains) if complete else None,
            # A partial hostname list reads as authoritative once it is in the
            # graph, so it is left unknown rather than published half-filled.
            "public_domains": public_domains if complete else None,
            "r2_dev_enabled": r2_dev_enabled,
            "zone_ids": zone_ids if custom_domains is not None else [],
        }
    return exposure, all_complete


def transform_buckets(
    buckets: List[Dict[str, Any]],
    account_id: str,
    exposure: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Qualify the bucket IDs with the account and the jurisdiction, and merge in the
    resolved exposure.
    """
    result: List[Dict[str, Any]] = []
    for bucket in buckets:
        transformed = bucket.copy()
        transformed["id"] = bucket_id(
            account_id, bucket["jurisdiction"], bucket["name"]
        )
        transformed.update(exposure.get(transformed["id"], {}))
        result.append(transformed)
    return result


def load_r2buckets(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CloudflareR2BucketSchema(),
        data,
        lastupdated=update_tag,
        account_id=account_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(CloudflareR2BucketSchema(), common_job_parameters).run(
        neo4j_session
    )
