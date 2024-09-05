FROM python:3.9-slim@sha256:c77f33ea7561185b45f8afa0ade846585ac3ae87e0f814948f8232a974d584de

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
