from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# Database fields:
# _ont_db_name - The name/identifier of the database
# _ont_db_type - The database engine/type (e.g., "mysql", "postgres", "dynamodb")
# _ont_db_version - The database engine version
# _ont_db_endpoint - The connection endpoint/address for the database
# _ont_db_port - The port number the database listens on
# _ont_db_encrypted - Whether the database storage is encrypted
# _ont_db_location - The physical location/region of the database

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="RDSCluster",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="database_name", required=True
                ),
                OntologyFieldMapping(ontology_field="type", node_field="engine"),
                OntologyFieldMapping(
                    ontology_field="version", node_field="engine_version"
                ),
                OntologyFieldMapping(ontology_field="endpoint", node_field="endpoint"),
                OntologyFieldMapping(ontology_field="port", node_field="port"),
                OntologyFieldMapping(
                    ontology_field="encrypted", node_field="storage_encrypted"
                ),
                OntologyFieldMapping(ontology_field="location", node_field="region"),
            ],
        ),
        OntologyNodeMapping(
            node_label="RDSInstance",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="db_name", required=True
                ),
                OntologyFieldMapping(ontology_field="type", node_field="engine"),
                OntologyFieldMapping(
                    ontology_field="version", node_field="engine_version"
                ),
                OntologyFieldMapping(
                    ontology_field="endpoint", node_field="endpoint_address"
                ),
                OntologyFieldMapping(ontology_field="port", node_field="endpoint_port"),
                OntologyFieldMapping(
                    ontology_field="encrypted", node_field="storage_encrypted"
                ),
                OntologyFieldMapping(ontology_field="location", node_field="region"),
            ],
        ),
        OntologyNodeMapping(
            node_label="DynamoDBTable",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "dynamodb"},
                ),
                # _ont_db_version: Not applicable to DynamoDB (managed service)
                # _ont_db_endpoint: DynamoDB uses AWS SDK endpoints, not direct DB endpoints
                # _ont_db_port: Not applicable to DynamoDB (HTTPS API)
                # _ont_db_encrypted: Not exposed in current model
                OntologyFieldMapping(ontology_field="location", node_field="region"),
            ],
        ),
    ],
)

azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureSQLDatabase",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="type", node_field="kind"),
                # _ont_db_version: Not directly exposed in AzureSQLDatabase model
                # _ont_db_endpoint: Constructed from server endpoint, not directly on database
                # _ont_db_port: Typically 1433 for Azure SQL, but not in model
                # _ont_db_encrypted: Not directly exposed in current model
                OntologyFieldMapping(ontology_field="location", node_field="location"),
            ],
        ),
        OntologyNodeMapping(
            node_label="AzureCosmosDBSqlDatabase",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "cosmosdb-sql"},
                ),
                # _ont_db_version: Not applicable to managed CosmosDB
                # _ont_db_endpoint: Account-level, not database-level
                # _ont_db_port: Account-level, not database-level
                # _ont_db_encrypted: Account-level configuration
                OntologyFieldMapping(ontology_field="location", node_field="location"),
            ],
        ),
        OntologyNodeMapping(
            node_label="AzureCosmosDBMongoDBDatabase",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "cosmosdb-mongodb"},
                ),
                # _ont_db_version: Not applicable to managed CosmosDB
                # _ont_db_endpoint: Account-level, not database-level
                # _ont_db_port: Account-level, not database-level
                # _ont_db_encrypted: Account-level configuration
                OntologyFieldMapping(ontology_field="location", node_field="location"),
            ],
        ),
        OntologyNodeMapping(
            node_label="AzureCosmosDBCassandraKeyspace",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "cosmosdb-cassandra"},
                ),
                # _ont_db_version: Not applicable to managed CosmosDB
                # _ont_db_endpoint: Account-level, not keyspace-level
                # _ont_db_port: Account-level, not keyspace-level
                # _ont_db_encrypted: Account-level configuration
                OntologyFieldMapping(ontology_field="location", node_field="location"),
            ],
        ),
    ],
)

gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPBigtableInstance",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="display_name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "bigtable"},
                ),
                # _ont_db_version: Not applicable to managed Bigtable service
                # _ont_db_endpoint: Constructed programmatically, not in model
                # _ont_db_port: Not applicable (uses gRPC, not a fixed port)
                # _ont_db_encrypted: Bigtable is encrypted at rest by default, not exposed
            ],
        ),
    ],
)

DATABASES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "azure": azure_mapping,
    "gcp": gcp_mapping,
}
