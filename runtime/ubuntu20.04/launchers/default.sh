#!/bin/bash

set -eu

# YOUR CODE BELOW THIS LINE
# ----------------------------------------------------------------------------


# add things that need to be run before systemd here

# make sure we are not restarting the container with docker restart, that leaves the fs read-only
if [ ! -w / ]; then
    echo "Root file system is read-only. Make sure you don't use 'docker restart' on this
    container. You can 'docker stop' and then 'docker start' instead. Starting the container
    again should fix this."
    exit 1
fi

# setup a tmpfs space as a persistent XDG_RUNTIME_DIR for our user
XDG_RUNTIME_DIR="/home/${AAVM_USER}/.local/run"
mkdir -p "${XDG_RUNTIME_DIR}"
rm -rf "${XDG_RUNTIME_DIR:?}/*"
mount -t tmpfs none "${XDG_RUNTIME_DIR}"

# - update user password (only when the container is run for the first time)
if [ ! -f "/boot/.aavm-init.proof" ]; then
    echo -e "${AAVM_USER_PASSWORD}\n${AAVM_USER_PASSWORD}" | passwd "${AAVM_USER}"
fi

# run systemd with PID 1
exec /lib/systemd/systemd --show-status=1

# ----------------------------------------------------------------------------
# YOUR CODE ABOVE THIS LINE
