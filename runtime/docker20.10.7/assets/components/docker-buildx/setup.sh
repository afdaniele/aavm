#!/usr/bin/env bash

set -eux

# constants
DOCKER_BUILDX_BIN=/usr/local/lib/docker/cli-plugins/docker-buildx

# make buildx executable
chmod +x "${DOCKER_BUILDX_BIN}"
