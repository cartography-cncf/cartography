import logging
from string import Template
from typing import Any
from typing import List
from typing import Optional

import dns.rdatatype
import dns.resolver
import neo4j

from cartography.client.core.tx import run_write_query
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def ingest_dns_record_by_fqdn(
    neo4j_session: neo4j.Session,
    update_tag: int,
    fqdn: str,
    points_to_record: str,
    record_label: str,
    dns_node_additional_label: Optional[str] = None,
) -> None:
    """
    Creates a :DNSRecord node in the graph from the given FQDN and performs DNS resolution to connect it to its
    associated IP addresses.
    This also connects the new :DNSRecord to the node with ID `points_to_record` of label `record_label`.
    Finally, the :DNSRecord node is also labeled with a specified `dns_node_additional_label`, e.g. `AWSDNSRecord`.

    This results the following new nodes and relationships:
    (:DNSRecord:$`dns_node_additional_label`)-[:DNS_POINTS_TO]->(:Ip)
    (:DNSRecord:$`dns_node_additional_label`)-[:DNS_POINTS_TO]->(:$`record_label`)

    Example usage in ElasticSearch sync:
    ingest_dns_record_by_fqdn(neo4j_session, aws_update_tag, fqdn, node_id_of_the_ESDomain,
                              dns_node_additional_label="ESDomain")

    :param neo4j_session: Neo4j session object
    :param update_tag: Update tag to set the node with and childs
    :param fqdn: the fqdn record to add
    :param points_to_record: parent record to set DNS_POINTS_TO relationship to. Can be None
    :param record_label: the label of the node to attach to a DNS record, e.g. "ESDomain"
    :param dns_node_additional_label: The specific label of the DNSRecord, e.g. AWSDNSRecord.
    :return: the graph node id for the new/merged record
    """
    fqdn_data = get_dns_resolution_by_fqdn(fqdn)
    record_type = get_dns_record_type(fqdn_data)

    if record_type == "A":
        ip_list = []
        for result in fqdn_data:
            ip = str(result)
            ip_list.append(ip)

        value = ",".join(ip_list)
        record_id = ingest_dns_record(
            neo4j_session,
            fqdn,
            value,
            record_type,
            update_tag,
            points_to_record,
            record_label,
            dns_node_additional_label,  # type: ignore
        )
        _link_ip_to_A_record(neo4j_session, update_tag, ip_list, record_id)

        return record_id  # type: ignore
    else:
        raise NotImplementedError(
            "Ingestion of DNS record type '{}' by FQDN has not been implemented. Failed to ingest '{}'.".format(
                record_type,
                fqdn,
            ),
        )


@timeit
def _link_ip_to_A_record(
    neo4j_session: neo4j.Session,
    update_tag: int,
    ip_list: List[str],
    parent_record: str,
) -> None:
    """
    Link A record to to its IP

    :param neo4j_session: Neo4j session object
    :param update_tag: Update tag to set the node with and childs
    :param ip_list: List of IP to link
    :param parent_record: parent record to set DNS_POINTS_TO relationship to
    """
    ingest = """
    MATCH (parent:DNSRecord{id: $ParentId})
    WITH parent
    UNWIND $IP_LIST as current_ip
    MERGE (ip_node:Ip{id: current_ip})
    ON CREATE SET ip_node.firstseen = timestamp(), ip_node.ip = current_ip
    SET ip_node.lastupdated = $update_tag
    WITH parent, ip_node
    MERGE (parent)-[r:DNS_POINTS_TO]->(ip_node)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    run_write_query(
        neo4j_session,
        ingest,
        ParentId=parent_record,
        IP_LIST=ip_list,
        update_tag=update_tag,
    )


@timeit
def ingest_dns_record(
    neo4j_session: neo4j.Session,
    name: neo4j.Session,
    value: str,
    type: str,
    update_tag: int,
    points_to_record: str,
    record_label: str,
    dns_node_additional_label: str,
) -> str:
    """
    Ingest a new DNS record

    :param neo4j_session: Neo4j session object
    :param name: record name
    :param value: record value
    :param type: record type
    :param update_tag: Update tag to set the node with and childs
    :param points_to_record: parent record to set DNS_POINTS_TO relationship to. Can be None
    :param record_label: the label of the node to attach to a DNS record
    :param dns_node_additional_label: The specific label of the DNSRecord, e.g. AWSDNSRecord.
    :return: the intel graph node id for the new/merged record
    """
    template = Template(
        """
    MERGE (record:DNSRecord:$dns_node_additional_label{id: $Id})
    ON CREATE SET record.firstseen = timestamp(), record.name = $Name, record.type = $Type
    SET record.lastupdated = $update_tag, record.value = $Value
    WITH record
    MATCH (n:$record_label{id: $PointsToId})
    MERGE (record)-[r:DNS_POINTS_TO]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """,
    )

    record_id = f"{name}+{type}"

    run_write_query(
        neo4j_session,
        template.safe_substitute(
            record_label=record_label,
            dns_node_additional_label=dns_node_additional_label,
        ),
        Id=record_id,
        Name=name,
        Type=type,
        Value=value,
        PointsToId=points_to_record,
        update_tag=update_tag,
    )

    return record_id


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
