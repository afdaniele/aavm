#!/usr/bin/env bash

set -eux

# enable docker service
systemctl enable docker.service

# give the user permissions to access the engine
usermod -aG docker user
