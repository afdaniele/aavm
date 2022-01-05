#!/bin/bash

set -eu

# YOUR CODE BELOW THIS LINE
# ----------------------------------------------------------------------------


# add things that need to be run before systemd here

# setup a tmpfs space as a persistent XDG_RUNTIME_DIR for our user
XDG_RUNTIME_DIR="/home/${AAVM_USER}/.local/run"
mkdir -p "${XDG_RUNTIME_DIR}"
rm -rf "${XDG_RUNTIME_DIR:?}/*"
mount -t tmpfs none "${XDG_RUNTIME_DIR}"

# - update user password
echo -e "${AAVM_USER_PASSWORD}\n${AAVM_USER_PASSWORD}" | passwd "${AAVM_USER}"

# run systemd with PID 1
exec /lib/systemd/systemd --show-status=1


# ----------------------------------------------------------------------------
# YOUR CODE ABOVE THIS LINE
