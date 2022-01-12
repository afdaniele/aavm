#!/usr/bin/env bash

set -eux

# constants
export ROOTLESSKIT_VERSION="20.10.12"

# update apt lists
apt update

# busybox "ip" is insufficient:
#   [rootlesskit:child ] error: executing [[ip tuntap add name tap0 mode tap] [ip link set tap0 address 02:50:00:00:00:01]]: exit status 1
apt install -y --no-install-recommends \
    iproute2

# clear apt lists
rm -rf /var/lib/apt/list/*

# find the URL for the rootlesskit library
ROOTLESSKIT_URL=""
case $ARCH in
  amd64)
    ROOTLESSKIT_URL="https://download.docker.com/linux/static/stable/x86_64/docker-rootless-extras-${ROOTLESSKIT_VERSION}.tgz"
    ;;

  arm64v8)
    ROOTLESSKIT_URL="https://download.docker.com/linux/static/stable/aarch64/docker-rootless-extras-${ROOTLESSKIT_VERSION}.tgz"
    ;;

  *)
    echo >&2 "error: the component 'docker-rootless' does not support the architecture '${ARCH}'"
    exit 1
    ;;
esac

# download rootlesskit library
cd /tmp
mkdir ./rootlesskit
cd ./rootlesskit
wget --no-verbose -O ./rootless.tgz "${ROOTLESSKIT_URL}"

# install rootlesskit library
tar --extract \
    --file ./rootless.tgz \
    --strip-components 1 \
    --directory /usr/local/bin/ \
    'docker-rootless-extras/rootlesskit' \
    'docker-rootless-extras/rootlesskit-docker-proxy' \
    'docker-rootless-extras/vpnkit'

# cleanup
cd ~
rm -rf /tmp/rootlesskit
