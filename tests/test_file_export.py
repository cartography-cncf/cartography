import gzip
import json
import os
import tempfile
from dataclasses import dataclass

from cartography.client.core.tx import load
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.sinks import file_export as file_export_sink


@dataclass(frozen=True)
class _DummyNodeProps(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    vpcId: PropertyRef = PropertyRef("vpcId")
    subnet_id: PropertyRef = PropertyRef("subnet_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _DummySubRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _DummySubRel(CartographyRelSchema):
    target_node_label: str = "Tenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("TENANT_ID", set_in_kwargs=True),
    })
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: _DummySubRelProps = _DummySubRelProps()


@dataclass(frozen=True)
class _DummyOtherRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _DummyOtherRel(CartographyRelSchema):
    target_node_label: str = "EC2Subnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("subnet_id"),
    })
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_SUBNET"
    properties: _DummyOtherRelProps = _DummyOtherRelProps()


@dataclass(frozen=True)
class _DummySchema(CartographyNodeSchema):
    label: str = "EC2Instance"
    properties: _DummyNodeProps = _DummyNodeProps()
    sub_resource_relationship: _DummySubRel = _DummySubRel()
    other_relationships: OtherRelationships = OtherRelationships([
        _DummyOtherRel(),
    ])
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AWS"])


def _read_ndjson_gz(path: str):
    with gzip.open(path, mode="rt", encoding="utf-8") as fh:  # type: ignore
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def test_file_export_basic_vertex_and_edges():
    with tempfile.TemporaryDirectory() as td:
        out_path = os.path.join(td, "graph.ndjson.gz")
        file_export_sink.enable(out_path)
        file_export_sink.set_no_neo4j_write(True)

        data = [
            {
                "id": "i/i-abc",
                "vpcId": "vpc-1",
                "subnet_id": "subnet-1",
            },
        ]

        # Export-only run; we pass a dummy session since no Neo4j writes will occur
        load(  # type: ignore[arg-type]
            neo4j_session=None,  # not used when no_neo4j_write=True
            node_schema=_DummySchema(),
            dict_list=data,
            lastupdated=1700000000,
            TENANT_ID="t1",
        )

        file_export_sink.disable()

        records = list(_read_ndjson_gz(out_path))
        assert records, "export produced no records"
        vertices = [r for r in records if r.get("record_type") == "vertex"]
        edges = [r for r in records if r.get("record_type") == "edge"]

        assert len(vertices) == 1
        v = vertices[0]
        assert v["uid"] == "i/i-abc"
        assert "EC2Instance" in v["labels"]
        assert "AWS" in v["labels"]
        assert v["props"]["vpcId"] == "vpc-1"
        assert v["_sub_resource_label"] == "Tenant"
        assert v["_sub_resource_id"] == "t1"

        # Expect 2 edges: RESOURCE and IN_SUBNET
        rel_types = sorted(e["rel_type"] for e in edges)
        assert rel_types == ["IN_SUBNET", "RESOURCE"]

        # Validate one specific edge
        in_subnet = next(e for e in edges if e["rel_type"] == "IN_SUBNET")
        assert in_subnet["from_uid"] == "i/i-abc"
        assert in_subnet["to_uid"] == "subnet-1"

