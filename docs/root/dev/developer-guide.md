# Cartography Developer Guide

## Development using a Python venv

### Running the source code

This document assumes familiarity with Python dev practices such as using [virtualenvs](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/).
If you prefer docker instead, skip this and scroll down to [these instructions](#dev-dockerfile).

1. **Run Neo4j**

    Follow the [Install Steps](../install) so that you get Neo4j running locally. It's up to you if you want to use Docker or a native install.

1. **Install Python 3.10**

1. **Clone the source code**

    Run `cd {path-where-you-want-your-source-code}`. Get the source code with `git clone git://github.com/lyft/cartography.git`

1. **Perform an editable install of the cartography source code**

    Run `cd cartography` and then `uv sync` (yes, actually type the period into the command line) to install Cartography from source to the current venv.

4. **Run from source**

    After this finishes you should be able to run Cartography from source with `uv run cartography --neo4j-uri bolt://localhost:7687`. Any changes to the source code in `{path-where-you-want-your-source-code}/cartography` are now locally testable by running `cartography` from the command line.

### Automated testing

1. **Install test requirements**

    `uv sync --frozen --dev`

:::{hint}
--dev is optional; development dependencies are installed by default.
--frozen ensures that only the pinned dependencies from the lockfile are used, rather than resolving to the latest available versions.
:::

1. **(OPTIONAL) Setup environment variables for integration tests**

    The integration tests expect Neo4j to be running locally, listening on default ports, and with auth disabled.

    To run the integration tests on a specific Neo4j instance, add the following environment variable:

    `export "NEO4J_URL=<your_neo4j_instance_bolt_url:your_neo4j_instance_port>"`

1. **Run tests using `make`**
    - `test_lint` runs [pre-commit](https://pre-commit.com) linting against the codebase.
    - `test_unit` runs the unit test suite.

    :::{warning}
    The below commands will **DELETE ALL NODES** on your local Neo4j instance as part of our testing procedure. Only run any of the below commands if you are ok with this.
    :::

    - `make test_integration` runs the integration test suite.
    For more granular testing, you can invoke `pytest` directly:
      - `uv run pytest ./tests/integration/cartography/intel/aws/test_iam.py`
      - `uv run pytest ./tests/integration/cartography/intel/aws/test_iam.py::test_load_groups`
      - `uv run pytest -k test_load_groups`
    - `uv run make test` can be used to run all of the above.

### Implementing custom sync commands

By default, cartography will try to sync every intel module included as part of the default sync. If you're not using certain intel modules, you can create a custom sync script and invoke it using the cartography CLI. For example, if you're only interested in the AWS intel module you can create a sync script, `custom_sync.py`, that looks like this:

```python
from cartography import cli
from cartography import sync
from cartography.intel import aws
from cartography.intel import create_indexes

def build_custom_sync():
    s = sync.Sync()
    s.add_stages([
        ('create-indexes', create_indexes.run),
        ('aws', aws.start_aws_ingestion),
    ])
    return s

def main(argv):
    return cli.CLI(build_custom_sync(), prog='cartography').main(argv)

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]))
```

Which can then be invoked using `python custom_sync.py` and will have all the features of the cartography CLI while only including the intel modules you are specifically interested in using. For example:

```
cartography$ python custom_sync.py
INFO:cartography.sync:Starting sync with update tag '1569022981'
INFO:cartography.sync:Starting sync stage 'create-indexes'
INFO:cartography.intel.create_indexes:Creating indexes for cartography node types.
INFO:cartography.sync:Finishing sync stage 'create-indexes'
INFO:cartography.sync:Starting sync stage 'aws'
INFO:botocore.credentials:Found credentials in shared credentials file: ~/.aws/credentials
...
```

## dev.Dockerfile

We include a dev.Dockerfile that can help streamline common dev tasks. It is different from the main Dockerfile in that

1. It is strictly intended for dev purposes.
1. It performs an editable install of the cartography source code and test requirements.
1. It does not define a docker entrypoint. This is to allow you to run a custom sync script instead of just the main `cartography` command.

To use it, build dev.Dockerfile with
```bash
cd /path/to/cartography/repo  # We are assuming that you've already cloned the cartography source code
docker build -t cartography-cncf/cartography-dev -f dev.Dockerfile ./
```

With that, there are some interesting things you can do with it.

### Dev with docker-compose

#### Run the full test suite

```bash
docker-compose run --rm cartography-dev make test_lint
docker-compose run --rm  cartography-dev make test_unit
docker-compose run --rm  cartography-dev make test_integration

# for all the above
docker-compose run --rm  cartography-dev make test
```

#### Run a [custom sync script](#implementing-custom-sync-commands)

```bash
docker-compose run --rm  cartography-dev python custom_script.py
```

#### Run the cartography CLI

```bash
docker-compose run --rm  cartography-dev cartography --help
```

### Equivalent manual docker commands

If you don't like docker-compose or if it doesn't work for you for any reason, here are the equivalent manual docker commands for the previous scenarios:

#### Run unit tests with dev.Dockerfile

```bash
docker run --rm cartography-cncf/cartography-dev make test_unit
```

This is a simple command because it doesn't require any volume mounts or docker networking.

#### Run the linter with dev.Dockerfile

```bash
docker run --rm \
    -v $(pwd):/var/cartography \
    -v $(pwd)/.cache/pre-commit:/var/cartography/.cache/pre-commit \
    cartography-cncf/cartography-dev \
    make test_lint
```

The volume mounts are necessary to let pre-commit from within the container edit source files on the host machine, and for pre-commit's cached state to save on your host machine without needing to update itself every time you run it.

#### Run integration tests with dev.Dockerfile

First run a Neo4j container:
```bash
docker run \
    --publish=7474:7474 \
    --publish=7687:7687 \
    --network cartography-network \
    -v data:/data \
    --name cartography-neo4j \
    --env=NEO4J_AUTH=none \
    neo4j:4.4-community
```

and then call the integration test suite like this:
```bash
docker run --rm \
  --network cartography-network \
  -e NEO4J_URL=bolt://cartography-neo4j:7687 \
  cartography-cncf/cartography-dev \
  make test_integration
```

Note that we needed to specify the `NEO4J_URL` env var so that the integration test would be able to reach the Neo4j container.

#### Run the full test suite with dev.Dockerfile

Bring up a neo4j container
```bash
docker run \
    --publish=7474:7474 \
    --publish=7687:7687 \
    --network cartography-network \
    -v data:/data \
    --name cartography-neo4j \
    --env=NEO4J_AUTH=none \
    neo4j:4.4-community
```

and then run the full test suite by specifying all the necessary volumes, network, and env vars.
```bash
docker run --rm \
    -v $(pwd):/var/cartography \
    -v $(pwd)/.cache/pre-commit:/var/cartography/.cache/pre-commit \
    --network cartography-network \
    -e NEO4J_URL=bolt://cartography-neo4j:7687 \
    cartography-cncf/cartography-dev \
    make test
```

#### Run a [custom sync script](#implementing-custom-sync-commands) with dev.Dockerfile

```bash
docker run --rm cartography-cncf/cartography-dev python custom_sync.py
```

#### Run cartography CLI with dev.Dockerfile

```bash
docker run --rm cartography-cncf/cartography-dev cartography --help
```

## How to write a new intel module
See [here](writing-intel-modules).
