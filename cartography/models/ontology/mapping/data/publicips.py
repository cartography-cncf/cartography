from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping
from cartography.models.ontology.mapping.specs import OntologyRelMapping

# =============================================================================
# Node Mappings - Create PublicIP nodes from provider-specific IP resources
# =============================================================================

# AWS - ElasticIPAddress
aws_eip_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="ElasticIPAddress",
            fields=[
                OntologyFieldMapping(
                    ontology_field="ip_address", node_field="public_ip", required=True
                ),
            ],
        ),
    ],
)


# Azure - AzurePublicIPAddress
azure_pip_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzurePublicIPAddress",
            fields=[
                OntologyFieldMapping(
                    ontology_field="ip_address", node_field="ip_address", required=True
                ),
            ],
        ),
    ],
)


# Scaleway - ScalewayFlexibleIp
scaleway_fip_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayFlexibleIp",
            fields=[
                OntologyFieldMapping(
                    ontology_field="ip_address", node_field="address", required=True
                ),
            ],
        ),
    ],
)


# GCP - GCPNicAccessConfig
gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPNicAccessConfig",
            fields=[
                OntologyFieldMapping(
                    ontology_field="ip_address", node_field="public_ip", required=True
                ),
            ],
        ),
    ],
)


# =============================================================================
# Relation Mappings - Link PublicIP to ontology abstract nodes via provider nodes
# Note: Relations to semantic labels (ComputeInstance, LoadBalancer) are defined
# directly in the PublicIP schema model (publicip.py)
# =============================================================================

# CrowdStrike - Link PublicIP to Device via CrowdstrikeHost
crowdstrike_mapping = OntologyMapping(
    module_name="crowdstrike",
    nodes=[],
    rels=[
        OntologyRelMapping(
            __comment__="Link PublicIP to Device based on CrowdstrikeHost external_ip",
            query=(
                "MATCH (p:PublicIP), (host:CrowdstrikeHost)<-[:OBSERVED_AS]-(d:Device) "
                "WHERE host.external_ip = p.ip_address "
                "MERGE (p)-[r:POINTS_TO]->(d) "
                "ON CREATE SET r.firstseen = timestamp() "
                "SET r.lastupdated = $UPDATE_TAG"
            ),
            iterative=False,
        ),
    ],
)


PUBLIC_IPS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_eip_mapping,
    "azure": azure_pip_mapping,
    "crowdstrike": crowdstrike_mapping,
    "gcp": gcp_mapping,
    "scaleway": scaleway_fip_mapping,
}
