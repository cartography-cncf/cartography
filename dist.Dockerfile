FROM python:3.9-slim@sha256:6294b78e9e3de890e03f09b5229de1a3d9b568de6ed51fc524ebad074402714a

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
