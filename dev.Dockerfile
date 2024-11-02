# Builds cartography container for development by performing a Python editable install of the current source code.
FROM python:3.10-slim

# The UID and GID to run cartography as.
# This needs to match the gid and uid on the host.
# In WSL this needs to be 1000 to work.
ARG uid=1000
ARG gid=1000

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends make git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements files and install dependencies
WORKDIR /var/cartography
COPY test-requirements.txt ./
COPY . /var/cartography
RUN pip install -r test-requirements.txt && \
    pip install -U -e . && \
    chmod -R a+w /var/cartography

# now copy entire source tree
# Assumption: current working directory is the cartography source tree from github.
WORKDIR /var/cartography
ENV HOME=/var/cartography

RUN git config --global --add safe.directory /var/cartography && \
    git config --local user.name "cartography"
    # assumption: this dockerfile will get called with .cache as a volume mount

USER ${uid}:${gid}
