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
"""
import os
from threading import Thread
from flask import Flask, request, send_file, render_template
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash
from gevent import pywsgi
from html_files import page_quick
from html_files import page_sensor_readings
from operations_modules import wifi_file
from operations_modules import trigger_variances
from operations_modules import file_locations
from operations_modules import logger
from operations_modules import configuration_main
from operations_modules import software_version
from operations_modules import app_variables
from operations_modules import configuration_files
from operations_modules import server_http_auth


class CreateSensorHTTP:
    def __init__(self, sensor_access):
        self.app = Flask(__name__)
        self.auth = HTTPBasicAuth()
        http_auth = server_http_auth.CreateHTTPAuth()
        http_auth.set_http_auth_from_file()

        @self.app.route("/")
        @self.app.route("/index")
        @self.app.route("/Ver")
        @self.app.route("/About")
        def index():
            return render_template("index.html",
                                   KootnetVersion=software_version.version,
                                   InstalledSensors=configuration_main.installed_sensors.get_installed_names_str())

        @self.app.route("/mui.min.css")
        def mui_min_css():
            return send_file(file_locations.mui_min_css)

        @self.app.route("/mui.min.js")
        def mui_min_js():
            return send_file(file_locations.mui_min_js)

        @self.auth.verify_password
        def verify_password(username, password):
            if username == http_auth.http_flask_user:
                return check_password_hash(http_auth.http_flask_password, password)
            else:
                return False

        @self.app.route("/Quick")
        def quick_links():
            logger.network_logger.info("Quick Links accessed from " + str(request.remote_addr))
            if configuration_main.current_config.enable_debug_logging:
                debug_logging = True
            else:
                debug_logging = False

            if configuration_main.current_config.enable_interval_recording:
                interval_recording = True
            else:
                interval_recording = False

            if configuration_main.current_config.enable_trigger_recording:
                trigger_recording = True
            else:
                trigger_recording = False

            if configuration_main.current_config.enable_custom_temp:
                custom_temp_enabled = True
            else:
                custom_temp_enabled = False

            return render_template("quick.html",
                                   HostName=sensor_access.get_hostname(),
                                   IPAddress=sensor_access.get_ip(),
                                   CPUTemperature=sensor_access.get_cpu_temperature(),
                                   SQLDatabaseSize=sensor_access.get_db_size(),
                                   DiskUsage=sensor_access.get_disk_usage_percent(),
                                   RAMUsage=sensor_access.get_memory_usage_percent(),
                                   DateTime=sensor_access.get_system_datetime(),
                                   SystemUptime=sensor_access.get_uptime_minutes(),
                                   InstalledSensors=configuration_main.installed_sensors.get_installed_names_str(),
                                   KootnetVersion=configuration_main.software_version.version,
                                   LastUpdated=sensor_access.get_last_updated(),
                                   DebugLogging=debug_logging,
                                   IntervalRecording=interval_recording,
                                   TriggerRecording=trigger_recording,
                                   ManualTemperatureEnabled=custom_temp_enabled,
                                   CurrentTemperatureOffset=configuration_main.current_config.temperature_offset,
                                   IntervalDelay=configuration_main.current_config.sleep_duration_interval)

        @self.app.route("/TestSensor")
        def test_sensor():
            return page_sensor_readings.get_sensor_readings_page()

        @self.app.route("/CheckOnlineStatus")
        def check_online():
            logger.network_logger.debug("Sensor Checked by " + str(request.remote_addr))
            return "OK"

        @self.app.route("/GetSensorReadings")
        def get_sensor_readings():
            logger.network_logger.info("* Sent Sensor Readings")
            sensor_readings = sensor_access.get_sensor_readings()
            return_str = str(sensor_readings[0]) + "," + str(sensor_readings[1])
            return return_str

        @self.app.route("/GetSystemData")
        def get_system_data():
            logger.network_logger.info("* Sensor Data Sent to " + str(request.remote_addr))
            return sensor_access.get_system_information()

        @self.app.route("/GetConfigurationReport")
        def get_configuration_report():
            logger.network_logger.info("* Sensor Data Sent to " + str(request.remote_addr))
            return sensor_access.get_config_information()

        @self.app.route("/GetInstalledSensors")
        def get_installed_sensors():
            logger.network_logger.info("* Sent Installed Sensors")
            installed_sensors_str = configuration_main.installed_sensors.get_installed_sensors_config_as_str()
            return installed_sensors_str

        @self.app.route("/GetConfiguration")
        def get_configuration():
            logger.network_logger.info("* Sent Sensors Configuration")
            installed_config_str = configuration_files.convert_config_to_str(configuration_main.current_config)
            return installed_config_str

        @self.app.route("/GetWifiConfiguration")
        @self.auth.login_required
        def get_wifi_config():
            logger.network_logger.info("* Sent wpa_supplicant")
            return send_file(file_locations.wifi_config_file)

        @self.app.route("/SetWifiConfiguration", methods=["PUT"])
        @self.auth.login_required
        def set_wifi_config():
            try:
                new_wifi_config = request.form['command_data']
                wifi_file.write_wifi_config_to_file(new_wifi_config)
                logger.network_logger.info("* wpa_supplicant Changed - OK")
            except Exception as error:
                logger.network_logger.warning("* wpa_supplicant Change - Failed: " + str(error))
            return "OK"

        @self.app.route("/GetVarianceConfiguration")
        def get_variance_config():
            logger.network_logger.info("* Sent Variance Configuration")
            return send_file(file_locations.trigger_variances_file_location)

        @self.app.route("/SetVarianceConfiguration", methods=["PUT"])
        @self.auth.login_required
        def set_variance_config():
            try:
                new_variance_config = request.form['command_data']
                trigger_variances.write_triggers_to_file(new_variance_config)
                logger.network_logger.info("* wpa_supplicant Changed - OK")
            except Exception as error:
                logger.network_logger.warning("* wpa_supplicant Change - Failed: " + str(error))

            sensor_access.restart_services()
            return "OK"

        @self.app.route("/GetPrimaryLog")
        def get_primary_log():
            logger.network_logger.info("* Sent Primary Log")
            log = logger.get_sensor_log(file_locations.primary_log)
            if len(log) > 1150:
                log = log[:1150]
            return log

        @self.app.route("/GetPrimaryLogHTML")
        def get_primary_log_html():
            logger.network_logger.info("* Sent Primary Log in HTML format")
            log = logger.get_sensor_log_html(file_locations.primary_log)
            return log

        @self.app.route("/GetNetworkLog")
        def get_network_log():
            logger.network_logger.info("* Sent Network Log")
            log = logger.get_sensor_log(file_locations.network_log)
            if len(log) > 1150:
                log = log[:1150]
            return log

        @self.app.route("/GetNetworkLogHTML")
        def get_network_log_html():
            logger.network_logger.info("* Sent Network Log in HTML format")
            log = logger.get_sensor_log_html(file_locations.network_log)
            return log

        @self.app.route("/GetSensorsLog")
        def get_sensors_log():
            logger.network_logger.info("* Sent Sensor Log")
            log = logger.get_sensor_log(file_locations.sensors_log)
            if len(log) > 1150:
                log = log[:1150]
            return log

        @self.app.route("/GetSensorsLogHTML")
        def get_sensors_log_html():
            logger.network_logger.info("* Sent Sensor Log in HTML format")
            log = logger.get_sensor_log_html(file_locations.sensors_log)
            return log

        @self.app.route("/GetDatabaseNotes")
        def get_db_notes():
            logger.network_logger.info("* Sent Sensor Notes")
            return sensor_access.get_db_notes()

        @self.app.route("/DeletePrimaryLog")
        @self.auth.login_required
        def delete_primary_log():
            logger.network_logger.info("* Primary Sensor Log Deleted")
            logger.clear_primary_log()

        @self.app.route("/DeleteNetworkLog")
        @self.auth.login_required
        def delete_network_log():
            logger.network_logger.info("* Network Sensor Log Deleted")
            logger.clear_network_log()

        @self.app.route("/DeleteSensorsLog")
        @self.auth.login_required
        def delete_sensors_log():
            logger.network_logger.info("* Sensors Log Deleted")
            logger.clear_sensor_log()

        @self.app.route("/GetDatabaseNoteDates")
        def get_db_note_dates():
            logger.network_logger.info("* Sent Sensor Note Dates")
            return sensor_access.get_db_note_dates()

        @self.app.route("/GetDatabaseNoteUserDates")
        def get_db_note_user_dates():
            logger.network_logger.info("* Sent Sensor Note User Set Dates")
            return sensor_access.get_db_note_user_dates()

        @self.app.route("/DeleteDatabaseNote", methods=["PUT"])
        @self.auth.login_required
        def del_db_note():
            note_datetime = request.form['command_data']
            logger.network_logger.info("* Deleted Note from: " + str(note_datetime))
            sensor_access.delete_db_note(note_datetime)

        @self.app.route("/DownloadPrimaryLog")
        def download_primary_log():
            logger.network_logger.info("* Sent Full Primary Log")
            log_name = sensor_access.get_ip()[-3:].replace(".", "_") + sensor_access.get_hostname() + "PrimaryLog.txt"
            return send_file(file_locations.primary_log, as_attachment=True, attachment_filename=log_name)

        @self.app.route("/DownloadNetworkLog")
        def download_network_log():
            logger.network_logger.info("* Sent Full Network Log")
            log_name = sensor_access.get_ip()[-3:].replace(".", "_") + sensor_access.get_hostname() + "NetworkLog.txt"
            return send_file(file_locations.network_log, as_attachment=True, attachment_filename=log_name)

        @self.app.route("/DownloadSensorsLog")
        def download_sensors_log():
            logger.network_logger.info("* Sent Full Sensor Log")
            log_name = sensor_access.get_ip()[-3:].replace(".", "_") + sensor_access.get_hostname() + "SensorLog.txt"
            return send_file(file_locations.sensors_log, as_attachment=True, attachment_filename=log_name)

        @self.app.route("/DownloadSQLDatabase")
        def download_sensors_sql_database():
            logger.network_logger.info("* Sent Sensor SQL Database")
            sql_filename = sensor_access.get_ip()[-3:].replace(".", "_") + sensor_access.get_hostname() + "SensorDatabase.sqlite"
            return send_file(file_locations.sensor_database_location, as_attachment=True, attachment_filename=sql_filename)

        @self.app.route("/PutDatabaseNote", methods=["PUT"])
        @self.auth.login_required
        def put_sql_note():
            new_note = request.form['command_data']
            sensor_access.add_note_to_database(new_note)
            logger.network_logger.info("* Inserted Note into Database")
            return "OK"

        @self.app.route("/UpdateDatabaseNote", methods=["PUT"])
        @self.auth.login_required
        def update_sql_note():
            datetime_entry_note_csv = request.form['command_data']
            sensor_access.update_note_in_database(datetime_entry_note_csv)
            logger.network_logger.info("* Updated Note in Database")
            return "OK"

        @self.app.route("/UpgradeOnline")
        @self.auth.login_required
        def upgrade_http():
            logger.network_logger.info("* Started Upgrade - HTTP")
            os.system(app_variables.bash_commands["UpgradeOnline"])
            return "HTTP Upgrade Started.  This may take a few minutes ..."

        @self.app.route("/CleanOnline")
        @self.auth.login_required
        def upgrade_clean_http():
            logger.network_logger.info("* Started Clean Upgrade - HTTP")
            os.system(app_variables.bash_commands["CleanOnline"])
            return "HTTP Clean Upgrade Started.  This may take a few minutes ..."

        @self.app.route("/UpgradeOnlineDev")
        @self.auth.login_required
        def upgrade_http_dev():
            logger.network_logger.info("* Started Upgrade - HTTP Developer")
            os.system(app_variables.bash_commands["UpgradeOnlineDEV"])
            return "HTTP Developer Upgrade Started.  This may take a few minutes ..."

        @self.app.route("/UpgradeSMB")
        @self.auth.login_required
        def upgrade_smb():
            logger.network_logger.info("* Started Upgrade - SMB")
            os.system(app_variables.bash_commands["UpgradeSMB"])
            return "SMB Upgrade Started.  This may take a few minutes ..."

        @self.app.route("/CleanSMB")
        @self.auth.login_required
        def upgrade_clean_smb():
            logger.network_logger.info("* Started Clean Upgrade - SMB")
            os.system(app_variables.bash_commands["CleanSMB"])
            return "SMB Clean Upgrade Started.  This may take a few minutes ..."

        @self.app.route("/UpgradeSMBDev")
        @self.auth.login_required
        def upgrade_smb_dev():
            logger.network_logger.info("* Started Upgrade - SMB Developer")
            os.system(app_variables.bash_commands["UpgradeSMBDEV"])
            return "SMB Developer Upgrade Started.  This may take a few minutes ..."

        @self.app.route("/ReInstallRequirements")
        @self.auth.login_required
        def reinstall_program_requirements():
            logger.network_logger.info("* Started Program Dependency Install")
            os.system(app_variables.bash_commands["ReInstallRequirements"])
            return "Dependency Install Started.  This may take a few minutes ..."

        @self.app.route("/UpgradeSystemOS")
        @self.auth.login_required
        def upgrade_system_os():
            logger.network_logger.info("* Updating Operating System & rebooting")
            if configuration_main.linux_os_upgrade_ready:
                configuration_main.linux_os_upgrade_ready = False
                system_upgrade_thread = Thread(target=sensor_access.upgrade_linux_os)
                system_upgrade_thread.daemon = True
                system_upgrade_thread.start()
            else:
                logger.sensors_logger.warning("* Operating System Upgrade Already Running")
            return "OK"

        @self.app.route("/inkupg")
        @self.auth.login_required
        def upgrade_rp_controller():
            logger.network_logger.info("* Started Upgrade - E-Ink Mobile")
            os.system(app_variables.bash_commands["inkupg"])
            return "OK"

        @self.app.route("/RebootSystem")
        @self.auth.login_required
        def system_reboot():
            logger.network_logger.info("* Rebooting System")
            os.system(app_variables.bash_commands["RebootSystem"])

        @self.app.route("/ShutdownSystem")
        @self.auth.login_required
        def system_shutdown():
            logger.network_logger.info("* System Shutdown started by " + str(request.remote_addr))
            os.system(app_variables.bash_commands["ShutdownSystem"])

        @self.app.route("/RestartServices")
        def services_restart():
            logger.network_logger.info("* Service restart started by " + str(request.remote_addr))
            sensor_access.restart_services()

        @self.app.route("/SetHostName", methods=["PUT"])
        @self.auth.login_required
        def set_hostname():
            try:
                new_host = request.form['command_data']
                os.system("hostnamectl set-hostname " + new_host)
                logger.network_logger.info("* Hostname Changed to " + new_host + " - OK")
            except Exception as error:
                logger.network_logger.warning("* Hostname Change Failed: " + str(error))
            return "OK"

        @self.app.route("/SetDateTime", methods=["PUT"])
        @self.auth.login_required
        def set_date_time():
            new_datetime = request.form['command_data']
            os.system("date --set " + new_datetime[:10] + " && date --set " + new_datetime[11:])
            logger.network_logger.info("* Set System DateTime: " + new_datetime)
            return "OK"

        @self.app.route("/SetConfiguration", methods=["PUT"])
        @self.auth.login_required
        def set_configuration():
            logger.network_logger.info("* Setting Sensor Configuration")

            raw_config = request.form['command_data'].splitlines()
            new_config = configuration_files.convert_config_lines_to_obj(raw_config)
            configuration_files.write_config_to_file(new_config)
            sensor_access.restart_services()
            return "OK"

        @self.app.route("/SetInstalledSensors", methods=["PUT"])
        @self.auth.login_required
        def set_installed_sensors():
            logger.network_logger.info("* Setting Sensor Installed Sensors")
            raw_installed_sensors = request.form['command_data'].splitlines()
            new_installed_sensors = configuration_files.convert_installed_sensors_lines_to_obj(raw_installed_sensors)
            configuration_files.write_installed_sensors_to_file(new_installed_sensors)
            sensor_access.restart_services()
            return "OK"

        @self.app.route("/GetHostName")
        def get_hostname():
            logger.network_logger.debug("* Sent Sensor HostName")
            return str(sensor_access.get_hostname())

        @self.app.route("/GetSystemUptime")
        def get_system_uptime():
            logger.network_logger.debug("* Sent Sensor System Uptime")
            return str(sensor_access.get_system_uptime())

        @self.app.route("/GetCPUTemperature")
        def get_cpu_temperature():
            logger.network_logger.debug("* Sent Sensor CPU Temperature")
            return str(sensor_access.get_cpu_temperature())

        @self.app.route("/GetEnvTemperature")
        def get_env_temperature():
            logger.network_logger.debug("* Sent Sensor Environment Temperature")
            return str(sensor_access.get_sensor_temperature())

        @self.app.route("/GetTempOffsetEnv")
        def get_env_temp_offset():
            logger.network_logger.debug("* Sent Sensor Env Temperature Offset")
            return str(configuration_main.current_config.temperature_offset)

        @self.app.route("/GetPressure")
        def get_pressure():
            logger.network_logger.debug("* Sent Sensor Pressure")
            return str(sensor_access.get_pressure())

        @self.app.route("/GetAltitude")
        def get_altitude():
            logger.network_logger.debug("* Sent Sensor Altitude")
            return str(sensor_access.get_altitude())

        @self.app.route("/GetHumidity")
        def get_humidity():
            logger.network_logger.debug("* Sent Sensor Humidity")
            return str(sensor_access.get_humidity())

        @self.app.route("/GetDistance")
        def get_distance():
            logger.network_logger.debug("* Sent Sensor Distance")
            return str(sensor_access.get_distance())

        @self.app.route("/GetAllGas")
        def get_all_gas():
            logger.network_logger.debug("* Sent All GAS Sensors")
            gas_return = [sensor_access.get_gas_resistance_index(),
                          sensor_access.get_gas_oxidised(),
                          sensor_access.get_gas_reduced(),
                          sensor_access.get_gas_nh3()]
            return str(gas_return)

        @self.app.route("/GetGasResistanceIndex")
        def get_gas_resistance_index():
            logger.network_logger.debug("* Sent Sensor GAS Resistance Index")
            return str(sensor_access.get_gas_resistance_index())

        @self.app.route("/GetGasOxidised")
        def get_gas_oxidised():
            logger.network_logger.debug("* Sent Sensor GAS Oxidised")
            return str(sensor_access.get_gas_oxidised())

        @self.app.route("/GetGasReduced")
        def get_gas_reduced():
            logger.network_logger.debug("* Sent Sensor GAS Reduced")
            return str(sensor_access.get_gas_reduced())

        @self.app.route("/GetGasNH3")
        def get_gas_nh3():
            logger.network_logger.debug("* Sent Sensor GAS NH3")
            return str(sensor_access.get_gas_nh3())

        @self.app.route("/GetAllParticulateMatter")
        def get_all_particulate_matter():
            logger.network_logger.debug("* Sent All Particulate Matter Sensors")
            return_pm = [sensor_access.get_particulate_matter_1(),
                         sensor_access.get_particulate_matter_2_5(),
                         sensor_access.get_particulate_matter_10()]

            return str(return_pm)

        @self.app.route("/GetParticulateMatter1")
        def get_particulate_matter_1():
            logger.network_logger.debug("* Sent Sensor Particulate Matter 1")
            return str(sensor_access.get_particulate_matter_1())

        @self.app.route("/GetParticulateMatter2_5")
        def get_particulate_matter_2_5():
            logger.network_logger.debug("* Sent Sensor Particulate Matter 2.5")
            return str(sensor_access.get_particulate_matter_2_5())

        @self.app.route("/GetParticulateMatter10")
        def get_particulate_matter_10():
            logger.network_logger.debug("* Sent Sensor Particulate Matter 10")
            return str(sensor_access.get_particulate_matter_10())

        @self.app.route("/GetLumen")
        def get_lumen():
            logger.network_logger.debug("* Sent Sensor Lumen")
            return str(sensor_access.get_lumen())

        @self.app.route("/GetEMS")
        def get_ems():
            logger.network_logger.debug("* Sent Sensor Electromagnetic Spectrum")
            return str(sensor_access.get_ems())

        @self.app.route("/GetAllUltraViolet")
        def get_all_ultra_violet():
            logger.network_logger.debug("* Sent All Ultra Violet Sensors")
            return_ultra_violet = [sensor_access.get_ultra_violet_a(), sensor_access.get_ultra_violet_b()]
            return str(return_ultra_violet)

        @self.app.route("/GetUltraVioletA")
        def get_ultra_violet_a():
            logger.network_logger.debug("* Sent Sensor Ultra Violet A")
            return str(sensor_access.get_ultra_violet_a())

        @self.app.route("/GetUltraVioletB")
        def get_ultra_violet_b():
            logger.network_logger.debug("* Sent Sensor Ultra Violet B")
            return str(sensor_access.get_ultra_violet_b())

        @self.app.route("/GetAccelerometerXYZ")
        def get_acc_xyz():
            logger.network_logger.debug("* Sent Sensor Accelerometer XYZ")
            return str(sensor_access.get_accelerometer_xyz())

        @self.app.route("/GetMagnetometerXYZ")
        def get_mag_xyz():
            logger.network_logger.debug("* Sent Sensor Magnetometer XYZ")
            return str(sensor_access.get_magnetometer_xyz())

        @self.app.route("/GetGyroscopeXYZ")
        def get_gyro_xyz():
            logger.network_logger.debug("* Sent Sensor Gyroscope XYZ")
            return str(sensor_access.get_gyroscope_xyz())

        @self.app.route("/GetIntervalSensorReadings")
        def get_interval_readings():
            logger.network_logger.debug("* Sent Interval Sensor Readings")
            return str(sensor_access.get_interval_sensor_readings())

        @self.app.route("/DisplayText", methods=["PUT"])
        @self.auth.login_required
        def display_text():
            if configuration_main.current_config.enable_display and configuration_main.installed_sensors.has_display:
                logger.network_logger.info("* Displaying Text on Installed Display")
                text_message = request.form['command_data']
                sensor_access.display_message(text_message)
            else:
                logger.network_logger.warning("* Unable to Display Text: Sensor Display Disabled or not installed")

        logger.network_logger.info("** starting up on port " + str(app_variables.flask_http_port) + " **")
        http_server = pywsgi.WSGIServer((app_variables.flask_http_ip, app_variables.flask_http_port), self.app)
        logger.primary_logger.info("HTTP Server Started")
        http_server.serve_forever()
