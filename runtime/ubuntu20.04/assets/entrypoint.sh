#!/usr/bin/env bash



# create 'duckie' user, password is the default (but encrypted)
useradd \
    --create-home \
    --password "paZ0XeCbsQDFc" \
    --shell /bin/bash \
    --uid 1000 \
    --user-group \
    duckie

# add things that need to be run before systemd here
# (empty)

# run systemd with PID 1
exec /lib/systemd/systemd