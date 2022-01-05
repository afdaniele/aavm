#!/usr/bin/env bash

set -eux

# update apt lists
apt update

# https://github.com/docker/docker/blob/master/project/PACKAGERS.md#runtime-dependencies
# TODO: perhaps using apt instead of apk helps getting these deps without listing them all here
# - pigz: https://github.com/moby/moby/pull/35697 (faster gzip implementation)
apt install -y --no-install-recommends \
    btrfs-progs \
    e2fsprogs \
    iptables \
    openssl \
    uidmap \
    xfsprogs \
    xz-utils \
    pigz \
    fuse-overlayfs \
    dbus-user-session \
    docker.io

# clear apt lists
rm -rf /var/lib/apt/list/*
