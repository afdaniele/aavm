#!/usr/bin/env bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

set -eux

# add options to systemd's docker service
# TODO: test without this
cp -r "${SCRIPTPATH}/docker.service.d" "/etc/systemd/system/"

# enable docker service
systemctl enable docker.service
