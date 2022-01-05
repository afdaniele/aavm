#!/usr/bin/env bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

set -eux

# add options to systemd's ssh service
cp -r "${SCRIPTPATH}/ssh.service.d" "/etc/systemd/system/"



#set -eux

# enable sshd
systemctl enable ssh.service

# add a configuration service
#cp "${SCRIPTPATH}/ssh-enable-login.service" /etc/systemd/system/
#systemctl enable ssh-enable-login


