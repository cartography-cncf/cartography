import logging
from datetime import datetime

import neo4j
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cartography.intel.cve import feed
from cartography.settings import check_module_settings
from cartography.settings import settings
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


def _retryable_session() -> Session:
    session = Session()
    retry_policy = Retry(
        total=8,
        connect=1,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    logger.info(f"Configured session with retry policy: {retry_policy}")
    return session


def _sync_year_archives(
    http_session: Session,
    neo4j_session: neo4j.Session,
    cve_api_key: str | None,
) -> None:
    existing_years = feed.get_cve_sync_metadata(neo4j_session)
    current_year = datetime.now().year
    logger.info(f"Syncing CVE data for year archives. Existing years: {existing_years}. Current year: {current_year}")
    for year in range(1999, current_year + 1):
        if year in existing_years:
            continue
        logger.info(f"Syncing CVE data for year {year}")
        cves = feed.get_published_cves_per_year(http_session, settings.cve.url, str(year), cve_api_key)
        feed_metadata = feed.transform_cve_feed(cves)
        feed.load_cve_feed(neo4j_session, [feed_metadata], settings.common.update_tag)
        published_cves = feed.transform_cves(cves)
        feed.load_cves(neo4j_session, published_cves, feed_metadata['FEED_ID'], settings.common.update_tag)
        merge_module_sync_metadata(
            neo4j_session,
            group_type='CVE',
            group_id=year,
            synced_type='year',
            update_tag=settings.common.update_tag,
            stat_handler=stat_handler,
        )


def _sync_modified_data(
    http_session: Session,
    neo4j_session: neo4j.Session,
    cve_api_key: str | None,
) -> None:
    logger.info("Syncing CVE data for modified data")
    last_modified_date = feed.get_last_modified_cve_date(neo4j_session)
    cves = feed.get_modified_cves(http_session, settings.cve.url, last_modified_date, cve_api_key)
    feed_metadata = feed.transform_cve_feed(cves)
    feed.load_cve_feed(neo4j_session, [feed_metadata], settings.common.update_tag)
    modified_cves = feed.transform_cves(cves)
    feed.load_cves(neo4j_session, modified_cves, feed_metadata['FEED_ID'], settings.common.update_tag)
    merge_module_sync_metadata(
        neo4j_session,
        group_type='CVE',
        group_id=feed_metadata['timestamp'][:4],
        synced_type='modified',
        update_tag=settings.common.update_tag,
        stat_handler=stat_handler,
    )


@timeit
def start_cve_ingestion(neo4j_session: neo4j.Session) -> None:
    """
    Perform ingestion of CVE data from NIST APIs.
    :param neo4j_session: Neo4J session for database interface
    :return: None
    """
    if not check_module_settings('CVE', ['enabled']):
        return
    if settings.cve.get('url', None) is None:
        settings.cve.update({'url': 'https://services.nvd.nist.gov/rest/json/cves/2.0/'})
    cve_api_key: str | None = settings.cve.get('api_key', None)
    with _retryable_session() as http_session:
        _sync_year_archives(http_session, neo4j_session=neo4j_session, cve_api_key=cve_api_key)
        _sync_modified_data(http_session, neo4j_session=neo4j_session, cve_api_key=cve_api_key)
        # CVEs are never deleted, so we don't need to run a cleanup job
