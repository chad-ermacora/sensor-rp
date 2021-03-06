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
from flask import Blueprint, request, send_file
from operations_modules import logger
from operations_modules import file_locations
from operations_modules import app_generic_functions
from configuration_modules import app_config_access
from http_server.server_http_auth import auth
from sensor_modules import sensor_access

#  Note: Remote Sensor Management uses it's own section for setting configs
#  /http_server/flask_blueprints/sensor_control_files/sensor_control_config_sets.py
html_get_config_routes = Blueprint("html_get_config_routes", __name__)


@html_get_config_routes.route("/GetConfiguration")
def get_primary_configuration():
    logger.network_logger.debug("* Primary Sensor Configuration Sent to " + str(request.remote_addr))
    return app_config_access.primary_config.get_config_as_str()


@html_get_config_routes.route("/SetPrimaryConfiguration", methods=["PUT"])
@auth.login_required
def set_primary_configuration():
    try:
        if request.form.get("test_run"):
            app_config_access.primary_config.load_from_file = False
        else:
            logger.network_logger.info("** Primary Sensor Configuration Set by " + str(request.remote_addr))
        app_config_access.primary_config.set_config_with_str(request.form.get("command_data"))
        if request.form.get("test_run") is None:
            app_config_access.primary_config.save_config_to_file()
            app_generic_functions.thread_function(sensor_access.restart_services)
        return "OK"
    except Exception as error:
        log_msg = "Failed to set Primary Configuration from " + str(request.remote_addr)
        logger.network_logger.error(log_msg + " - " + str(error))
    return "Failed"


@html_get_config_routes.route("/GetInstalledSensors")
def get_installed_sensors():
    logger.network_logger.debug("* Installed Sensors Sent to " + str(request.remote_addr))
    return app_config_access.installed_sensors.get_config_as_str()


@html_get_config_routes.route("/SetInstalledSensors", methods=["PUT"])
@auth.login_required
def set_installed_sensors():
    try:
        if request.form.get("test_run"):
            app_config_access.installed_sensors.load_from_file = False
        else:
            logger.network_logger.info("** Installed Sensors Set by " + str(request.remote_addr))
        app_config_access.installed_sensors.set_config_with_str(request.form.get("command_data"))
        if request.form.get("test_run") is None:
            app_config_access.installed_sensors.save_config_to_file()
            app_generic_functions.thread_function(sensor_access.restart_services)
        return "OK"
    except Exception as error:
        log_msg = "Failed to set Installed Sensors from " + str(request.remote_addr)
        logger.network_logger.error(log_msg + " - " + str(error))
    return "Failed"


@html_get_config_routes.route("/GetIntervalConfiguration")
def get_interval_config():
    logger.network_logger.debug("* Interval Configuration Sent to " + str(request.remote_addr))
    return app_config_access.interval_recording_config.get_config_as_str()


@html_get_config_routes.route("/SetIntervalConfiguration", methods=["PUT"])
@auth.login_required
def set_interval_config():
    try:
        if request.form.get("test_run"):
            app_config_access.interval_recording_config.load_from_file = False
        else:
            logger.network_logger.debug("* Interval Configuration Set by " + str(request.remote_addr))
        app_config_access.interval_recording_config.set_config_with_str(request.form.get("command_data"))
        if request.form.get("test_run") is None:
            app_config_access.interval_recording_config.save_config_to_file()
            app_generic_functions.thread_function(sensor_access.restart_services)
        return "OK"
    except Exception as error:
        log_msg = "Failed to set Interval from " + str(request.remote_addr)
        logger.network_logger.error(log_msg + " - " + str(error))
    return "Failed"


@html_get_config_routes.route("/GetHighLowTriggerConfiguration")
def get_high_low_trigger_config():
    logger.network_logger.debug("* High Low Trigger Configuration Sent to " + str(request.remote_addr))
    return app_config_access.trigger_high_low.get_config_as_str()


@html_get_config_routes.route("/SetHighLowTriggerConfiguration", methods=["PUT"])
@auth.login_required
def set_high_low_trigger_config():
    try:
        if request.form.get("test_run"):
            app_config_access.trigger_high_low.load_from_file = False
        else:
            logger.network_logger.debug("* High/Low Trigger Configuration Set by " + str(request.remote_addr))
        app_config_access.trigger_high_low.set_config_with_str(request.form.get("command_data"))
        if request.form.get("test_run") is None:
            app_config_access.trigger_high_low.save_config_to_file()
            app_generic_functions.thread_function(sensor_access.restart_services)
        return "OK"
    except Exception as error:
        log_msg = "Failed to set High/Low Trigger from " + str(request.remote_addr)
        logger.network_logger.error(log_msg + " - " + str(error))
    return "Failed"


@html_get_config_routes.route("/GetVarianceConfiguration")
def get_variance_config():
    logger.network_logger.debug("* Variance Trigger Configuration Sent to " + str(request.remote_addr))
    return app_config_access.trigger_variances.get_config_as_str()


@html_get_config_routes.route("/SetVarianceConfiguration", methods=["PUT"])
@auth.login_required
def set_variance_config():
    try:
        if request.form.get("test_run"):
            app_config_access.trigger_variances.load_from_file = False
        else:
            logger.network_logger.debug("* Variance Trigger Configuration Set by " + str(request.remote_addr))
        app_config_access.trigger_variances.set_config_with_str(request.form.get("command_data"))
        if request.form.get("test_run") is None:
            app_config_access.trigger_variances.save_config_to_file()
            app_generic_functions.thread_function(sensor_access.restart_services)
        return "OK"
    except Exception as error:
        log_msg = "Failed to set Trigger Variances from " + str(request.remote_addr)
        logger.network_logger.error(log_msg + " - " + str(error))
    return "Failed"


@html_get_config_routes.route("/GetDisplayConfiguration")
def get_display_config():
    logger.network_logger.debug("* Display Configuration Sent to " + str(request.remote_addr))
    return app_config_access.display_config.get_config_as_str()


@html_get_config_routes.route("/SetDisplayConfiguration", methods=["PUT"])
@auth.login_required
def set_display_config():
    try:
        if request.form.get("test_run"):
            app_config_access.display_config.load_from_file = False
        else:
            logger.network_logger.info("** Display Configuration Set by " + str(request.remote_addr))
        app_config_access.display_config.set_config_with_str(request.form.get("command_data"))
        if request.form.get("test_run") is None:
            app_config_access.display_config.save_config_to_file()
        return "OK"
    except Exception as error:
        log_msg = "Failed to set Display Configuration from " + str(request.remote_addr)
        logger.network_logger.error(log_msg + " - " + str(error))
    return "Failed"


@html_get_config_routes.route("/GetEmailConfiguration")
@auth.login_required
def get_email_config():
    logger.network_logger.debug("* Email Configuration Sent to " + str(request.remote_addr))
    return app_config_access.email_config.get_config_as_str()


@html_get_config_routes.route("/SetEmailConfiguration", methods=["PUT"])
@auth.login_required
def set_email_config():
    try:
        if request.form.get("test_run"):
            app_config_access.email_config.load_from_file = False
        else:
            logger.network_logger.info("** Email Configuration Set by " + str(request.remote_addr))
        app_config_access.email_config.set_config_with_str(request.form.get("command_data"))
        if request.form.get("test_run") is None:
            app_config_access.email_config.save_config_to_file()
        return "OK"
    except Exception as error:
        log_msg = "Failed to set Email Configuration from " + str(request.remote_addr)
        logger.network_logger.error(log_msg + " - " + str(error))
    return "Failed"


@html_get_config_routes.route("/GetMQTTPublisherConfiguration")
@auth.login_required
def get_mqtt_publisher_config():
    logger.network_logger.debug("* MQTT Publisher Configuration Sent to " + str(request.remote_addr))
    return app_config_access.mqtt_publisher_config.get_config_as_str()


@html_get_config_routes.route("/SetMQTTPublisherConfiguration", methods=["PUT"])
@auth.login_required
def set_mqtt_publisher_config():
    try:
        if request.form.get("test_run"):
            app_config_access.mqtt_publisher_config.load_from_file = False
        else:
            logger.network_logger.info("** MQTT Publisher Configuration Set by " + str(request.remote_addr))
        app_config_access.mqtt_publisher_config.set_config_with_str(request.form.get("command_data"))
        if request.form.get("test_run") is None:
            app_config_access.mqtt_publisher_config.save_config_to_file()
        return "OK"
    except Exception as error:
        log_msg = "Failed to set MQTT Publisher Configuration from " + str(request.remote_addr)
        logger.network_logger.error(log_msg + " - " + str(error))
    return "Failed"


@html_get_config_routes.route("/GetMQTTSubscriberConfiguration")
@auth.login_required
def get_mqtt_subscriber_config():
    logger.network_logger.debug("* MQTT Subscriber Configuration Sent to " + str(request.remote_addr))
    return app_config_access.mqtt_subscriber_config.get_config_as_str()


@html_get_config_routes.route("/SetMQTTSubscriberConfiguration", methods=["PUT"])
@auth.login_required
def set_mqtt_subscriber_config():
    try:
        if request.form.get("test_run"):
            app_config_access.mqtt_subscriber_config.load_from_file = False
        else:
            logger.network_logger.info("** MQTT Subscriber Configuration Set by " + str(request.remote_addr))
        app_config_access.mqtt_subscriber_config.set_config_with_str(request.form.get("command_data"))
        if request.form.get("test_run") is None:
            app_config_access.mqtt_subscriber_config.save_config_to_file()
        return "OK"
    except Exception as error:
        log_msg = "Failed to set MQTT Subscriber Configuration from " + str(request.remote_addr)
        logger.network_logger.error(log_msg + " - " + str(error))
    return "Failed"


@html_get_config_routes.route("/GetSensorControlConfiguration")
def get_sensor_control_config():
    logger.network_logger.debug("* Sensor Control Configuration Sent to " + str(request.remote_addr))
    return app_config_access.sensor_control_config.get_config_as_str()


@html_get_config_routes.route("/SetSensorControlConfiguration", methods=["PUT"])
@auth.login_required
def set_sensor_control_config():
    try:
        if request.form.get("test_run"):
            app_config_access.sensor_control_config.load_from_file = False
        else:
            logger.network_logger.debug("* Sensor Control Configuration Set by " + str(request.remote_addr))
        app_config_access.sensor_control_config.set_config_with_str(request.form.get("command_data"))
        if request.form.get("test_run") is None:
            app_config_access.sensor_control_config.save_config_to_file()
        return "OK"
    except Exception as error:
        log_msg = "Failed to set Sensor Control Configuration from " + str(request.remote_addr)
        logger.network_logger.error(log_msg + " - " + str(error))
    return "Failed"


@html_get_config_routes.route("/GetWeatherUndergroundConfiguration")
@auth.login_required
def get_weather_underground_config():
    logger.network_logger.debug("* Weather Underground Configuration Sent to " + str(request.remote_addr))
    return app_config_access.weather_underground_config.get_config_as_str()


@html_get_config_routes.route("/SetWeatherUndergroundConfiguration", methods=["PUT"])
@auth.login_required
def set_weather_underground_config():
    try:
        if request.form.get("test_run"):
            app_config_access.weather_underground_config.load_from_file = False
        else:
            logger.network_logger.debug("* Weather Underground Configuration Set by " + str(request.remote_addr))
        app_config_access.weather_underground_config.set_config_with_str(request.form.get("command_data"))
        if request.form.get("test_run") is None:
            app_config_access.weather_underground_config.save_config_to_file()
        return "OK"
    except Exception as error:
        log_msg = "Failed to set Weather Underground Configuration from " + str(request.remote_addr)
        logger.network_logger.error(log_msg + " - " + str(error))
    return "Failed"


@html_get_config_routes.route("/GetOnlineServicesLuftdaten")
def get_luftdaten_config():
    logger.network_logger.debug("* Luftdaten Configuration Sent to " + str(request.remote_addr))
    return app_config_access.luftdaten_config.get_config_as_str()


@html_get_config_routes.route("/SetLuftdatenConfiguration", methods=["PUT"])
@auth.login_required
def set_luftdaten_config():
    try:
        if request.form.get("test_run"):
            app_config_access.luftdaten_config.load_from_file = False
        else:
            logger.network_logger.debug("* Luftdaten Configuration Set by " + str(request.remote_addr))
        app_config_access.luftdaten_config.set_config_with_str(request.form.get("command_data"))
        if request.form.get("test_run") is None:
            app_config_access.luftdaten_config.save_config_to_file()
        return "OK"
    except Exception as error:
        log_msg = "Failed to set Luftdaten Configuration from " + str(request.remote_addr)
        logger.network_logger.error(log_msg + " - " + str(error))
    return "Failed"


@html_get_config_routes.route("/GetOnlineServicesOpenSenseMap")
@auth.login_required
def get_open_sense_map_config():
    logger.network_logger.debug("* Open Sense Map Configuration Sent to " + str(request.remote_addr))
    return app_config_access.open_sense_map_config.get_config_as_str()


@html_get_config_routes.route("/SetOpenSenseMapConfiguration", methods=["PUT"])
@auth.login_required
def set_open_sense_map_config():
    try:
        if request.form.get("test_run"):
            app_config_access.open_sense_map_config.load_from_file = False
        else:
            logger.network_logger.debug("* OpenSenseMap Configuration Set by " + str(request.remote_addr))
        app_config_access.open_sense_map_config.set_config_with_str(request.form.get("command_data"))
        if request.form.get("test_run") is None:
            app_config_access.open_sense_map_config.save_config_to_file()
        return "OK"
    except Exception as error:
        log_msg = "Failed to set Open Sense Map Configuration from " + str(request.remote_addr)
        logger.network_logger.error(log_msg + " - " + str(error))
    return "Failed"


@html_get_config_routes.route("/GetWifiConfiguration")
@auth.login_required
def get_wifi_config():
    logger.network_logger.debug("* Wifi Sent to " + str(request.remote_addr))
    return send_file(file_locations.wifi_config_file)


@html_get_config_routes.route("/SetWifiConfiguration", methods=["PUT"])
@auth.login_required
def set_wifi_config():
    logger.network_logger.debug("* Wifi Set by " + str(request.remote_addr))
    try:
        new_wifi_config = request.form.get("command_data")
        app_generic_functions.write_file_to_disk(file_locations.wifi_config_file, new_wifi_config)
        return "OK"
    except Exception as error:
        log_msg = "Failed to set Primary Configuration from " + str(request.remote_addr)
        logger.network_logger.error(log_msg + " - " + str(error))
    return "Failed"
