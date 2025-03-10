# This is a thin distribution of the cartography software.
# It is published at ghcr.io.
FROM python:3.10-slim@sha256:f680fc3f447366d9be2ae53dc7a6447fe9b33311af209225783932704f0cb4e7

# Default to ''. Overridden with a specific version specifier e.g. '==0.98.0' by build args or from GitHub actions.
ARG VERSION_SPECIFIER

# the UID and GID to run cartography as
# (https://github.com/hexops/dockerfile#do-not-use-a-uid-below-10000).
ARG uid=10001
ARG gid=10001

WORKDIR /var/cartography
ENV HOME=/var/cartography

# Install cartography at the given version specifier. Can be ''.
RUN pip install --no-cache-dir cartography${VERSION_SPECIFIER}

USER ${uid}:${gid}

# verify that the binary at least runs
RUN cartography -h

ENTRYPOINT ["cartography"]
CMD ["-h"]
