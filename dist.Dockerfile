FROM python:3.9-slim@sha256:3b9df6b3c69a775d4ccb2c2d4b418abd312c6decccfc8bcde2755094ab56f833

# the UID and GID to run cartography as
# (https://github.com/hexops/dockerfile#do-not-use-a-uid-below-10000).
ARG uid=10001
ARG gid=10001

COPY . /var/cartography
WORKDIR /var/cartography

RUN pip install -U -e .

USER ${uid}:${gid}

# verify that the binary at least runs
RUN cartography -h

ENTRYPOINT ["cartography"]
CMD ["-h"]
