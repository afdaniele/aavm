#!/usr/bin/env bash

set -eux

# update apt lists
apt update

# install docker-compose
apt install -y --no-install-recommends \
    avahi-utils \
    avahi-daemon \
    libnss-mdns

# clear apt lists
rm -rf /var/lib/apt/list/*
