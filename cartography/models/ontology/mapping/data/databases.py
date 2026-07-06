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
            node_label="RDSInstance",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="db_instance_identifier",
                    required=True,
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
            node_label="ESDomain",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # `engine` is derived in the elasticsearch transform from
                # ElasticsearchVersion so we label OpenSearch-backed domains
                # as "opensearch" and the legacy Elasticsearch-backed ones as
                # "elasticsearch".
                OntologyFieldMapping(ontology_field="type", node_field="engine"),
                OntologyFieldMapping(
                    ontology_field="version", node_field="elasticsearch_version"
                ),
                OntologyFieldMapping(ontology_field="endpoint", node_field="endpoint"),
                OntologyFieldMapping(
                    ontology_field="encrypted",
                    node_field="encryption_at_rest_options_enabled",
                ),
                # _ont_db_port: Not applicable (HTTPS API)
                # _ont_db_location: Region is not currently stored on the ESDomain node.
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
        OntologyNodeMapping(
            node_label="GCPCloudSQLInstance",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="version", node_field="database_version"
                ),
                OntologyFieldMapping(
                    ontology_field="type", node_field="database_engine"
                ),
                OntologyFieldMapping(ontology_field="location", node_field="region"),
                # endpoint: connection_name available but format differs from standard endpoints
                # port: not directly available in GCPCloudSQLInstance
                # encrypted: not directly available in GCPCloudSQLInstance
            ],
        ),
        OntologyNodeMapping(
            node_label="GCPBigQueryDataset",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="dataset_id",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "bigquery"},
                ),
                OntologyFieldMapping(ontology_field="location", node_field="location"),
                # _ont_db_version: Not applicable to managed BigQuery service
                # _ont_db_endpoint: BigQuery uses project/dataset identifiers, not endpoints
                # _ont_db_port: Not applicable (REST/gRPC API)
                # _ont_db_encrypted: BigQuery is encrypted at rest by default, not exposed
            ],
        ),
    ],
)

scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayRdbInstance",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="type", node_field="engine"),
                # version: not exposed as a standalone field; engine string includes it.
                OntologyFieldMapping(
                    ontology_field="endpoint",
                    node_field="public_endpoint_hostname",
                    special_handling="coalesce",
                    extra={"fields": ["public_endpoint_ip", "private_endpoint_ip"]},
                ),
                OntologyFieldMapping(
                    ontology_field="port",
                    node_field="public_endpoint_port",
                    special_handling="coalesce",
                    extra={"fields": ["private_endpoint_port"]},
                ),
                OntologyFieldMapping(
                    ontology_field="encrypted",
                    node_field="encryption_at_rest_enabled",
                ),
                OntologyFieldMapping(ontology_field="location", node_field="region"),
            ],
        ),
        OntologyNodeMapping(
            node_label="ScalewayRedisCluster",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "redis"},
                ),
                OntologyFieldMapping(ontology_field="version", node_field="version"),
                OntologyFieldMapping(
                    ontology_field="endpoint",
                    node_field="public_endpoint_ip",
                    special_handling="coalesce",
                    extra={"fields": ["private_endpoint_ip"]},
                ),
                OntologyFieldMapping(
                    ontology_field="port",
                    node_field="public_endpoint_port",
                    special_handling="coalesce",
                    extra={"fields": ["private_endpoint_port"]},
                ),
                # _ont_db_encrypted: Redis storage encryption isn't exposed on the
                # cluster node; tls_enabled covers transport encryption only.
                OntologyFieldMapping(ontology_field="location", node_field="zone"),
            ],
        ),
        OntologyNodeMapping(
            node_label="ScalewayMongoDBInstance",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "mongodb"},
                ),
                OntologyFieldMapping(ontology_field="version", node_field="version"),
                OntologyFieldMapping(
                    ontology_field="endpoint",
                    node_field="public_endpoint_dns",
                    special_handling="coalesce",
                    extra={"fields": ["private_endpoint_dns"]},
                ),
                OntologyFieldMapping(
                    ontology_field="port",
                    node_field="public_endpoint_port",
                    special_handling="coalesce",
                    extra={"fields": ["private_endpoint_port"]},
                ),
                # _ont_db_encrypted: Scaleway MongoDB is encrypted at rest by
                # default but the flag isn't surfaced on the instance object.
                OntologyFieldMapping(ontology_field="location", node_field="region"),
            ],
        ),
        OntologyNodeMapping(
            node_label="ScalewayDataWarehouseDeployment",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "clickhouse"},
                ),
                OntologyFieldMapping(ontology_field="version", node_field="version"),
                OntologyFieldMapping(ontology_field="location", node_field="region"),
                # endpoint/port: not surfaced as scalars on the deployment; only
                # a public-exposure flag (is_public) is retained.
                # _ont_db_encrypted: encrypted at rest by default, not exposed.
            ],
        ),
        OntologyNodeMapping(
            node_label="ScalewayServerlessSQLDatabase",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "postgres"},
                ),
                OntologyFieldMapping(
                    ontology_field="version", node_field="engine_major_version"
                ),
                OntologyFieldMapping(ontology_field="endpoint", node_field="endpoint"),
                OntologyFieldMapping(ontology_field="location", node_field="region"),
                # _ont_db_encrypted: encrypted at rest by default, not exposed.
            ],
        ),
        OntologyNodeMapping(
            node_label="ScalewaySearchDeployment",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "opensearch"},
                ),
                OntologyFieldMapping(ontology_field="version", node_field="version"),
                OntologyFieldMapping(ontology_field="location", node_field="region"),
                # endpoint/port: not surfaced as scalars; only a public-exposure
                # flag (is_public) is retained.
                # _ont_db_encrypted: encrypted at rest by default, not exposed.
            ],
        ),
    ],
)

DATABASES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "azure": azure_mapping,
    "gcp": gcp_mapping,
    "scaleway": scaleway_mapping,
}
