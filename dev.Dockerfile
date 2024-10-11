# Builds cartography container for development by performing a Python editable install of the current source code.
FROM python:3.10-slim

# the UID and GID to run cartography as
# (https://github.com/hexops/dockerfile#do-not-use-a-uid-below-10000).
ARG uid=10001
ARG gid=10001

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends make git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Assumption: current working directory is the cartography source tree from github.
COPY . /var/cartography
WORKDIR /var/cartography
ENV HOME=/var/cartography

RUN pip install -U -e . && \
    pip install -r test-requirements.txt && \
    # Grant write access to the directory for unit and integration test coverage files
    chmod -R a+w /var/cartography && \
    # Sets the directory as safe due to a mismatch in the user that cloned the repo
    # and the user that is going to run the unit&integ tests. This lets pre-commit work.
    git config --global --add safe.directory /var/cartography && \
    git config --local user.name "cartography"

USER ${uid}:${gid}
