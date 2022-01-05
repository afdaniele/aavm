#!/usr/bin/env bash

set -eux

# constants
AVAHI_VERSION=0.7-4ubuntu7.1

# update apt lists
apt update

# install docker-compose
apt install -y --no-install-recommends \
    libnss-mdns \
    avahi-utils \
    avahi-daemon=${AVAHI_VERSION}

# clear apt lists
rm -rf /var/lib/apt/list/*
