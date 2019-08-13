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
from datetime import datetime
from time import strftime
from flask import render_template
from operations_modules import logger
from operations_modules import configuration_main
from operations_modules import file_locations
from operations_modules import wifi_file
from operations_modules import trigger_variances
from http_server import server_plotly_graph
from http_server.server_http_post_checks import get_html_checkbox_state


class CreateRenderTemplates:
    def __init__(self, sensor_access):
        self.sensor_access = sensor_access
        self.current_config = configuration_main.current_config
        self.installed_sensors = configuration_main.installed_sensors

        configuration_main.cache_hostname = sensor_access.get_hostname()
        configuration_main.cache_ip = sensor_access.get_ip()
        configuration_main.cache_program_last_updated = sensor_access.get_last_updated()
        configuration_main.cache_reboot_count = str(sensor_access.get_system_reboot_count())

    @staticmethod
    def message_and_return(return_message, text_message2="", url="/", special_command=""):
        return render_template("message_return.html",
                               TextMessage=return_message,
                               TextMessage2=text_message2,
                               CloseWindow=special_command,
                               URL=url)

    def index_page(self):
        return render_template("index.html", HostName=self.sensor_access.get_hostname())

    @staticmethod
    def system_management():
        return render_template("system_commands.html")

    @staticmethod
    def logout():
        return render_template("message_return.html",
                               TextMessage="Logout OK.  Returning to Home.",
                               URL="/"), 401

    def system_information(self):
        if configuration_main.current_config.enable_debug_logging:
            debug_logging = True
        else:
            debug_logging = False

        if configuration_main.current_config.enable_display:
            display_enabled = True
        else:
            display_enabled = False

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

        return render_template("sensor_information.html",
                               HostName=configuration_main.cache_hostname,
                               IPAddress=configuration_main.cache_ip,
                               KootnetVersion=configuration_main.software_version.version,
                               LastUpdated=configuration_main.cache_program_last_updated,
                               DateTime=strftime("%Y-%m-%d %H:%M - %Z"),
                               SystemUptime=self.sensor_access.get_uptime_str(),
                               SensorReboots=configuration_main.cache_reboot_count,
                               CPUTemperature=self.sensor_access.get_cpu_temperature(),
                               RAMUsage=self.sensor_access.get_memory_usage_percent(),
                               DiskUsage=self.sensor_access.get_disk_usage_percent(),
                               DebugLogging=debug_logging,
                               SupportedDisplay=display_enabled,
                               IntervalRecording=interval_recording,
                               IntervalDelay=self.current_config.sleep_duration_interval,
                               TriggerRecording=trigger_recording,
                               ManualTemperatureEnabled=custom_temp_enabled,
                               CurrentTemperatureOffset=configuration_main.current_config.temperature_offset,
                               InstalledSensors=configuration_main.installed_sensors.get_installed_names_str(),
                               SQLDatabaseLocation=file_locations.sensor_database_location,
                               SQLDatabaseDateRange=self.sensor_access.get_db_first_last_date(),
                               SQLDatabaseSize=self.sensor_access.get_db_size(),
                               NumberNotes=self.sensor_access.get_db_notes_count())

    def sensors_readings(self):
        red, orange, yellow, green, blue, violet = server_plotly_graph.get_ems_for_render_template(
            self.sensor_access.get_ems())

        return render_template("sensor_readings.html",
                               HostName=configuration_main.cache_hostname,
                               IPAddress=configuration_main.cache_ip,
                               DateTime=strftime("%Y-%m-%d %H:%M - %Z"),
                               SystemUptime=self.sensor_access.get_uptime_str(),
                               CPUTemperature=self.sensor_access.get_cpu_temperature(),
                               EnvTemperature=self.sensor_access.get_sensor_temperature(),
                               EnvTemperatureOffset=configuration_main.current_config.temperature_offset,
                               Pressure=self.sensor_access.get_pressure(),
                               Altitude=self.sensor_access.get_altitude(),
                               Humidity=self.sensor_access.get_humidity(),
                               Distance=self.sensor_access.get_distance(),
                               GasResistanceIndex=self.sensor_access.get_gas_resistance_index(),
                               GasOxidising=self.sensor_access.get_gas_oxidised(),
                               GasReducing=self.sensor_access.get_gas_reduced(),
                               GasNH3=self.sensor_access.get_gas_nh3(),
                               PM1=self.sensor_access.get_particulate_matter_1(),
                               PM25=self.sensor_access.get_particulate_matter_2_5(),
                               PM10=self.sensor_access.get_particulate_matter_10(),
                               Lumen=self.sensor_access.get_lumen(),
                               Red=red,
                               Orange=orange,
                               Yellow=yellow,
                               Green=green,
                               Blue=blue,
                               Violet=violet,
                               UVA=self.sensor_access.get_ultra_violet_a(),
                               UVB=self.sensor_access.get_ultra_violet_b(),
                               Acc=self.sensor_access.get_accelerometer_xyz(),
                               Mag=self.sensor_access.get_magnetometer_xyz(),
                               Gyro=self.sensor_access.get_gyroscope_xyz())

    def edit_configurations(self):
        try:
            text_variance_triggers = trigger_variances.convert_triggers_to_str(
                configuration_main.trigger_variances)
            text_wifi_config = wifi_file.get_wifi_config_from_file()

            debug_logging = get_html_checkbox_state(self.current_config.enable_debug_logging)
            display = get_html_checkbox_state(self.current_config.enable_display)
            interval_recording = get_html_checkbox_state(self.current_config.enable_interval_recording)
            trigger_recording = get_html_checkbox_state(self.current_config.enable_trigger_recording)
            custom_temp_offset = get_html_checkbox_state(self.current_config.enable_custom_temp)

            return render_template("edit_configurations.html",
                                   PageURL="/ConfigurationsHTML",
                                   CheckedDebug=debug_logging,
                                   CheckedDisplay=display,
                                   CheckedInterval=interval_recording,
                                   IntervalDelay=int(configuration_main.current_config.sleep_duration_interval),
                                   CheckedTrigger=trigger_recording,
                                   CheckedCustomTempOffset=custom_temp_offset,
                                   temperature_offset=int(configuration_main.current_config.temperature_offset),
                                   GnuLinux=get_html_checkbox_state(self.installed_sensors.linux_system),
                                   RPIZeroW=get_html_checkbox_state(self.installed_sensors.raspberry_pi_zero_w),
                                   RPI3BPlus=get_html_checkbox_state(self.installed_sensors.raspberry_pi_3b_plus),
                                   SenseHAT=get_html_checkbox_state(self.installed_sensors.raspberry_pi_sense_hat),
                                   PimoroniBH1745=get_html_checkbox_state(self.installed_sensors.pimoroni_bh1745),
                                   PimoroniAS7262=get_html_checkbox_state(self.installed_sensors.pimoroni_as7262),
                                   PimoroniBMP280=get_html_checkbox_state(self.installed_sensors.pimoroni_bmp280),
                                   PimoroniBME680=get_html_checkbox_state(self.installed_sensors.pimoroni_bme680),
                                   PimoroniEnviroPHAT=get_html_checkbox_state(self.installed_sensors.pimoroni_enviro),
                                   PimoroniEnviroPlus=get_html_checkbox_state(
                                       self.installed_sensors.pimoroni_enviroplus),
                                   PimoroniPMS5003=get_html_checkbox_state(self.installed_sensors.pimoroni_pms5003),
                                   PimoroniLSM303D=get_html_checkbox_state(self.installed_sensors.pimoroni_lsm303d),
                                   PimoroniICM20948=get_html_checkbox_state(self.installed_sensors.pimoroni_icm20948),
                                   PimoroniVL53L1X=get_html_checkbox_state(self.installed_sensors.pimoroni_vl53l1x),
                                   PimoroniLTR559=get_html_checkbox_state(self.installed_sensors.pimoroni_ltr_559),
                                   PimoroniVEML6075=get_html_checkbox_state(self.installed_sensors.pimoroni_veml6075),
                                   Pimoroni11x7LEDMatrix=get_html_checkbox_state(
                                       self.installed_sensors.pimoroni_matrix_11x7),
                                   PimoroniSPILCD10_96=get_html_checkbox_state(self.installed_sensors.pimoroni_st7735),
                                   PimoroniMonoOLED128x128BW=get_html_checkbox_state(
                                       self.installed_sensors.pimoroni_mono_oled_luma),
                                   VariancesTitle="Trigger Variances",
                                   VariancesConfig=text_variance_triggers,
                                   WiFiTitle="WiFi Configuration (GNU/Linux WPA Supplicant)",
                                   WiFiConfig=text_wifi_config)
        except Exception as error:
            logger.network_logger.error("Stuff broke!: " + str(error))

    def get_log_view(self):
        primary_log_lines = logger.get_number_of_log_entries(file_locations.primary_log)
        network_log_lines = logger.get_number_of_log_entries(file_locations.network_log)
        sensors_log_lines = logger.get_number_of_log_entries(file_locations.sensors_log)
        return render_template("log_view.html",
                               LogURL="/GetLogsHTML",
                               PrimaryLog=logger.get_sensor_log(file_locations.primary_log),
                               PrimaryLogLinesText=self._get_log_view_message(primary_log_lines),
                               NetworkLog=logger.get_sensor_log(file_locations.network_log),
                               NetworkLogLinesText=self._get_log_view_message(network_log_lines),
                               SensorsLog=logger.get_sensor_log(file_locations.sensors_log),
                               SensorsLogLinesText=self._get_log_view_message(sensors_log_lines))

    @staticmethod
    def _get_log_view_message(log_lines_length):
        if log_lines_length:
            if logger.max_log_lines_return > log_lines_length:
                text_log_entries_return = str(log_lines_length) + "/" + str(log_lines_length)
            else:
                text_log_entries_return = str(logger.max_log_lines_return) + "/" + str(log_lines_length)
        else:
            text_log_entries_return = "0/0"
        return text_log_entries_return

    @staticmethod
    def plotly_graph_main():
        try:
            interval_plotly_file_creation_date_unix = os.path.getmtime(file_locations.save_plotly_html_to +
                                                                       file_locations.interval_plotly_html_filename)
            interval_creation_date = str(datetime.fromtimestamp(interval_plotly_file_creation_date_unix))[:-7]
        except Exception as error:
            logger.primary_logger.debug("No Interval Plotly file created: " + str(error))
            interval_creation_date = "No Plotly Graph Found"

        try:
            triggers_plotly_file_creation_date_unix = os.path.getmtime(file_locations.save_plotly_html_to +
                                                                       file_locations.triggers_plotly_html_filename)
            triggers_creation_date = str(datetime.fromtimestamp(triggers_plotly_file_creation_date_unix))[:-7]
        except Exception as error:
            logger.primary_logger.debug("No Triggers Plotly file: " + str(error))
            triggers_creation_date = "No Plotly Graph Found"

        return render_template("plotly_graph.html",
                               IntervalPlotlyCreationDate=interval_creation_date,
                               TriggerPlotlyCreationDate=triggers_creation_date)
