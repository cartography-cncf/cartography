FROM python:3.9-slim@sha256:80a625f9f5c36e2eb0d4358fe03bdf6bc99aeea9dfb37a1961eb31525c0e11a7

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
