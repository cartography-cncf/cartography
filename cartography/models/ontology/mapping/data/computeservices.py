# Ontology mapping for the ComputeService semantic label.
#
# _ont_name - The display name of the service / orchestrator.
# _ont_region - The region or location where the service is deployed.
# _ont_status - Current provisioning or operational status of the service.
from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

aws_ecs_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="ECSService",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(ontology_field="status", node_field="status"),
            ],
        ),
    ],
)

gcp_cloudrun_service_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPCloudRunService",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="region", node_field="location"),
                # status: GCPCloudRunService does not surface a single provisioning
                # status field; revision-level state lives on GCPCloudRunRevision.
            ],
        ),
    ],
)

gcp_cloudrun_job_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPCloudRunJob",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="region", node_field="location"),
                # status: GCPCloudRunJob does not surface a single provisioning
                # status field; per-execution state lives on GCPCloudRunExecution.
            ],
        ),
    ],
)

COMPUTESERVICES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws_ecs": aws_ecs_mapping,
    "gcp_cloudrun_service": gcp_cloudrun_service_mapping,
    "gcp_cloudrun_job": gcp_cloudrun_job_mapping,
}
