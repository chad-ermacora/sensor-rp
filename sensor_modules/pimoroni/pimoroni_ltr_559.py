"""
This module is for the Pimoroni LTR-559 Light & Proximity
It Retrieves & Returns Sensor data to be written to the DB

Lite-On LTR-559ALS-01 sensor
I2C interface (address: 0x23)
IR/UV-filtering
50.60Hz flicker rejection
0.01 lux to 64,000 lux light detection range
~5cm proximity detection range
3.3V or 5V compatible
Reverse polarity protection
Raspberry Pi-compatible pinout (pins 1, 3, 5, 7, 9)
Compatible with Raspberry Pi 3B+, 3, 2, B+, A+, Zero, and Zero W

pip3 install ltr559

@author: OO-Dragon
"""
import time
from operations_modules import logger
from configuration_modules import app_config_access

round_decimal_to = 5
pause_sensor_during_access_sec = 0.02


class CreateLTR559:
    """ Creates Function access to the Pimoroni LTR-559. """

    def __init__(self):
        self.sensor_in_use = False
        try:
            ltr559_import = __import__("sensor_modules.drivers.ltr559", fromlist=["LTR559"])
            self.ltr_559 = ltr559_import.LTR559()
            self.ltr_559.get_lux()
            logger.sensors_logger.debug("Pimoroni LTR-559 Initialization - OK")
        except Exception as error:
            logger.sensors_logger.error("Pimoroni LTR-559 Initialization - Failed: " + str(error))
            app_config_access.installed_sensors.pimoroni_ltr_559 = 0
            app_config_access.installed_sensors.update_configuration_settings_list()

    def lumen(self):
        """ Returns Lumen as a Float. """
        while self.sensor_in_use:
            time.sleep(pause_sensor_during_access_sec)
        self.sensor_in_use = True
        try:
            lumen = float(self.ltr_559.get_lux())
        except Exception as error:
            logger.sensors_logger.error("Pimoroni LTR-559 Lumen - Failed: " + str(error))
            lumen = 0.0
        self.sensor_in_use = False
        return round(lumen, round_decimal_to)

    def distance(self):
        """ Returns distance in cm?. """
        while self.sensor_in_use:
            time.sleep(pause_sensor_during_access_sec)
        self.sensor_in_use = True
        try:
            distance = float(self.ltr_559.get_proximity())
        except Exception as error:
            logger.sensors_logger.error("Pimoroni LTR-559 Proximity - Failed: " + str(error))
            distance = 0.0
        self.sensor_in_use = False
        return round(distance, round_decimal_to)
