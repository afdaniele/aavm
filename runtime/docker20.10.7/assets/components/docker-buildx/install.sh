#!/usr/bin/env bash

set -eux

# constants
DOCKER_BUILDX_VERSION=0.9.1
DOCKER_BUILDX_URL_PREFIX=https://github.com/docker/buildx/releases/download/v${DOCKER_BUILDX_VERSION}/buildx-v${DOCKER_BUILDX_VERSION}
DOCKER_BUILDX_BIN=/usr/local/lib/docker/cli-plugins/docker-buildx

# make destination dir
mkdir -p $(dirname "${DOCKER_BUILDX_BIN}")

# compile url
if [ "$ARCH" == "arm32v7" ]; then
    DOCKER_BUILDX_URL=${DOCKER_BUILDX_URL_PREFIX}.linux-arm-v7
fi
if [ "$ARCH" == "arm64v8" ]; then
    DOCKER_BUILDX_URL=${DOCKER_BUILDX_URL_PREFIX}.linux-arm64
fi
if [ "$ARCH" == "amd64" ]; then
    DOCKER_BUILDX_URL=${DOCKER_BUILDX_URL_PREFIX}.linux-amd64
fi

# install docker buildx
wget --no-verbose -O "${DOCKER_BUILDX_BIN}" "${DOCKER_BUILDX_URL}"

# make buildx executable
chmod +x "${DOCKER_BUILDX_BIN}"
