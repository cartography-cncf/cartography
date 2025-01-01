# This is a thin distribution of the cartography software.
# It is published at ghcr.io.
FROM python:3.10-slim

# Build argument from GitHub actions
ARG VERSION

# the UID and GID to run cartography as
# (https://github.com/hexops/dockerfile#do-not-use-a-uid-below-10000).
ARG uid=10001
ARG gid=10001

WORKDIR /var/cartography
ENV HOME=/var/cartography

# Install cartography at the version specified from GitHub actions
RUN pip install cartography==$VERSION

USER ${uid}:${gid}

# verify that the binary at least runs
RUN cartography -h

ENTRYPOINT ["cartography"]
CMD ["-h"]
