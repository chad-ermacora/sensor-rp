"""
    KootNet Sensors is a collection of programs and scripts to deploy,
    interact with, and collect readings from various Sensors.
    Copyright (C) 2018  Chad Ermacora  chad.ermacora@gmail.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

    This file contains the location of files on the host system.
"""


debug_file_location = "/etc/kootnet/enable_debug_logging.conf"
sensor_database_location = "/home/kootnet_data/SensorRecordingDatabase.sqlite"
config_file_location = "/etc/kootnet/sql_recording.conf"
http_auth_file_location = "/home/kootnet_data/auth.conf"
save_plotly_html_to = "/home/kootnet_data/"
interval_plotly_html_filename = "IntervalPlotlySensorGraph.html"
triggers_plotly_html_filename = "TriggersPlotlySensorGraph.html"
sensors_installed_file_location = "/etc/kootnet/installed_sensors.conf"
trigger_variances_file_location = "/etc/kootnet/trigger_variances.conf"
wifi_config_file = "/etc/wpa_supplicant/wpa_supplicant.conf"

display_font = "/opt/kootnet-sensors/extras/DejaVuSans-Bold.ttf"
j_query_js = "/opt/kootnet-sensors/http_server/extras/jquery-3.4.1.min.js"
mui_min_css = "/opt/kootnet-sensors/http_server/extras/mui.min-ver-0.9.43.css"
mui_colors_min_css = "/opt/kootnet-sensors/http_server/extras/mui-colors.min-ver-0.9.43.css"
mui_min_js = "/opt/kootnet-sensors/http_server/extras/mui.min-ver-0.9.43.js"
menu_script = "/opt/kootnet-sensors/http_server/extras/menu.js"
menu_css_style = "/opt/kootnet-sensors/http_server/extras/style.css"
graph_script = "/opt/kootnet-sensors/http_server/extras/graph_ui.js"

old_version_file_location = "/etc/kootnet/installed_version.txt"
last_updated_file_location = "/etc/kootnet/last_updated.txt"

log_directory = "/home/kootnet_data/logs/"
log_zip_file = log_directory + "all_logs.zip"
primary_log = log_directory + "Primary_log.txt"
network_log = log_directory + "Network_log.txt"
sensors_log = log_directory + "Sensors_log.txt"
