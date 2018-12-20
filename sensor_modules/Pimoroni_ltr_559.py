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
from operations_modules import operations_logger

round_decimal_to = 5


class CreateLTR559:
    """ Creates Function access to the Pimoroni LTR-559. """

    def __init__(self):
        self.ltr_559 = __import__('ltr559')

    def lumen(self):
        """ Returns Lumen. """
        try:
            lumen = float(self.ltr_559.get_lux())
            operations_logger.sensors_logger.debug("Pimoroni LTR-559 Lumen - OK")
        except Exception as error:
            operations_logger.sensors_logger.error("Pimoroni LTR-559 Lumen - Failed - " + str(error))
            lumen = 0.0

        return round(lumen, round_decimal_to)

    def distance(self):
        """ Returns distance in cm?. """
        try:
            distance = float(self.ltr_559.get_proximity())
            operations_logger.sensors_logger.debug("Pimoroni LTR-559 Proximity - OK")
        except Exception as error:
            operations_logger.sensors_logger.error("Pimoroni LTR-559 Proximity - Failed - " + str(error))
            distance = 0.0

        return round(distance, round_decimal_to)
