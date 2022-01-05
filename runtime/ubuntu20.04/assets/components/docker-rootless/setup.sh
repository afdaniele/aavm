#!/usr/bin/env bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

set -eux

# create "/var/lib/docker" for our rootless user
export AAVM_USER_DOCKER_DIR="${AAVM_USER_HOME}/.local/share/docker"
mkdir -p "${AAVM_USER_DOCKER_DIR}"
chown -R "${AAVM_USER_UID}:${AAVM_USER_GID}" \
    "${AAVM_USER_HOME}/.local" \
    "${AAVM_USER_HOME}/.local/share" \
    "${AAVM_USER_HOME}/.local/share/docker"

# set up subuid/subgid so that "--userns-remap=default" works out-of-the-box
addgroup --system dockremap
adduser --system dockremap
usermod -aG dockremap dockremap
echo 'dockremap:165536:65536' >> /etc/subuid
echo 'dockremap:165536:65536' >> /etc/subgid

# disable docker service extra components
systemctl disable docker.socket
systemctl disable containerd.service

# remove docker service options
rm "/etc/systemd/system/docker.service.d/00.options.conf"

# copy 'dockerd-rootless' script
cp "${SCRIPTPATH}/dockerd-rootless" "/usr/local/bin/dockerd-rootless"

# copy docker-rootless systemd unit
cp "${SCRIPTPATH}/docker-rootless.service" "/etc/systemd/system/docker.service"
