# Cartography Installation On Test Machine

.. _cartography-installation:

Time to set up a test machine to run Cartography. Cartography _should_ work on both Linux and Windows, but bear in mind we've only tested it on Linux so far.

1. Ensure that you have Python 3.10 set up on your machine.

    - Older or newer versions of Python may work but are not explicitly supported. You will probably have more luck with newer versions.

1. **Run the Neo4j graph database version 4.4.\*** or higher on your server. 4.3 and lower will _not_ work.

        ⚠️ Neo4j 5.x will probably work since it's included in our test suite, but we do not explicitly support it yet.

    1. If you prefer **Docker** (recommended), run `docker run --publish=7474:7474 --publish=7687:7687 -v data:/data --env=NEO4J_AUTH=none neo4j:4.4-community` to spin up a Neo4j container. Refer to the Neo4j Docker [official docs](https://github.com/neo4j/docker-neo4j) for more information.

        - Note that we are just playing around here on a test instance and have specified `--env=NEO4J_AUTH=none` to turn off authentication.

        - If you experience very slow write performance using an ARM-based machine like an M1 Mac, you should use an ARM image. Neo4j keeps ARM builds [here](https://hub.docker.com/r/arm64v8/neo4j/).

    1. Else if you prefer a **manual install**,

        1. Neo4j requires a JVM (JDK/JRE 11 or higher) to be installed. One option is to install [Amazon Coretto 11](https://docs.aws.amazon.com/corretto/latest/corretto-11-ug/what-is-corretto-11.html).

            ⚠️ Make sure you have `JAVA_HOME` environment variable set. The following works for Mac OS: `export JAVA_HOME=$(/usr/libexec/java_home)`

        1. Go to the [Neo4j download page](https://neo4j.com/download-center/#community), and download Neo4j Community Edition 4.4.\*.

        1. [Install](https://neo4j.com/docs/operations-manual/current/installation/) Neo4j.

            ⚠️ For local testing, you might want to turn off authentication via property `dbms.security.auth_enabled` in file NEO4J_PATH/conf/neo4j.conf

1. Configure your data sources. See the configuration section of [each relevant intel module](../root/modules) for more details.

1. **Get and run Cartography**

    1. Run `pip install cartography`

        - This will install cartography in the current Python virtual environment. We recommend creating a separate virtual environment for just Cartography and its dependencies.

    1. Finally, let's sync some data into the test graph. In this example we will use AWS. Refer to each module's [specific configuration section](../root/modules) on how to set them up.

        - For one account using the `default` profile defined in your AWS config file, run

            ```
            cartography --neo4j-uri bolt://localhost:7687
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

        If everything worked, the sync will pull data from your configured accounts and ingest data to Neo4j! This process might take a long time if your account has a lot of assets.

        If you encounter errors, review these references:
        - Ensure your ~/.aws/credentials and ~/.aws/config files are set up correctly: https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html
        - Review the various AWS environment variables: https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-envvars.html
        - Cartography uses the boto3 Python library to access AWS, so remember that boto3's standard order of precedence when retrieving credentials applies: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials

    1. Enjoy! Next set up other data providers, see our [Operations Guide](ops.html) for tips on running Cartography in production, view our [usage instructions](../../README.md#usage) for querying tips, and think of [applications](../root/usage/applications.md) to build around it.
