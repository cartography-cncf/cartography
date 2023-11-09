# Testing with docker

## Using the included docker-compose support
docker-compose lets you run cartography (and its unit and integration tests)
without needing to install Python and without needing to install Neo4j.

### Usage

1. Build the cartography Dockerfile. This creates a Docker image with all the
Python dependencies needed by cartography and installs cartography itself to
the image.

    ```bash
    # Make sure you don't forget the '.' (represents current directory)
    docker build -t lyft/cartography .
    ```

1. Start up the docker-compose dev environment

    ```bash
    docker-compose up -d
    ```

1. Run the tests
    ```bash
    docker-compose run cartography make test
    # Alternatively replace `make test` with `make test_lint`,
    # `make test_unit`, or `make test_integration`
    ```

Now when you make changes to the code, you can follow the steps above again to
rebuild the container and re-run the automated tests. You can also run the full
cartography sync by following the ["Notes"](#notes) section of this document.

### Configuration

Configuration is possible via the `.compose` directory, which is
git ignored. neo4j config, logs, etc is located at `.compose/neo4j/...`

Configuration for cartography itself should be passed in through
environment variables, using the docker-compose format `-e VARIABLE -e VARIABLE`

AWS credentials can be bind mapped in using volumes. TODO: document correct
bind mount format for docker-compose run.

### Notes

* On initial start of the compose stack, it's necessary to
change the neo4j user's password through the neo4j UI.
* Neither the docker image, nor the docker-compose file define an
entrypoint, so it's necessary to pass in the command being run. This
also makes it possible to run a custom sync script, rather than only
cartography.

### Example

```bash
# Temporarily disable bash command history
set +o history
# See the cartography github configuration intel module docs
export GITHUB_KEY=BASE64ENCODEDKEY
# You need to set this after starting neo4j once, and resetting
# the default neo4j password, which is neo4j
export NEO4j_PASSWORD=...
# Reenable bash command history
set -o history
# Start cartography dependencies
docker-compose up -d
# Run cartography
docker-compose run -e GITHUB_KEY -e NEO4j_PASSWORD cartography cartography --github-config-env-var GITHUB_KEY --neo4j-uri bolt://neo4j:7687 --neo4j-password-env-var NEO4j_PASSWORD --neo4j-user neo4j
```
