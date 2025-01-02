# This image is for dev only.
# Performs a Python editable install of the current Cartography source.
# Assumptions:
# - This dockerfile will get called with .cache as a volume mount.
# - The current working directory on the host building this container
#   is the cartography source tree from github.
FROM python:3.10-slim

# The UID and GID to run cartography as.
# This needs to match the gid and uid on the host.
# Update this to match. On WSL2 this is usually 1000.
ARG uid=1000
ARG gid=1000

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends make git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.13 /uv /uvx /bin/

# Install dependencies.
WORKDIR /var/cartography
COPY . /var/cartography
RUN uv sync && \
    chmod -R a+w /var/cartography

ENV HOME=/var/cartography
# Necessary for pre-commit.
RUN git config --global --add safe.directory /var/cartography && \
    git config --local user.name "cartography"

USER ${uid}:${gid}

# Wait for git to be ready before running anything else. Avoid race condition.
ENTRYPOINT ["/var/cartography/dev-entrypoint.sh"]
