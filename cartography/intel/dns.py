import logging
from typing import Any

import dns.rdatatype
import dns.resolver

from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def resolve_a_record(fqdn: str) -> list[str]:
    """
    Resolve an FQDN to the IP addresses of its A record.

    :param fqdn: the FQDN to resolve
    :return: the resolved IP addresses
    """
    fqdn_data = get_dns_resolution_by_fqdn(fqdn)
    record_type = get_dns_record_type(fqdn_data)
    if record_type != "A":
        raise NotImplementedError(
            f"Ingestion of DNS record type '{record_type}' by FQDN has not been implemented. "
            f"Failed to ingest '{fqdn}'.",
        )
    return [str(result) for result in fqdn_data]


@timeit
def get_dns_resolution_by_fqdn(fqdn: str) -> Any:
    """
    Get dns resolution data for fqdn

    :param fqdn: record to query
    :return: DNS resolution Answer as dns.resolver.Answer
    """
    return dns.resolver.query(fqdn)


def get_dns_record_type(record_data: Any) -> str:
    """
    Get DNS record type from answer

    :param record_data: dns resolution data
    :return: record type (A,CNAME, ...)
    """
    return dns.rdatatype.to_text(record_data.rdtype)
