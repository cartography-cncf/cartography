FROM python:3.9-slim@sha256:2d01c76bb5bdcee5e711df349ff6e76efdf920f2e30e50effcf4f6e0dfccd3a2

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
