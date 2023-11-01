FROM python:3.12-slim-bookworm as base

# variable store
ARG WDIR="/zero_build"
ENV CONAN_UPLOAD_CUSTOM 0

# install basic packages
RUN \
    apt-get update \
    && \
    apt-get install -y \
        curl \
        git \
        gcc \
        g++ \
        libssl-dev \
        python3 \
        python3-pip \
        make \
        zip \
        bc \
        libgpgme-dev \
        bison \
        flex

# place sources from host to container
COPY . $WDIR
WORKDIR $WDIR

# configure Python environment
RUN python3 -m pip install pip --upgrade && \
    python3 -m pip install poetry && \
    python3 -m poetry config virtualenvs.create false && \
    python3 -m poetry install --no-root

# install shared tools from tools.json
RUN python3 $WDIR/wrapper/bridge.py --tools

# launch app
CMD [ "/bin/bash" ]
