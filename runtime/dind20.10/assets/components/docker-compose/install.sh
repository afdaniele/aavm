#!/usr/bin/env bash

set -eux

# constants
DOCKER_COMPOSE_VERSION=1.25.0-1

# update apt lists
apt update

# install docker-compose
apt install -y --no-install-recommends \
    docker-compose=${DOCKER_COMPOSE_VERSION}

# clear apt lists
rm -rf /var/lib/apt/list/*
