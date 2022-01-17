#!/bin/bash

set -eu

# NOTE: this setup script will be executed right before the launcher file inside the container,
#       use it to configure your environment.

# NOTE: do not use variables here
source "/aavm/constants.sh"

# make sure the docker socket is exposed correctly
export DOCKER_HOST="unix:///home/${AAVM_USER}/.local/run/docker.sock"
