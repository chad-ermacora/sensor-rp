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
import time
import requests
from threading import Thread
from queue import Queue
from flask import render_template
from operations_modules import logger
from operations_modules import file_locations
from operations_modules import app_cached_variables
from operations_modules import app_generic_functions
from configuration_modules import app_config_access
from configuration_modules.config_primary import CreatePrimaryConfiguration
from configuration_modules.config_installed_sensors import CreateInstalledSensorsConfiguration
from configuration_modules.config_interval_recording import CreateIntervalRecordingConfiguration
from configuration_modules.config_trigger_variances import CreateTriggerVariancesConfiguration
from configuration_modules.config_trigger_high_low import CreateTriggerHighLowConfiguration
from configuration_modules.config_display import CreateDisplayConfiguration
from configuration_modules.config_email import CreateEmailConfiguration
from http_server.server_http_generic_functions import get_html_hidden_state, message_and_return
from http_server.flask_blueprints.sensor_control_files.reports import generate_sensor_control_report

network_commands = app_cached_variables.CreateNetworkGetCommands()

initial_primary_select = CreatePrimaryConfiguration(load_from_file=False).get_config_as_str()
default_primary_config = CreatePrimaryConfiguration(load_from_file=False).get_config_as_str()
default_primary_config = default_primary_config.replace("\n", "\\n")
default_installed_sensors_config = CreateInstalledSensorsConfiguration(load_from_file=False).get_config_as_str()
default_installed_sensors_config = default_installed_sensors_config.replace("\n", "\\n")
default_interval_recording_config = CreateIntervalRecordingConfiguration(load_from_file=False).get_config_as_str()
default_interval_recording_config = default_interval_recording_config.replace("\n", "\\n")
default_variance_config = CreateTriggerVariancesConfiguration(load_from_file=False).get_config_as_str()
default_variance_config = default_variance_config.replace("\n", "\\n")
default_high_low_config = CreateTriggerHighLowConfiguration(load_from_file=False).get_config_as_str()
default_high_low_config = default_high_low_config.replace("\n", "\\n")
default_display_config = CreateDisplayConfiguration(load_from_file=False).get_config_as_str()
default_display_config = default_display_config.replace("\n", "\\n")
default_email_config = CreateEmailConfiguration(load_from_file=False).get_config_as_str()
default_email_config = default_email_config.replace("\n", "\\n")
default_wifi_config = "# https://manpages.debian.org/stretch/wpasupplicant/wpa_supplicant.conf.5.en.html"
default_network_config = "# https://manpages.debian.org/testing/dhcpcd5/dhcpcd.conf.5.en.html"


class CreateSensorHTTPCommand:
    """ Creates Object to use for Sending a command and optional data to a remote sensor. """

    def __init__(self, sensor_address, command, command_data=None):
        if command_data is None:
            self.sensor_command_data = {"NotSet": True}
        else:
            self.sensor_command_data = command_data

        self.sensor_address = sensor_address
        self.http_port = "10065"
        self.sensor_command = command
        self._check_ip_port()

    def send_http_command(self):
        """ Sends command and data to sensor. """
        try:
            url = "https://" + self.sensor_address + ":" + self.http_port + "/" + self.sensor_command
            requests.post(url=url, timeout=5, verify=False, data=self.sensor_command_data,
                          auth=(app_cached_variables.http_login, app_cached_variables.http_password))
        except Exception as error:
            logger.network_logger.error("Unable to send command to " + str(self.sensor_address) + ": " + str(error))

    def _check_ip_port(self):
        if app_generic_functions.check_for_port_in_address(self.sensor_address):
            ip_and_port = app_generic_functions.get_ip_and_port_split(self.sensor_address)
            self.sensor_address = ip_and_port[0]
            self.http_port = ip_and_port[1]


def check_sensor_status_sensor_control(address_list):
    """
    Uses provided remote sensor IP or DNS addresses (as a list) and checks if it's online.
    Returns a flask rendered template with results as an HTML page.
    """
    data_queue = Queue()

    text_insert = ""
    threads = []
    for address in address_list:
        threads.append(Thread(target=get_remote_sensor_check_and_delay, args=[address, data_queue, True]))
    app_generic_functions.start_and_wait_threads(threads)

    address_responses = []
    while not data_queue.empty():
        address_responses.append(data_queue.get())
        data_queue.task_done()

    address_responses = sorted(address_responses, key=lambda i: i['address'])
    for response in address_responses:
        new_address = response["address"]
        port = "10065"
        if app_generic_functions.check_for_port_in_address(response["address"]):
            address_split = app_generic_functions.get_ip_and_port_split(response["address"])
            new_address = address_split[0]
            port = address_split[1]
        response_time = response["response_time"]
        background_colour = app_generic_functions.get_response_bg_colour(response_time)
        sensor_url_link = "'https://" + new_address + ":" + port + "/SensorInformation'"

        text_insert += "        <tr><th><span style='background-color: #f2f2f2;'><a target='_blank' href=" + \
                       sensor_url_link + ">" + response["address"] + "</a></span></th>\n" + \
                       "        <th><span style='background-color: " + background_colour + ";'>" + \
                       response_time + " Seconds</span></th>\n" + \
                       "        <th><span style='background-color: #f2f2f2;'>" + \
                       response["sensor_hostname"] + "</span></th></tr>\n"
    return render_template("sensor_control_online_status.html",
                           PageURL="/SensorControlManage",
                           RestartServiceHidden=get_html_hidden_state(app_cached_variables.html_service_restart),
                           RebootSensorHidden=get_html_hidden_state(app_cached_variables.html_sensor_reboot),
                           SensorResponse=text_insert.strip())


def create_all_databases_zipped(ip_list):
    """
    Downloads remote sensor databases from provided IP or DNS addresses (as a list)
    then creates a single zip file for download off the local web portal.
    """
    data_queue = Queue()

    try:
        _queue_name_and_file_list(ip_list, data_queue, command=network_commands.sensor_sql_database)

        data_list = get_data_queue_items(data_queue)
        database_names = []
        sensors_database = []
        for sensor_data in data_list:
            db_name = sensor_data[0].split(".")[-1] + "_" + sensor_data[1] + ".zip"
            database_names.append(db_name)
            sensors_database.append(sensor_data[2])

        write_to_memory = app_generic_functions.save_to_memory_ok(get_sum_db_sizes(ip_list))
        if write_to_memory:
            app_generic_functions.clear_zip_names()
            app_cached_variables.sc_databases_zip_in_memory = True
            app_cached_variables.sc_in_memory_zip = app_generic_functions.zip_files(database_names, sensors_database)
        else:
            app_cached_variables.sc_databases_zip_in_memory = False
            app_generic_functions.zip_files(database_names,
                                            sensors_database,
                                            save_type="save_to_disk",
                                            file_location=file_locations.html_sensor_control_databases_zip)
        app_cached_variables.sc_databases_zip_name = "Multiple_Databases_" + str(time.time())[:-8] + ".zip"
    except Exception as error:
        logger.network_logger.error("Sensor Control - Databases Zip Generation Error: " + str(error))
        app_cached_variables.sc_databases_zip_name = ""
    app_cached_variables.creating_databases_zip = False
    logger.network_logger.info("Sensor Control - Databases Zip Generation Complete")


def create_multiple_sensor_logs_zipped(ip_list):
    """
    Downloads remote sensor logs from provided IP or DNS addresses (as a list)
    then creates a single zip file for download off the local web portal.
    """
    data_queue = Queue()
    try:
        _queue_name_and_file_list(ip_list, data_queue, command=network_commands.download_zipped_logs)

        data_list = get_data_queue_items(data_queue)
        database_names = []
        sensors_database = []
        for sensor_data in data_list:
            db_name = sensor_data[0].split(".")[-1] + "_" + sensor_data[1] + ".zip"
            database_names.append(db_name)
            sensors_database.append(sensor_data[2])

        app_generic_functions.clear_zip_names()
        app_cached_variables.sc_in_memory_zip = app_generic_functions.zip_files(database_names, sensors_database)
        app_cached_variables.sc_logs_zip_name = "Multiple_Logs_" + str(time.time())[:-8] + ".zip"
    except Exception as error:
        logger.network_logger.error("Sensor Control - Logs Zip Generation Error: " + str(error))
        app_cached_variables.sc_logs_zip_name = ""
    app_cached_variables.creating_logs_zip = False
    logger.network_logger.info("Sensor Control - Multi Sensors Logs Zip Generation Complete")


def get_remote_sensor_check_and_delay(address, data_queue, add_hostname=False, add_db_size=False, add_logs_size=False):
    """
    Checks a remote sensor's response time and add's it to the data_queue
    Optional: Include hostname, database size and zipped log size.
    """
    get_sensor_reading = app_generic_functions.get_http_sensor_reading
    task_start_time = time.time()
    sensor_status = get_sensor_reading(address, timeout=5)
    task_end_time = round(time.time() - task_start_time, 3)
    if sensor_status == "OK":
        sensor_hostname = ""
        download_size = "NA"
        if add_hostname:
            sensor_hostname = get_sensor_reading(address, command="GetHostName").strip()
        if add_db_size:
            download_size = get_sensor_reading(address, command="GetSQLDBSize").strip()
        if add_logs_size:
            download_size = get_sensor_reading(address, command="GetZippedLogsSize").strip()
    else:
        task_end_time = "NA "
        sensor_hostname = "Offline"
        download_size = "NA"
    data_queue.put({"address": address,
                    "status": str(sensor_status),
                    "response_time": str(task_end_time),
                    "sensor_hostname": str(sensor_hostname),
                    "download_size": str(download_size)})


def put_all_reports_zipped_to_cache(ip_list):
    """
    Downloads ALL remote sensor reports from provided IP or DNS addresses (as a list)
    then creates a single zip file for download off the local web portal.
    """
    try:
        hostname = app_cached_variables.hostname
        generate_html_reports_combo(ip_list)
        html_reports = [app_cached_variables.html_combo_report]
        html_report_names = ["ReportCombo.html"]
        app_cached_variables.sc_in_memory_zip = app_generic_functions.zip_files(html_report_names, html_reports)
        app_cached_variables.sc_reports_zip_name = "Reports_from_" + hostname + "_" + str(time.time())[:-8] + ".zip"
    except Exception as error:
        logger.network_logger.error("Sensor Control - Reports Zip Generation Error: " + str(error))
    app_cached_variables.creating_the_reports_zip = False
    logger.network_logger.info("Sensor Control - Reports Zip Generation Complete")


def downloads_sensor_control(address_list, download_type="sensors_download_databases"):
    """
    Used to initiate Downloads from provided IP or DNS addresses (list).
    Function option "download_type" dictates which type of download.
    Default = sensors_download_databases
    """
    data_queue = Queue()

    download_command = network_commands.sensor_sql_database
    download_type_message = "the SQLite3 Database Zipped"
    add_zipped_database_size = True
    add_zipped_logs_size = False
    size_type = "MB"
    column_download_message = "Uncompressed DB Size"
    extra_message = "Due to the CPU demands of zipping on the fly, raw Database size is shown here.<br>" + \
                    "Actual download size will be much smaller."
    if download_type == app_config_access.sensor_control_config.radio_download_logs:
        extra_message = ""
        column_download_message = "Zipped Logs Size"
        size_type = "KB"
        add_zipped_database_size = False
        add_zipped_logs_size = True
        download_command = network_commands.download_zipped_logs
        download_type_message = "Full Logs Zipped"
    sensor_download_url = "window.open('https://{{ IPAddress }}/" + download_command + "');"
    sensor_download_sql_list = ""
    text_ip_and_response = ""

    threads = []
    for address in address_list:
        threads.append(Thread(target=get_remote_sensor_check_and_delay,
                              args=[address, data_queue, False,
                                    add_zipped_database_size,
                                    add_zipped_logs_size]))
    app_generic_functions.start_and_wait_threads(threads)

    address_responses = []
    while not data_queue.empty():
        address_responses.append(data_queue.get())
        data_queue.task_done()

    address_responses = sorted(address_responses, key=lambda i: i['address'])
    for response in address_responses:
        if response["status"] == "OK":
            if app_generic_functions.check_for_port_in_address(response["address"]):
                address_split = app_generic_functions.get_ip_and_port_split(response["address"])
                address_and_port = address_split[0].strip() + ":" + address_split[1].strip()
            else:
                address_and_port = response["address"].strip() + ":10065"
            response_time = response["response_time"]
            background_colour = app_generic_functions.get_response_bg_colour(response_time)
            new_download = sensor_download_url.replace("{{ IPAddress }}", address_and_port)
            sensor_download_sql_list += new_download + "\n            "
            text_ip_and_response += "        <tr><th><span style='background-color: #f2f2f2;'>" + \
                                    response["address"] + "</span></th>\n" + \
                                    "        <th><span style='background-color: " + background_colour + ";'>" + \
                                    response_time + " Seconds</span></th>\n" + \
                                    "        <th><span style='background-color: #f2f2f2;'>" + \
                                    response["download_size"] + " " + size_type + "</span></th></tr>\n"

    return render_template("sensor_control_downloads.html",
                           PageURL="/SensorControlManage",
                           RestartServiceHidden=get_html_hidden_state(app_cached_variables.html_service_restart),
                           RebootSensorHidden=get_html_hidden_state(app_cached_variables.html_sensor_reboot),
                           DownloadTypeMessage=download_type_message,
                           DownloadURLs=sensor_download_sql_list.strip(),
                           SensorResponse=text_ip_and_response.strip(),
                           ColumnDownloadMessage=column_download_message,
                           ExtraMessage=extra_message)


def generate_html_reports_combo(ip_list, skip_rewrite_link=False):
    """
    Returns a combination of all reports in HTML format.
    Reports are downloaded from the provided list of remote sensors (IP or DNS addresses)
    """
    try:
        system_report = app_config_access.sensor_control_config.radio_report_system
        config_report = app_config_access.sensor_control_config.radio_report_config
        sensors_report = app_config_access.sensor_control_config.radio_report_test_sensors
        latency_report = app_config_access.sensor_control_config.radio_report_sensors_latency

        generate_sensor_control_report(ip_list, report_type=system_report)
        generate_sensor_control_report(ip_list, report_type=config_report)
        generate_sensor_control_report(ip_list, report_type=sensors_report)
        generate_sensor_control_report(ip_list, report_type=latency_report)

        html_system_report = app_cached_variables.html_system_report
        html_config_report = app_cached_variables.html_config_report
        html_readings_report = app_cached_variables.html_readings_report
        html_latency_report = app_cached_variables.html_latency_report
        if not skip_rewrite_link:
            html_system_report = _replace_text_in_report(app_cached_variables.html_system_report, "System")
            html_config_report = _replace_text_in_report(app_cached_variables.html_config_report, "Configuration")
            html_readings_report = _replace_text_in_report(app_cached_variables.html_readings_report, "Sensor Readings")
            html_latency_report = _replace_text_in_report(app_cached_variables.html_latency_report, "Sensor Latency")

        html_final_combo_return = app_generic_functions.get_file_content(file_locations.html_combo_report)
        html_final_combo_return = html_final_combo_return.replace("{{ FullSystemReport }}", html_system_report)
        html_final_combo_return = html_final_combo_return.replace("{{ FullConfigurationReport }}", html_config_report)
        html_final_combo_return = html_final_combo_return.replace("{{ FullReadingsReport }}", html_readings_report)
        html_final_combo_return = html_final_combo_return.replace("{{ FullLatencyReport }}", html_latency_report)
    except Exception as error:
        logger.primary_logger.error("Sensor Control - Unable to Generate Reports for Download: " + str(error))
        html_final_combo_return = "Error"
    app_cached_variables.html_combo_report = html_final_combo_return


def _replace_text_in_report(report, new_text):
    old_text_list = ["Back to Sensor Control", "/SensorControlManage"]
    new_text_list = ["Kootnet Sensor Report - " + new_text, ""]

    for old_text, new_text in zip(old_text_list, new_text_list):
        report = report.replace(old_text, new_text)
    return report


def create_the_big_zip(ip_list):
    """
    Downloads everything from sensors based on provided IP or DNS addresses (as a list)
    then creates a single zip file for download off the local web portal.
    """
    data_queue = Queue()

    new_name = "TheBigZip_" + app_cached_variables.hostname + "_" + str(time.time())[:-8] + ".zip"
    app_cached_variables.sc_big_zip_name = new_name

    if len(ip_list) > 0:
        try:
            return_names = ["ReportCombo.html"]
            generate_html_reports_combo(ip_list)
            return_files = [app_cached_variables.html_combo_report]

            _queue_name_and_file_list(ip_list, data_queue, network_commands.download_zipped_everything)
            ip_name_and_data = get_data_queue_items(data_queue)

            for sensor in ip_name_and_data:
                current_file_name = sensor[0].split(".")[-1] + "_" + sensor[1] + ".zip"
                return_names.append(current_file_name)
                return_files.append(sensor[2])

            if app_generic_functions.save_to_memory_ok(get_sum_db_sizes(ip_list)):
                app_cached_variables.sc_in_memory_zip = app_generic_functions.zip_files(return_names, return_files)
            else:
                zip_location = file_locations.html_sensor_control_big_zip
                app_generic_functions.zip_files(return_names, return_files, save_type="to_disk",
                                                file_location=zip_location)

            logger.network_logger.info("Sensor Control - The Big Zip Generation Completed")
            app_cached_variables.creating_the_big_zip = False
        except Exception as error:
            logger.primary_logger.error("Sensor Control - Big Zip Error: " + str(error))
            app_cached_variables.creating_the_big_zip = False
            app_cached_variables.sc_big_zip_name = ""


def _queue_name_and_file_list(ip_list, data_queue, command):
    threads = []
    for address in ip_list:
        threads.append(Thread(target=_worker_queue_list_ip_name_file, args=[address, data_queue, command]))
    app_generic_functions.start_and_wait_threads(threads)


def _worker_queue_list_ip_name_file(address, data_queue, command):
    try:
        sensor_name = app_generic_functions.get_http_sensor_reading(address, command="GetHostName")
        sensor_data = app_generic_functions.get_http_sensor_file(address, command)
        data_queue.put([address, sensor_name, sensor_data])
    except Exception as error:
        logger.network_logger.error("Sensor Control - Get Remote File Failed: " + str(error))


def sensor_control_management():
    """ Returns flask rendered template (HTML page) of "Sensor Control" in the Web Portal. """
    radio_checked_online_status = ""
    radio_checked_combo_reports = ""
    radio_checked_systems_report = ""
    radio_checked_config_report = ""
    radio_checked_sensors_test_report = ""
    radio_checked_sensors_latency_report = ""
    radio_checked_download_reports = ""
    radio_checked_download_database = ""
    radio_checked_download_logs = ""
    radio_checked_download_big_zip = ""

    radio_checked_send_relayed = ""
    radio_checked_send_direct = ""

    disabled_download_relayed = ""
    disabled_download_direct = ""
    selected_action = app_config_access.sensor_control_config.selected_action
    if selected_action == app_config_access.sensor_control_config.radio_check_status:
        radio_checked_online_status = "checked"
        disabled_download_relayed = "disabled"
        disabled_download_direct = "disabled"
    elif selected_action == app_config_access.sensor_control_config.radio_report_combo:
        radio_checked_combo_reports = "checked"
        disabled_download_relayed = "disabled"
        disabled_download_direct = "disabled"
    elif selected_action == app_config_access.sensor_control_config.radio_report_system:
        radio_checked_systems_report = "checked"
        disabled_download_relayed = "disabled"
        disabled_download_direct = "disabled"
    elif selected_action == app_config_access.sensor_control_config.radio_report_config:
        radio_checked_config_report = "checked"
        disabled_download_relayed = "disabled"
        disabled_download_direct = "disabled"
    elif selected_action == app_config_access.sensor_control_config.radio_report_test_sensors:
        radio_checked_sensors_test_report = "checked"
        disabled_download_relayed = "disabled"
        disabled_download_direct = "disabled"
    elif selected_action == app_config_access.sensor_control_config.radio_report_sensors_latency:
        radio_checked_sensors_latency_report = "checked"
        disabled_download_relayed = "disabled"
        disabled_download_direct = "disabled"
    elif selected_action == app_config_access.sensor_control_config.radio_download_reports:
        radio_checked_download_reports = "checked"
        radio_checked_send_relayed = "checked"
        disabled_download_direct = "disabled"
    elif selected_action == app_config_access.sensor_control_config.radio_download_databases:
        radio_checked_download_database = "checked"
    elif selected_action == app_config_access.sensor_control_config.radio_download_logs:
        radio_checked_download_logs = "checked"
    elif selected_action == app_config_access.sensor_control_config.radio_create_the_big_zip:
        radio_checked_download_big_zip = "checked"
        radio_checked_send_relayed = "checked"
        disabled_download_direct = "disabled"

    if radio_checked_send_relayed == "" and radio_checked_send_direct == "":
        radio_checked_send_relayed = "checked"

    download_big_zip = "disabled"
    if not app_cached_variables.creating_the_big_zip and app_cached_variables.sc_big_zip_name != "":
        download_big_zip = ""

    download_reports_zip = "disabled"
    if not app_cached_variables.creating_the_reports_zip and app_cached_variables.sc_reports_zip_name != "":
        download_reports_zip = ""

    download_databases_zip = "disabled"
    if not app_cached_variables.creating_databases_zip and app_cached_variables.sc_databases_zip_name != "":
        download_databases_zip = ""

    download_logs_zip = "disabled"
    if not app_cached_variables.creating_logs_zip and app_cached_variables.sc_logs_zip_name != "":
        download_logs_zip = ""

    disable_run_action_button = "disabled"
    if app_cached_variables.creating_the_big_zip:
        extra_message = "Creating Big Zip"
    elif app_cached_variables.creating_the_reports_zip:
        extra_message = "Creating Reports Zip"
    elif app_cached_variables.creating_databases_zip:
        extra_message = "Creating Databases Zip"
    elif app_cached_variables.creating_logs_zip:
        extra_message = "Creating Logs Zip"
    elif app_cached_variables.creating_combo_report:
        extra_message = "Creating Combo Report"
    elif app_cached_variables.creating_system_report:
        extra_message = "Creating System Report"
    elif app_cached_variables.creating_config_report:
        extra_message = "Creating Configuration Report"
    elif app_cached_variables.creating_readings_report:
        extra_message = "Creating Readings Report"
    elif app_cached_variables.creating_latency_report:
        extra_message = "Creating Latency Report"
    else:
        disable_run_action_button = ""
        extra_message = ""

    return render_template("sensor_control.html",
                           PageURL="/SensorControlManage",
                           RestartServiceHidden=get_html_hidden_state(app_cached_variables.html_service_restart),
                           RebootSensorHidden=get_html_hidden_state(app_cached_variables.html_sensor_reboot),
                           ExtraTextMessage=extra_message,
                           DownloadReportsZipDisabled=download_reports_zip,
                           DownloadDatabasesDisabled=download_databases_zip,
                           DownloadLogsDisabled=download_logs_zip,
                           DownloadBigZipDisabled=download_big_zip,
                           RunActionDisabled=disable_run_action_button,
                           CheckedOnlineStatus=radio_checked_online_status,
                           CheckedComboReports=radio_checked_combo_reports,
                           CheckedSystemReports=radio_checked_systems_report,
                           CheckedConfigReports=radio_checked_config_report,
                           CheckedSensorsTestReports=radio_checked_sensors_test_report,
                           CheckedSensorsLatencyReports=radio_checked_sensors_latency_report,
                           CheckedRelayedDownload=radio_checked_send_relayed,
                           CheckedDirectDownload=radio_checked_send_direct,
                           CheckedDownloadReports=radio_checked_download_reports,
                           CheckedDownloadDatabases=radio_checked_download_database,
                           CheckedDownloadLogs=radio_checked_download_logs,
                           CheckedDownloadBig=radio_checked_download_big_zip,
                           DisabledRelayedDownload=disabled_download_relayed,
                           DisabledDirectDownload=disabled_download_direct,
                           SensorIP1=app_config_access.sensor_control_config.sensor_ip_dns1,
                           SensorIP2=app_config_access.sensor_control_config.sensor_ip_dns2,
                           SensorIP3=app_config_access.sensor_control_config.sensor_ip_dns3,
                           SensorIP4=app_config_access.sensor_control_config.sensor_ip_dns4,
                           SensorIP5=app_config_access.sensor_control_config.sensor_ip_dns5,
                           SensorIP6=app_config_access.sensor_control_config.sensor_ip_dns6,
                           SensorIP7=app_config_access.sensor_control_config.sensor_ip_dns7,
                           SensorIP8=app_config_access.sensor_control_config.sensor_ip_dns8,
                           SensorIP9=app_config_access.sensor_control_config.sensor_ip_dns9,
                           SensorIP10=app_config_access.sensor_control_config.sensor_ip_dns10,
                           SensorIP11=app_config_access.sensor_control_config.sensor_ip_dns11,
                           SensorIP12=app_config_access.sensor_control_config.sensor_ip_dns12,
                           SensorIP13=app_config_access.sensor_control_config.sensor_ip_dns13,
                           SensorIP14=app_config_access.sensor_control_config.sensor_ip_dns14,
                           SensorIP15=app_config_access.sensor_control_config.sensor_ip_dns15,
                           SensorIP16=app_config_access.sensor_control_config.sensor_ip_dns16,
                           SensorIP17=app_config_access.sensor_control_config.sensor_ip_dns17,
                           SensorIP18=app_config_access.sensor_control_config.sensor_ip_dns18,
                           SensorIP19=app_config_access.sensor_control_config.sensor_ip_dns19,
                           SensorIP20=app_config_access.sensor_control_config.sensor_ip_dns20,
                           SensorControlEditConfig=_get_sensor_control_edit_configs())


def _get_sensor_control_edit_configs():
    return render_template("sensor_control_edit_configs.html",
                           InitialPrimaryConfig=initial_primary_select,
                           DefaultPrimaryText=default_primary_config,
                           DefaultInstalledSensorsText=default_installed_sensors_config,
                           DefaultIntervalRecText=default_interval_recording_config,
                           DefaultVarianceRecText=default_variance_config,
                           DefaultHighLowRecText=default_high_low_config,
                           DefaultDisplayText=default_display_config,
                           DefaultEmailText=default_email_config,
                           DefaultWifiText=default_wifi_config,
                           DefaultNetworkText=default_network_config)


def get_sum_db_sizes(ip_list):
    """ Gets the size of remote sensors zipped database based on provided IP or DNS addresses (as a list) """
    data_queue = Queue()

    databases_size = 0.0
    try:
        threads = []
        for address in ip_list:
            threads.append(Thread(target=_worker_get_db_size, args=[address, data_queue]))
        app_generic_functions.start_and_wait_threads(threads)

        while not data_queue.empty():
            db_size = data_queue.get()
            databases_size += db_size
            data_queue.task_done()
    except Exception as error:
        logger.network_logger.error("Sensor Control - Unable to retrieve Database Sizes Sum: " + str(error))
    logger.network_logger.debug("Total DB Sizes in MB: " + str(databases_size))
    return databases_size


def _worker_get_db_size(address, data_queue):
    get_http_sensor_reading = app_generic_functions.get_http_sensor_reading
    get_database_size_command = network_commands.sensor_sql_database_size
    try:
        try_get = True
        get_error_count = 0
        while try_get and get_error_count < 3:
            try:
                db_size = float(get_http_sensor_reading(address, command=get_database_size_command))
                data_queue.put(db_size)
                try_get = False
            except Exception as error:
                log_msg = "Sensor Control - Error getting sensor DB Size for "
                logger.network_logger.error(log_msg + address + " attempt #" + str(get_error_count + 1))
                logger.network_logger.debug("Sensor Control DB Sizes Error: " + str(error))
                get_error_count += 1
        if get_error_count > 2:
            data_queue.put(0)
    except Exception as error:
        log_msg = "Sensor Control - Unable to retrieve Database Size for " + address + ": " + str(error)
        logger.network_logger.error(log_msg)


def get_data_queue_items(data_queue):
    """ Returns a list of items from a data_queue. """
    que_data = []
    while not data_queue.empty():
        que_data.append(data_queue.get())
        data_queue.task_done()
    return que_data


def sensor_addresses_required_msg():
    msg_1 = "Please set at least one remote sensor address"
    msg_2 = "Press the button 'SHOW/HIDE IP LIST' under remote management to set sensor addresses."
    return message_and_return(msg_1, text_message2=msg_2, url="SensorControlManage")
