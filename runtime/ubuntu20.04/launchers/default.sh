#!/bin/bash

trap shutdown SIGINT
trap shutdown SIGTERM

# YOUR CODE BELOW THIS LINE
# ----------------------------------------------------------------------------


# create 'duckie' user, password is the default (but encrypted)
#useradd \
#    --create-home \
#    --password "paZ0XeCbsQDFc" \
#    --shell /bin/bash \
#    --uid 1000 \
#    --user-group \
#    duckie

# add things that need to be run before systemd here
# (empty)

systemctl disable etc-hostname.mount
systemctl mask etc-hostname.mount

# run systemd with PID 1
exec /lib/systemd/systemd


# ----------------------------------------------------------------------------
# YOUR CODE ABOVE THIS LINE

