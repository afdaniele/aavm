#!/usr/bin/env bash

set -eux

# constants
OPENSSH_SERVER_VERSION=1:8.2p*

# update apt lists
apt update

# install docker-compose
apt install -y --no-install-recommends \
    openssh-server=${OPENSSH_SERVER_VERSION}

# clear apt lists
rm -rf /var/lib/apt/list/*
