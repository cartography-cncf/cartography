from cartography.models.ontology.mapping.data.dnsrecords import (
    DNSRECORDS_ONTOLOGY_MAPPING,
)


def test_gcp_recordset_does_not_map_list_field_to_scalar_ont_value():
    # GCPRecordSet.data is list-valued; mapping it to _ont_value makes the scalar
    # toString(_ont_value) in ontology_dnsrecords_linking.json raise CypherTypeError
    # on list values (e.g. a TXT record ["1.0.0"]). GCP is linked via UNWIND dns.data
    # instead, so _ont_value must stay unset for GCPRecordSet.
    gcp_nodes = DNSRECORDS_ONTOLOGY_MAPPING["gcp"].nodes
    mapped_ontology_fields = {
        field.ontology_field for node in gcp_nodes for field in node.fields
    }
    assert "value" not in mapped_ontology_fields
