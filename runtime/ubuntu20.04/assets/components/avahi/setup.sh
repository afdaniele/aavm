#!/usr/bin/env bash

set -eux

# enable avahi service
systemctl enable avahi-daemon.service
