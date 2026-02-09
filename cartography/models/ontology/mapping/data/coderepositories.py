from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# CodeRepository ontology fields:
# - id: Unique identifier (URL or URI)
# - name: Repository name
# - fullname: Full path including namespace (e.g., "org/repo")
# - description: Repository description
# - url: Web URL to access the repository
# - default_branch: Default branch name
# - public: Whether the repository is publicly accessible
# - archived: Whether the repository is archived

github_mapping = OntologyMapping(
    module_name="github",
    nodes=[
        OntologyNodeMapping(
            node_label="GitHubRepository",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True
                ),
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="fullname", node_field="fullname"),
                OntologyFieldMapping(
                    ontology_field="description", node_field="description"
                ),
                OntologyFieldMapping(ontology_field="url", node_field="url"),
                OntologyFieldMapping(
                    ontology_field="default_branch", node_field="defaultbranch"
                ),
                OntologyFieldMapping(
                    ontology_field="public",
                    node_field="private",
                    special_handling="invert_boolean",
                ),
                OntologyFieldMapping(ontology_field="archived", node_field="archived"),
            ],
        ),
    ],
)

gitlab_mapping = OntologyMapping(
    module_name="gitlab",
    nodes=[
        OntologyNodeMapping(
            node_label="GitLabProject",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True
                ),
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="fullname", node_field="path_with_namespace"
                ),
                OntologyFieldMapping(
                    ontology_field="description", node_field="description"
                ),
                # GitLabProject uses 'id' as web_url, so we use the same field for url
                OntologyFieldMapping(ontology_field="url", node_field="id"),
                OntologyFieldMapping(
                    ontology_field="default_branch", node_field="default_branch"
                ),
                # GitLab uses 'visibility' (private, internal, public) - only "public" maps to public=true
                OntologyFieldMapping(
                    ontology_field="public",
                    node_field="visibility",
                    special_handling="equal_boolean",
                    extra={"values": ["public"]},
                ),
                OntologyFieldMapping(ontology_field="archived", node_field="archived"),
            ],
        ),
    ],
)

CODEREPOSITORIES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "github": github_mapping,
    "gitlab": gitlab_mapping,
}
