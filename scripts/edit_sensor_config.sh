#!/usr/bin/env bash
CONFIG_DIR="/etc/kootnet"
# Make sure its running with root
if [[ $EUID != 0 ]]; then
  printf "\nStarting with sudo\n"
  sudo "$0" "$@"
  exit $?
fi
# Change HTTP Authentication User & Password
read -p "Do you want to Change the HTTP Authentication? (Y/N) " -n 1 -r AUTH
echo
if [[ ${AUTH} =~ ^[Yy]$ ]]
then
  bash /opt/kootnet-sensors/scripts/change_http_authentication.sh
fi
# Open Config Files if installed
if [[ -f ${CONFIG_DIR}"/installed_datetime.txt" ]]
then
  printf "\nPrevious install detected, opening configuration files\n"
  nano ${CONFIG_DIR}/installed_sensors.conf
  nano ${CONFIG_DIR}/sql_recording.conf
  nano /etc/network/interfaces
  nano /etc/wpa_supplicant/wpa_supplicant.conf
  printf "\nRestarting Services, please wait ...\n\n"
  systemctl daemon-reload
  systemctl restart KootnetSensors
  sleep 5
  printf "Printing config & testing sensors\n\n"
  /home/kootnet_data/python-env/bin/python3 /opt/kootnet-sensors/test_sensors.py
fi
printf "\nPress enter to exit ..."
read -r nothing
