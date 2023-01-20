FROM debian:stable-slim

# environment variable to control Conan upload process
ENV CONAN_UPLOAD_CUSTOM 0
# install basic packages
RUN \
    apt update \
    && \
    apt install -y \
                build-essential \
                nghttp2 \
                libnghttp2-dev \
                curl \
                git \
                gcc \
                libssl-dev \
                python \
                python3 \
                python3-pip \
                make \
                zip \
                sudo \
                bc \
    && \
    apt autoremove -y
# place sources from host to container
COPY . /s0nhbuild
# setup Conan
RUN python3 -m pip install conan
# set entrypoint
CMD [ "/bin/bash" ]
