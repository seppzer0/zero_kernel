FROM python:3.12-slim-bookworm AS base

# variable store
ARG WDIR=/zero_build
ENV CONAN_UPLOAD_CUSTOM 0

# transfer sources from host to container
COPY . ${WDIR}
WORKDIR ${WDIR}
ENV PYTHONPATH ${WDIR}

# install system packages
RUN \
    apt-get update \
    && \
    apt-get install -y \
        curl \
        wget \
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

# configure Python environment
RUN python3 -m pip install pip --upgrade && \
    python3 -m pip install -r requirement-uv.txt && \
    uv sync --frozen --no-install-project

# install shared tools from tools.json;
#
# The idea here is that we pre-pack all the tools into the Docker/Podman image that can be used for any device:
# (toolchains, binutils -- everything except device-specific kernel source);
# 
# This significantly reduces the total build time, as each time we make a build call for a device,
# only device-specific kernel source is being downloaded into the container.
#
RUN uv run ${WDIR}/builder/utils/bridge.py --shared

# launch app
CMD [ "/bin/bash" ]
