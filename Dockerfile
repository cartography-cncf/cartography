# Base image
FROM python:3.10-slim@sha256:49454d2bf78a48f217eb25ecbcb4b5face313fea6a6e82706465a6990303ada2 AS base
# Default to ''. Overridden with a specific version specifier e.g. '==0.98.0' by build args or from GitHub actions.
ARG VERSION_SPECIFIER
# the UID and GID to run cartography as
# (https://github.com/hexops/dockerfile#do-not-use-a-uid-below-10000).
ARG uid=10001
ARG gid=10001
USER ${uid}:${gid}
WORKDIR /var/cartography
ENV HOME=/var/cartography



# Intermediate image to build the venv
FROM base AS builder
# Install uv version 0.7.3
COPY --from=ghcr.io/astral-sh/uv@sha256:87a04222b228501907f487b338ca6fc1514a93369bfce6930eb06c8d576e58a4 /uv /uvx /bin/
# Install cartography
RUN ls -alh /var/cartography
RUN uv tool install cartography${VERSION_SPECIFIER}
RUN ls -alh /var/cartography


# Final production image
FROM base AS production
# Copy venv from the builder stage
COPY --from=builder --chown=${uid}:${gid} /var/cartography/.local /var/cartography/.local
ENV PATH="/var/cartography/.local/bin:$PATH"
# verify that the binary at least runs
RUN cartography -h

ENTRYPOINT ["cartography"]
CMD ["-h"]
