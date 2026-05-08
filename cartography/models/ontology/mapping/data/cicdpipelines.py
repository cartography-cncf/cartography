from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# CICDPipeline fields:
# _ont_name - The display name of the pipeline definition
# _ont_type - The pipeline category, normalized to "build" / "deploy" / "iac"
# _ont_status - The lifecycle state of the pipeline (active, disabled, ...)

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="CodeBuildProject",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "build"},
                ),
                # _ont_status: CodeBuild has no per-project status; only per-build status.
            ],
        ),
    ],
)

# Azure Data Factory pipelines are deliberately excluded from CICDPipeline. ADF pipelines
# are data-movement / ETL workflows (datasets, linked services, data flows), not CI/CD
# pipeline definitions. Mapping them here would conflate ETL with build/deploy/IaC and
# pollute supply-chain inventory queries.

github_mapping = OntologyMapping(
    module_name="github",
    nodes=[
        OntologyNodeMapping(
            node_label="GitHubWorkflow",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "build"},
                ),
                OntologyFieldMapping(ontology_field="status", node_field="state"),
            ],
        ),
    ],
)

gitlab_mapping = OntologyMapping(
    module_name="gitlab",
    nodes=[
        OntologyNodeMapping(
            node_label="GitLabCIConfig",
            fields=[
                # GitLabCIConfig has no display name; the file_path
                # (e.g. ".gitlab-ci.yml") is the canonical identifier.
                OntologyFieldMapping(
                    ontology_field="name", node_field="file_path", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "build"},
                ),
                # _ont_status: config is a static definition, no runtime status.
            ],
        ),
    ],
)

spacelift_mapping = OntologyMapping(
    module_name="spacelift",
    nodes=[
        OntologyNodeMapping(
            node_label="SpaceliftStack",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "iac"},
                ),
                OntologyFieldMapping(ontology_field="status", node_field="state"),
            ],
        ),
    ],
)

CICDPIPELINES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "github": github_mapping,
    "gitlab": gitlab_mapping,
    "spacelift": spacelift_mapping,
}
