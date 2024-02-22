# Cartography Installation

.. _cartography-installation:

Time to set up the server that will run Cartography.  Cartography _should_ work on both Linux and Windows servers, but bear in mind we've only tested it in Linux so far.  Cartography supports Python 3.10. Older versions of Python may work but are not explicitly supported.

1. **Run the Neo4j graph database version 4.x** on your server.

        ⚠️ Neo4j 5.x will probably work but Cartography does not explicitly support it yet.

    1. If you prefer **Docker**, follow the Neo4j Docker [official docs](https://github.com/neo4j/docker-neo4j) to run a version 4.x container.

        - If you are using an ARM-based machine like an M1 Mac, you should use an ARM image otherwise performance will be very slow - Neo4j keeps ARM builds [here](https://hub.docker.com/r/arm64v8/neo4j/).

        - If you're just playing around, you can specify the `--env=NEO4J_AUTH=none` argument to your `docker` command to run a Neo4j container without authentication.

    1. Else if you prefer a **manual install**,

        1. Neo4j requires a JVM (JDK/JRE 11 or higher) to be installed. One option is to install [Amazon Coretto 11](https://docs.aws.amazon.com/corretto/latest/corretto-11-ug/what-is-corretto-11.html).

                ⚠️ Make sure you have `JAVA_HOME` environment variable set. The following works for Mac OS: `export JAVA_HOME=$(/usr/libexec/java_home)`

        1. Go to the [Neo4j download page](https://neo4j.com/download-center/#community), and download Neo4j Community Edition 4.4.\*. If you prefer Docker, you can view Neo4j's instructions [here].

        1. [Install](https://neo4j.com/docs/operations-manual/current/installation/) Neo4j on the server you will run Cartography on.

                ⚠️ For local testing, you might want to turn off authentication via property `dbms.security.auth_enabled` in file /NEO4J_PATH/conf/neo4j.conf

4. Configure your data sources. See the configuration section of each relevant intel module for more details.

5. **Get and run Cartography**

    1. Run `pip install cartography` to install our code.

    1. Finally, to sync your data:

        - For one account using the `default` profile defined in your AWS config file, run

            ```
            cartography --neo4j-uri <uri for your neo4j instance; usually bolt://localhost:7687>
            ```

        - Or for a specific account defined as a separate profile in your AWS config file, set the `AWS_PROFILE` environment variable, for example

            ```
            AWS_PROFILE=other-profile cartography --neo4j-uri <uri for your neo4j instance; usually bolt://localhost:7687>
            ```

        - For more than one AWS account, run

            ```
            AWS_CONFIG_FILE=/path/to/your/aws/config cartography --neo4j-uri <uri for your neo4j instance; usually bolt://localhost:7687> --aws-sync-all-profiles
            ```

        You can view a full list of Cartography's CLI arguments by running `cartography --help`

        The sync will pull data from your configured accounts and ingest data to Neo4j!  This process might take a long time if your account has a lot of assets.

    1. See our [Operations Guide](ops.html) for tips on running Cartography in production.
