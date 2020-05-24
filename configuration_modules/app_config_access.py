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
from operations_modules import logger
from operations_modules.app_cached_variables import running_with_root
from configuration_modules.config_installed_sensors import CreateInstalledSensorsConfiguration
from configuration_modules.config_primary import CreatePrimaryConfiguration
from configuration_modules.config_trigger_variances import CreateTriggerVariancesConfiguration
from configuration_modules.config_display import CreateDisplayConfiguration
from configuration_modules.config_sensor_control import CreateSensorControlConfiguration
from configuration_modules.config_mqtt_broker import CreateMQTTBrokerConfiguration
from configuration_modules.config_mqtt_publisher import CreateMQTTPublisherConfiguration
from configuration_modules.config_mqtt_subscriber import CreateMQTTSubscriberConfiguration
from configuration_modules.config_weather_underground import CreateWeatherUndergroundConfiguration
from configuration_modules.config_luftdaten import CreateLuftdatenConfiguration
from configuration_modules.config_open_sense_map import CreateOpenSenseMapConfiguration

if running_with_root:
    logger.primary_logger.debug("Initializing configurations")
    installed_sensors = CreateInstalledSensorsConfiguration()
else:
    logger.primary_logger.warning(" -- Sensors Initialization Skipped - root permissions required for sensors")
    installed_sensors = CreateInstalledSensorsConfiguration(load_from_file=False)
    if CreateInstalledSensorsConfiguration().kootnet_dummy_sensor:
        installed_sensors.kootnet_dummy_sensor = 1
        installed_sensors.no_sensors = False
        installed_sensors.update_configuration_settings_list()

primary_config = CreatePrimaryConfiguration()
trigger_variances = CreateTriggerVariancesConfiguration()
display_config = CreateDisplayConfiguration()
sensor_control_config = CreateSensorControlConfiguration()
mqtt_broker_config = CreateMQTTBrokerConfiguration()
mqtt_publisher_config = CreateMQTTPublisherConfiguration()
mqtt_subscriber_config = CreateMQTTSubscriberConfiguration()
weather_underground_config = CreateWeatherUndergroundConfiguration()
luftdaten_config = CreateLuftdatenConfiguration()
open_sense_map_config = CreateOpenSenseMapConfiguration()