# This will copy all the needed files, install the dependencies and update the system
# In crontab under root, scripts are auto run to keep 3 programs running as well as
# The primary interval sensor program recording to a SQL DB.
if [ -f "/home/pi/KootNetSensors/zInstalled.txt" ]
then
  printf '\nInstall Detected, Opening Configuration Files\n'
  nano /home/pi/KootNetSensors/installed_sensors.txt
  nano /home/pi/KootNetSensors/config.txt
  nano /etc/network/interfaces
  nano /etc/wpa_supplicant/wpa_supplicant.conf
else
  # Create folders, download files to root/SensorInstallFiles/, then install
  rm -R /root/SensorInstallFiles 2>/dev/null
  mkdir /root/SensorInstallFiles 2>/dev/null
  mkdir /home/sensors 2>/dev/null
  cd /root/SensorInstallFiles
  wget -r -np -nH -R "index.html*" http://kootenay-networks.com/utils/koot_net_sensors/Installers/raw_files/sensor-rp/
  clear
  printf '\nFiles Downloaded from KootNet HTTP Server\n\nStarting Install\n'
  cp -R /root/SensorInstallFiles/utils/koot_net_sensors/Installers/raw_files/sensor-rp/* /home/sensors/
  # Add easy upgrade, config edits & sensor test app(s) to user pi's home directory
  cp /home/sensors/upgrade/update_programs_online.sh /home/pi/update_sensor_online.sh
  cp /home/sensors/upgrade/install_kootnet_sensors.sh /home/pi/sensor_edit_configs.sh
  cp /home/sensors/upgrade/clean_upgrade_online.sh /home/pi/KootNetSensors/clean_upgrade_online.sh
  cp /home/sensors/upgrade/clean_upgrade_smb.sh /home/pi/KootNetSensors/clean_upgrade_smb.sh
  ln -sf /home/sensors/test_sensors.py /home/pi/test_sensors.py
  printf '\nInstalled Config Files, Opening for edit\n'
  # Create "installed_sensors.txt" file
  bash /home/sensors/upgrade/check_installed_sensors.sh
  # Add and edit TCP/IP v4 Network + Wireless
  cat >> /etc/network/interfaces << "EOF"

# Be sure to Change the IP to match your network
#
# To let your wireless router assign the IP
# Change 'iface wlan0 inet static' to 'iface wlan0 inet dhcp'
# Then remove all lines below EXCEPT for the one with wpa-conf

allow-hotplug wlan0
iface wlan0 inet static
  address 192.168.10.254
  netmask 255.255.255.0
  gateway 192.168.10.1
  dns-nameservers 192.168.10.1
  wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
EOF
  date > /home/pi/KootNetSensors/zInstalled.txt
  cat > /etc/wpa_supplicant/wpa_supplicant.conf << "EOF"
# Be sure to update to your wireless network
#
# Which ever wireless network has more signal strength
# Is the one that will connect, assuming settings are correct
#
# To add additional wireless network connections
# Copy one of the network blocks, including both { } and
# Paste it at the bottom of the file & Modify as needed

ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=CA

network={
        ssid="SensorWifi"
        psk="2505512335"
        key_mgmt=WPA-PSK
}
network={
        ssid="KI-WiFi"
        psk="2505510208"
        key_mgmt=WPA-PSK
}
EOF
  nano /etc/network/interfaces
  nano /etc/wpa_supplicant/wpa_supplicant.conf
  # Upgrade System
  printf '\nStarting System Update, this may take awhile ...\n\n'
  # Remove wolfram-engine due to size of upgrades
  apt-get -y remove wolfram-engine
  apt-get update
  apt-get -y upgrade
  printf '\nChecking Dependencies\n'
  apt-get -y install python3-pip fonts-freefont-ttf sense-hat lighttpd python3-smbus rpi.gpio fake-hwclock
  pip3 install gpiozero envirophat sense_hat bme680 bh1745 lsm303d vl53l1x smbus2
fi
printf '\n'
# Install crontab entries
bash /home/sensors/upgrade/update_crontab.sh
# Make sure permissions are correct
bash /home/sensors/upgrade/update_file_permissions.sh
printf '\nPrinting Config and Testing Sensors\n\n'
killall python3
python3 /home/sensors/test_sensors.py
printf '\nPlease wait up to 60 Seconds for Sensor to come online\n'
