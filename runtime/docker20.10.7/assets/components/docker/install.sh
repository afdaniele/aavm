#!/usr/bin/env bash

set -eux

# constants
DOCKER_VERSION=20.10.7-0ubuntu5~20.04.2

# update apt lists
apt update

# - pigz: https://github.com/moby/moby/pull/35697 (faster gzip implementation)
apt install -y --no-install-recommends \
    e2fsprogs \
    xfsprogs \
    btrfs-progs \
    openssl \
    xz-utils \
    uidmap \
    pigz \
    fuse-overlayfs \
    dbus-user-session \
    docker.io=${DOCKER_VERSION}

# clear apt lists
rm -rf /var/lib/apt/list/*
