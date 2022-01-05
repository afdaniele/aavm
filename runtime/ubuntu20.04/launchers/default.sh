#!/bin/bash

# YOUR CODE BELOW THIS LINE
# ----------------------------------------------------------------------------


# add things that need to be run before systemd here

# - update user password
echo -e "${AAVM_USER_PASSWORD}\n${AAVM_USER_PASSWORD}" | passwd "${AAVM_USER}"

# run systemd with PID 1
exec /lib/systemd/systemd --show-status=1


# ----------------------------------------------------------------------------
# YOUR CODE ABOVE THIS LINE
