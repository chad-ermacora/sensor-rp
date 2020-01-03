#!/usr/bin/env bash
CONFIG_DIR="/etc/kootnet"
# HTTP Server Options
HTTP_SERVER="http://kootenay-networks.com"
DEB_INSTALLER="/KootnetSensors.deb"
clear
# Make sure its running with root
if [[ $EUID != 0 ]]; then
  printf "\nStarting with sudo\n"
  sudo "$0" "$@"
  exit $?
fi
# Check for development switch
if [[ "$1" == "dev" ]]
then
  HTTP_FOLDER="/installers/dev"
  printf '\n-- DEVELOPMENT HTTP UPGRADE OR INSTALL --\n'
else
  printf '\n-- HTTP UPGRADE OR INSTALL --\n'
  HTTP_FOLDER="/installers"
fi
# Clean up previous downloads if any
rm -f /tmp${DEB_INSTALLER} 2>/dev/null
printf '\nDownloading Deb Installer\n'
wget -O /tmp${DEB_INSTALLER} ${HTTP_SERVER}${HTTP_FOLDER}${DEB_INSTALLER}
printf '\nInstalling Kootnet Sensors Debian Package\n'
apt-get -y install /tmp${DEB_INSTALLER}
date > ${CONFIG_DIR}/last_updated.txt
echo ' - HTTP ' >> ${CONFIG_DIR}/last_updated.txt
printf '\n\nOpen https://localhost:10065 on the local sensor to configure\n\n'
printf 'To access the sensor from another device, replace "localhost" with an IP\n'
printf 'IP addresses show below  ** Note: 127.0.0.1 is the same as localhost **\n\n'
ip -4 addr | grep -oP '(?<=inet\s)\d+(\.\d+){3}'
printf '\n'
