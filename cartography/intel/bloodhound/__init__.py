"""Import Active Directory data from BloodHound CE collector output.

Cartography does not collect AD data itself. It reads the JSON that SharpHound
CE (or another BloodHound CE v6 collector) already produced, from a local path
or an object-store prefix holding zip archives or loose JSON files.

The import runs in three phases:

1. Validate: stream every file and reject the whole collection if any file is
   truncated, malformed or in an unsupported format. Nothing is written.
2. Load: write nodes, then edges, in batches.
3. Clean up: remove nodes and edges of each imported domain that this import did
   not refresh. Only domains in the import are touched, and an edge kind is only
   cleaned up when its collection method ran, so a partial SharpHound run never
   deletes data it did not collect. Host edges of computers SharpHound could not
   reach are kept.

Edges may reference principals outside the import, such as a group from a
trusted domain named in an ACE. Those principals get placeholder nodes with
``collected`` set to false, which are removed once nothing references them.

A failure in any phase raises before cleanup, which leaves the previous import
in place.
"""

import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import run_write_query
from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.intel.bloodhound.collection import BloodHoundImportError
from cartography.intel.bloodhound.collection import open_collection
from cartography.intel.bloodhound.parser import ACL_RIGHTS
from cartography.intel.bloodhound.parser import ADD_KEY_CREDENTIAL_LINK
from cartography.intel.bloodhound.parser import ADD_MEMBER
from cartography.intel.bloodhound.parser import ADD_SELF
from cartography.intel.bloodhound.parser import ADMIN_TO
from cartography.intel.bloodhound.parser import ALL_EXTENDED_RIGHTS
from cartography.intel.bloodhound.parser import ALLOWED_TO_ACT
from cartography.intel.bloodhound.parser import ALLOWED_TO_DELEGATE
from cartography.intel.bloodhound.parser import CAN_PS_REMOTE
from cartography.intel.bloodhound.parser import CAN_RDP
from cartography.intel.bloodhound.parser import CollectionMethod
from cartography.intel.bloodhound.parser import COMPUTERS
from cartography.intel.bloodhound.parser import CONTAINERS
from cartography.intel.bloodhound.parser import CONTAINS
from cartography.intel.bloodhound.parser import CROSS_FOREST_TRUST
from cartography.intel.bloodhound.parser import DC_SYNC
from cartography.intel.bloodhound.parser import DOMAINS
from cartography.intel.bloodhound.parser import FORCE_CHANGE_PASSWORD
from cartography.intel.bloodhound.parser import GENERIC_ALL
from cartography.intel.bloodhound.parser import GENERIC_WRITE
from cartography.intel.bloodhound.parser import GP_LINK
from cartography.intel.bloodhound.parser import GPOS
from cartography.intel.bloodhound.parser import GROUPS
from cartography.intel.bloodhound.parser import HAS_SESSION
from cartography.intel.bloodhound.parser import HAS_SID_HISTORY
from cartography.intel.bloodhound.parser import is_deleted
from cartography.intel.bloodhound.parser import iter_edges
from cartography.intel.bloodhound.parser import iter_objects
from cartography.intel.bloodhound.parser import MEMBER_OF
from cartography.intel.bloodhound.parser import object_domain_sid
from cartography.intel.bloodhound.parser import OUS
from cartography.intel.bloodhound.parser import OWNS
from cartography.intel.bloodhound.parser import placeholder_domain
from cartography.intel.bloodhound.parser import PLACEHOLDER_LABELS
from cartography.intel.bloodhound.parser import READ_GMSA_PASSWORD
from cartography.intel.bloodhound.parser import READ_LAPS_PASSWORD
from cartography.intel.bloodhound.parser import SAME_FOREST_TRUST
from cartography.intel.bloodhound.parser import transform_node
from cartography.intel.bloodhound.parser import USERS
from cartography.intel.bloodhound.parser import validate_collection
from cartography.intel.bloodhound.parser import ValidatedCollection
from cartography.intel.bloodhound.parser import WRITE_DACL
from cartography.intel.bloodhound.parser import WRITE_OWNER
from cartography.intel.bloodhound.parser import WRITE_SPN
from cartography.intel.common.object_store import ReportReader
from cartography.intel.common.report_reader_builder import (
    build_report_reader_for_source,
)
from cartography.intel.common.report_source import parse_report_source
from cartography.models.bloodhound.acl import ADAddKeyCredentialLinkMatchLink
from cartography.models.bloodhound.acl import ADAddMemberMatchLink
from cartography.models.bloodhound.acl import ADAddSelfMatchLink
from cartography.models.bloodhound.acl import ADAllExtendedRightsMatchLink
from cartography.models.bloodhound.acl import ADDCSyncMatchLink
from cartography.models.bloodhound.acl import ADForceChangePasswordMatchLink
from cartography.models.bloodhound.acl import ADGenericAllMatchLink
from cartography.models.bloodhound.acl import ADGenericWriteMatchLink
from cartography.models.bloodhound.acl import ADOwnsMatchLink
from cartography.models.bloodhound.acl import ADReadGmsaPasswordMatchLink
from cartography.models.bloodhound.acl import ADReadLapsPasswordMatchLink
from cartography.models.bloodhound.acl import ADWriteDaclMatchLink
from cartography.models.bloodhound.acl import ADWriteOwnerMatchLink
from cartography.models.bloodhound.acl import ADWriteSpnMatchLink
from cartography.models.bloodhound.computer import ADComputerSchema
from cartography.models.bloodhound.container import ADContainerSchema
from cartography.models.bloodhound.delegation import ADAllowedToActMatchLink
from cartography.models.bloodhound.delegation import ADAllowedToDelegateMatchLink
from cartography.models.bloodhound.delegation import ADHasSidHistoryMatchLink
from cartography.models.bloodhound.domain import ADDomainSchema
from cartography.models.bloodhound.gpo import ADGPOSchema
from cartography.models.bloodhound.group import ADGroupSchema
from cartography.models.bloodhound.host import ADAdminToMatchLink
from cartography.models.bloodhound.host import ADCanPsRemoteMatchLink
from cartography.models.bloodhound.host import ADCanRdpMatchLink
from cartography.models.bloodhound.host import ADHasSessionMatchLink
from cartography.models.bloodhound.ou import ADOUSchema
from cartography.models.bloodhound.relationships import ADContainsMatchLink
from cartography.models.bloodhound.relationships import ADCrossForestTrustMatchLink
from cartography.models.bloodhound.relationships import ADGPLinkMatchLink
from cartography.models.bloodhound.relationships import ADMemberOfMatchLink
from cartography.models.bloodhound.relationships import ADSameForestTrustMatchLink
from cartography.models.bloodhound.user import ADUserSchema
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

__all__ = [
    "BloodHoundImportError",
    "start_bloodhound_ingestion",
    "sync",
]

_BATCH_SIZE = 10_000
_SUB_RESOURCE_LABEL = "ADDomain"

_NODE_SCHEMAS: dict[str, CartographyNodeSchema] = {
    USERS: ADUserSchema(),
    GROUPS: ADGroupSchema(),
    COMPUTERS: ADComputerSchema(),
    OUS: ADOUSchema(),
    GPOS: ADGPOSchema(),
    CONTAINERS: ADContainerSchema(),
}


@dataclass(frozen=True)
class EdgeKind:
    # The BloodHound CE edge this relationship imports. The relationship type is
    # this name in UPPER_SNAKE, for example GPLink -> GP_LINK.
    bloodhound_name: str
    schema: CartographyRelSchema
    # The edge kind is only cleaned up for a domain when one of these
    # collection methods ran for it...
    methods: CollectionMethod
    # ...and the import holds that domain's data for every type that declares
    # this edge kind, so no edge is removed because its input was left out.
    source_types: tuple[str, ...]


EDGE_KINDS: dict[str, EdgeKind] = {
    MEMBER_OF: EdgeKind(
        "MemberOf",
        ADMemberOfMatchLink(),
        CollectionMethod.GROUP,
        (USERS, GROUPS, COMPUTERS),
    ),
    CONTAINS: EdgeKind(
        "Contains",
        ADContainsMatchLink(),
        CollectionMethod.CONTAINER,
        (DOMAINS, USERS, GROUPS, COMPUTERS, OUS, CONTAINERS),
    ),
    GP_LINK: EdgeKind(
        "GPLink",
        ADGPLinkMatchLink(),
        CollectionMethod.CONTAINER,
        (DOMAINS, OUS),
    ),
    SAME_FOREST_TRUST: EdgeKind(
        "SameForestTrust",
        ADSameForestTrustMatchLink(),
        CollectionMethod.TRUSTS,
        (DOMAINS,),
    ),
    CROSS_FOREST_TRUST: EdgeKind(
        "CrossForestTrust",
        ADCrossForestTrustMatchLink(),
        CollectionMethod.TRUSTS,
        (DOMAINS,),
    ),
}

# Every object type carries ACEs, so a permission edge can come from any file.
_ACL_SOURCE_TYPES = (DOMAINS, USERS, GROUPS, COMPUTERS, OUS, GPOS, CONTAINERS)
_ACL_SCHEMAS: dict[str, CartographyRelSchema] = {
    GENERIC_ALL: ADGenericAllMatchLink(),
    GENERIC_WRITE: ADGenericWriteMatchLink(),
    WRITE_DACL: ADWriteDaclMatchLink(),
    WRITE_OWNER: ADWriteOwnerMatchLink(),
    OWNS: ADOwnsMatchLink(),
    FORCE_CHANGE_PASSWORD: ADForceChangePasswordMatchLink(),
    ADD_MEMBER: ADAddMemberMatchLink(),
    ALL_EXTENDED_RIGHTS: ADAllExtendedRightsMatchLink(),
    ADD_KEY_CREDENTIAL_LINK: ADAddKeyCredentialLinkMatchLink(),
    READ_LAPS_PASSWORD: ADReadLapsPasswordMatchLink(),
    READ_GMSA_PASSWORD: ADReadGmsaPasswordMatchLink(),
    ADD_SELF: ADAddSelfMatchLink(),
    WRITE_SPN: ADWriteSpnMatchLink(),
}
EDGE_KINDS.update(
    {
        kind: EdgeKind(
            right, _ACL_SCHEMAS[kind], CollectionMethod.ACL, _ACL_SOURCE_TYPES
        )
        for right, kind in ACL_RIGHTS.items()
    },
)

# Local group edges come from computers and from GPOs linked to domains and OUs.
_LOCAL_GROUP_SOURCE_TYPES = (DOMAINS, COMPUTERS, OUS)
EDGE_KINDS.update(
    {
        DC_SYNC: EdgeKind(
            "DCSync",
            ADDCSyncMatchLink(),
            CollectionMethod.ACL,
            (DOMAINS,),
        ),
        ADMIN_TO: EdgeKind(
            "AdminTo",
            ADAdminToMatchLink(),
            CollectionMethod.LOCAL_ADMIN | CollectionMethod.GPO_LOCAL_GROUP,
            _LOCAL_GROUP_SOURCE_TYPES,
        ),
        CAN_RDP: EdgeKind(
            "CanRDP",
            ADCanRdpMatchLink(),
            CollectionMethod.RDP | CollectionMethod.GPO_LOCAL_GROUP,
            _LOCAL_GROUP_SOURCE_TYPES,
        ),
        CAN_PS_REMOTE: EdgeKind(
            "CanPSRemote",
            ADCanPsRemoteMatchLink(),
            CollectionMethod.PS_REMOTE | CollectionMethod.GPO_LOCAL_GROUP,
            _LOCAL_GROUP_SOURCE_TYPES,
        ),
        HAS_SESSION: EdgeKind(
            "HasSession",
            ADHasSessionMatchLink(),
            CollectionMethod.SESSION | CollectionMethod.LOGGED_ON,
            (COMPUTERS,),
        ),
        ALLOWED_TO_DELEGATE: EdgeKind(
            "AllowedToDelegate",
            ADAllowedToDelegateMatchLink(),
            CollectionMethod.OBJECT_PROPS,
            (USERS, COMPUTERS),
        ),
        ALLOWED_TO_ACT: EdgeKind(
            "AllowedToAct",
            ADAllowedToActMatchLink(),
            CollectionMethod.OBJECT_PROPS,
            (COMPUTERS,),
        ),
        HAS_SID_HISTORY: EdgeKind(
            "HasSIDHistory",
            ADHasSidHistoryMatchLink(),
            CollectionMethod.OBJECT_PROPS,
            (USERS, COMPUTERS),
        ),
    },
)

# Creates a placeholder for each principal not in the graph, and refreshes the
# placeholders that already exist. Real objects are never touched.
_PLACEHOLDER_QUERY = """
UNWIND $rows AS row
OPTIONAL MATCH (existing:ADObject {id: row.id})
FOREACH (_ IN CASE WHEN existing IS NULL THEN [1] ELSE [] END |
    CREATE (n:ADObject:%s {id: row.id})
    SET n.objectid = row.id,
        n.collected = false,
        n.domainsid = row.domainsid,
        n.domain = row.domain,
        n.firstseen = timestamp(),
        n.lastupdated = $UPDATE_TAG
)
FOREACH (_ IN CASE WHEN existing.collected = false THEN [1] ELSE [] END |
    SET existing.lastupdated = $UPDATE_TAG
)
"""

# Keeps the host edges of computers whose host data was not collected by
# marking them as refreshed before cleanup runs.
_KEEP_HOST_EDGES_QUERY = """
UNWIND $computer_ids AS computer_id
MATCH (c:ADComputer {id: computer_id})
MATCH (c)%s
WHERE r._sub_resource_label = $sub_resource_label
    AND r._sub_resource_id = $sub_resource_id
SET r.lastupdated = $UPDATE_TAG
"""
_HOST_EDGE_PATTERNS = {
    ADMIN_TO: "<-[r:ADMIN_TO]-()",
    CAN_RDP: "<-[r:CAN_RDP]-()",
    CAN_PS_REMOTE: "<-[r:CAN_PS_REMOTE]-()",
    HAS_SESSION: "-[r:HAS_SESSION]->()",
}

# Removes placeholders that no relationship references any more.
_ORPHAN_PLACEHOLDER_QUERY = """
MATCH (n:ADObject)
WHERE n.collected = false
    AND NOT n:ADDomain
    AND n.lastupdated <> $UPDATE_TAG
    AND NOT (n)--()
DELETE n
"""


class _Batcher:
    """Buffers rows per (kind, domain) and flushes them in bounded batches."""

    def __init__(self, flush: Callable[[str, str, list[dict[str, Any]]], None]):
        self._flush = flush
        self._rows: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        self._size = 0

    def add(self, kind: str, domain_sid: str, row: dict[str, Any]) -> None:
        self._rows[(kind, domain_sid)].append(row)
        self._size += 1
        if self._size >= _BATCH_SIZE:
            self.flush()

    def flush(self) -> None:
        for (kind, domain_sid), rows in self._rows.items():
            self._flush(kind, domain_sid, rows)
        self._rows.clear()
        self._size = 0


@timeit
def load_domains(
    neo4j_session: neo4j.Session,
    collection: ValidatedCollection,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ADDomainSchema(),
        list(collection.domain_rows.values()),
        lastupdated=update_tag,
    )
    load_trust_target_placeholders(neo4j_session, collection, update_tag)


def load_trust_target_placeholders(
    neo4j_session: neo4j.Session,
    collection: ValidatedCollection,
    update_tag: int,
) -> None:
    """Create placeholder domains for trust targets that are not in the graph yet.

    Existing domains are left alone so a placeholder never overwrites the
    properties of a domain imported earlier.
    """
    candidates = sorted(set(collection.trust_targets) - set(collection.domains))
    if not candidates:
        return
    existing = {
        record["id"]
        for record in neo4j_session.run(
            "MATCH (d:ADDomain) WHERE d.id IN $ids RETURN d.id AS id",
            ids=candidates,
        )
    }
    placeholders = [
        {
            "id": domain_sid,
            "name": collection.trust_targets[domain_sid],
            "domainsid": domain_sid,
            "collected": False,
        }
        for domain_sid in candidates
        if domain_sid not in existing
    ]
    if placeholders:
        logger.info(
            "Creating %d placeholder AD domain(s) for trust targets outside the import.",
            len(placeholders),
        )
        load(neo4j_session, ADDomainSchema(), placeholders, lastupdated=update_tag)


@timeit
def load_objects(
    neo4j_session: neo4j.Session,
    collection: ValidatedCollection,
    update_tag: int,
) -> None:
    def flush(data_type: str, domain_sid: str, rows: list[dict[str, Any]]) -> None:
        load(
            neo4j_session,
            _NODE_SCHEMAS[data_type],
            rows,
            lastupdated=update_tag,
            DOMAIN_SID=domain_sid,
        )

    batcher = _Batcher(flush)
    for validated in collection.files_of(*_NODE_SCHEMAS):
        logger.info(
            "Loading BloodHound %s from %s",
            validated.data_type,
            validated.provenance.source_uri,
        )
        for obj in iter_objects(validated.file):
            if is_deleted(obj):
                continue
            batcher.add(
                validated.data_type,
                object_domain_sid(validated.data_type, obj),
                transform_node(validated.data_type, obj, validated.provenance),
            )
    batcher.flush()


@timeit
def load_principal_placeholders(
    neo4j_session: neo4j.Session,
    collection: ValidatedCollection,
    update_tag: int,
) -> None:
    """Create placeholder nodes for principals that edges reference but no import holds.

    Runs after the objects are loaded, so only principals absent from the graph
    get a placeholder. A later import that holds the principal fills in the same
    node and sets ``collected`` to true.
    """
    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for principal_id, label in collection.referenced_principals.items():
        by_label[label].append({"id": principal_id, **placeholder_domain(principal_id)})
    for label in sorted(by_label):
        assert label in PLACEHOLDER_LABELS.values()
        rows = by_label[label]
        for start in range(0, len(rows), _BATCH_SIZE):
            run_write_query(
                neo4j_session,
                _PLACEHOLDER_QUERY % label,
                rows=rows[start : start + _BATCH_SIZE],
                UPDATE_TAG=update_tag,
            )


@timeit
def load_edges(
    neo4j_session: neo4j.Session,
    collection: ValidatedCollection,
    update_tag: int,
) -> None:
    def flush(kind: str, domain_sid: str, rows: list[dict[str, Any]]) -> None:
        load_matchlinks(
            neo4j_session,
            EDGE_KINDS[kind].schema,
            rows,
            lastupdated=update_tag,
            _sub_resource_label=_SUB_RESOURCE_LABEL,
            _sub_resource_id=domain_sid,
        )

    batcher = _Batcher(flush)
    for validated in collection.files:
        logger.info(
            "Loading BloodHound relationships from %s",
            validated.provenance.source_uri,
        )
        for obj in iter_objects(validated.file):
            if is_deleted(obj):
                continue
            domain_sid = object_domain_sid(validated.data_type, obj)
            for kind, row in iter_edges(validated.data_type, obj, validated.provenance):
                batcher.add(kind, domain_sid, row)
    batcher.flush()


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    collection: ValidatedCollection,
    update_tag: int,
) -> None:
    for domain_sid in sorted(collection.domains):
        parameters = {"UPDATE_TAG": update_tag, "DOMAIN_SID": domain_sid}
        for data_type, schema in _NODE_SCHEMAS.items():
            if (data_type, domain_sid) not in collection.collected_types:
                logger.info(
                    "Keeping existing %s of %s: none in this import.",
                    data_type,
                    domain_sid,
                )
                continue
            GraphJob.from_node_schema(schema, parameters).run(neo4j_session)
        for kind, edge_kind in EDGE_KINDS.items():
            missing_types = [
                data_type
                for data_type in edge_kind.source_types
                if (data_type, domain_sid) not in collection.collected_types
            ]
            if missing_types or not collection.was_collected(
                domain_sid,
                edge_kind.methods,
            ):
                logger.info(
                    "Keeping existing %s edges of %s: not fully collected in this import.",
                    kind,
                    domain_sid,
                )
                continue
            keep_host_edges(neo4j_session, collection, kind, domain_sid, update_tag)
            GraphJob.from_matchlink(
                edge_kind.schema,
                _SUB_RESOURCE_LABEL,
                domain_sid,
                update_tag,
            ).run(neo4j_session)
    run_write_query(neo4j_session, _ORPHAN_PLACEHOLDER_QUERY, UPDATE_TAG=update_tag)


def keep_host_edges(
    neo4j_session: neo4j.Session,
    collection: ValidatedCollection,
    kind: str,
    domain_sid: str,
    update_tag: int,
) -> None:
    computer_ids = sorted(collection.uncollected_hosts.get((kind, domain_sid), ()))
    if not computer_ids:
        return
    logger.info(
        "Keeping existing %s edges of %d computer(s) in %s: SharpHound did not "
        "collect their host data.",
        kind,
        len(computer_ids),
        domain_sid,
    )
    for start in range(0, len(computer_ids), _BATCH_SIZE):
        run_write_query(
            neo4j_session,
            _KEEP_HOST_EDGES_QUERY % _HOST_EDGE_PATTERNS[kind],
            computer_ids=computer_ids[start : start + _BATCH_SIZE],
            sub_resource_label=_SUB_RESOURCE_LABEL,
            sub_resource_id=domain_sid,
            UPDATE_TAG=update_tag,
        )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    reader: ReportReader,
    update_tag: int,
    collected_at: str | None = None,
) -> None:
    """Import one BloodHound collection.

    Raises BloodHoundImportError, without writing anything, when the collection
    is unreadable or incomplete.
    """
    logger.info("Importing BloodHound collection from %s", reader.source_uri)
    with open_collection(reader) as files:
        collection = validate_collection(files, collected_at)
        logger.info(
            "Validated BloodHound collection: %d file(s), %d domain(s).",
            len(collection.files),
            len(collection.domains),
        )
        load_domains(neo4j_session, collection, update_tag)
        load_objects(neo4j_session, collection, update_tag)
        load_principal_placeholders(neo4j_session, collection, update_tag)
        load_edges(neo4j_session, collection, update_tag)
        cleanup(neo4j_session, collection, update_tag)


@timeit
def start_bloodhound_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.bloodhound_source:
        logger.info("BloodHound source not configured - skipping module.")
        return

    source = parse_report_source(config.bloodhound_source)
    with build_report_reader_for_source(source, config=config) as reader:
        sync(
            neo4j_session,
            reader,
            config.update_tag,
            collected_at=config.bloodhound_collected_at,
        )
