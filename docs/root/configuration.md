# Configure Cartography

Cartography uses [**Dynaconf**](https://www.dynaconf.com/) for configuration management. All parameters can be provided in the form of a `settings.toml` file or as environment variables. Dynaconf will also automatically load any `.env` file present in the current directory.

Environment variables follow the pattern:
`PREFIX_MODULE__KEY(__OPTIONAL_SUB_KEY)`

```{warning}
Be careful with the double underscore between the module name and the keys — this syntax is specific to Dynaconf and indicates a level of nesting in the configuration. For example, the pattern above is parsed as `settings.module.key.optional_sub_key`.
```

## Cartography commons settings

| **Name** | **Type** | **Description** |
|----------|----------|-----------------|
| **CARTOGRAPHY_COMMON__HTTP_TIMEOUT** | `int` | Default timeout for all API Calls. Default to 60 seconds. |
| **CARTOGRAPHY_COMMON__UPDATE_TAG** | `int` | A unique tag to apply to all Neo4j nodes and relationships created or updated during the sync run. This tag is used by cleanup jobs to identify nodes and relationships that are stale and need to be removed from the graph. By default, cartography will use a UNIX timestamp as the update tag. |
| **CARTOGRAPHY_NEO4J__URI** | `str` | A valid Neo4j URI to sync against. See 'https://neo4j.com/docs/api/python-driver/current/driver.html#uri for complete documentation on the structure of a Neo4j URI. Default to `bolt://localhost:7687` |
| **CARTOGRAPHY_NEO4J__USER** | `str` | A username with which to authenticate to Neo4j. |
| **CARTOGRAPHY_NEO4J__PASSWORD** | `str` |  A password with which to authenticate to Neo4j. |
| **CARTOGRAPHY_NEO4J__DATABASE** | `str` |  The name of the database in Neo4j to connect to. If not specified, uses the config settings of your Neo4j database itself to infer which database is set to default. See https://neo4j.com/docs/api/python-driver/4.4/api.html#database.'
| **CARTOGRAPHY_NEO4J__PASSWORD_PROMPT** | `bool` | Present an interactive prompt for a password with which to authenticate to Neo4j. This parameter supersedes other methods of supplying a Neo4j password. Default to false. |
| **CARTOGRAPHY_NEO4J__MAX_CONNECTION_LIFETIME** | `int` | Time in seconds for the Neo4j driver to consider a TCP connection alive. cartography default = 3600, 'which is the same as the Neo4j driver default. See https://neo4j.com/docs/driver-manual/1.7/client-applications/#driver-config-connection-pool-management. |


## Migration to the New Format

Cartography previously used a Config file to pass the configuration context to all modules. This object is no longer necessary and is deprecated. Instead, the settings.settings object can be used (it does not need to be passed as an argument, the configuration is global).

### For CLI users
If you previously used the CLI, you can simply replace the arguments with environment variables (you can refer to the documentation of each module to know the different variables):

**Before**:
```bash
LASTPASS_CID="foo" LASTPASS_PROVHASH="bar" cartography --selected-modules lastpqss --lastpass-cid-env-var LASTPASS_CID --lastpass-provhash-env-var LASTPASS_PROVHASH
```
**After**
```bash
CARTOGRAPHY_LASTPASS__CID="foo" CARTOGRAPHY_LASTPASS__PROVHASH="bar" cartography --selected-modules lastpass
```

```{hint}
Configuration can also be done via a settings.toml file (not recommended for secrets) or a `.env` file in the local folder.
```

Example:
`.env` file
```
CARTOGRAPHY_LASTPASS__CID="foo"
CARTOGRAPHY_LASTPASS__PROVHASH="bar"
```

Execution
```
cartography --selected-modules lastpass
```

### With run_with_config function

If you were using the `run_with_config function`, this function is now **deprecated** and you should use the `run` function once your entire configuration is compatible with the new settings module.

In the meantime, you can continue to use the `run_with_config` function, which overrides the settings with the old configuration model.

### With import of start_{module}_ingestion functions

If you were directly importing the `start_{module}_ingestion` functions from each intel module, backward compatibility is ensured. Each module overrides the settings with the old configuration model.

The `config` parameter is deprecated, and you should no longer pass it to the module call functions once the configuration is migrated.
