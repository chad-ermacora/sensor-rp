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
import operations_config
import operations_db
import operations_sensors
import logging
from logging.handlers import RotatingFileHandler
from time import sleep

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')

file_handler = RotatingFileHandler('/home/pi/KootNetSensors/logs/Sensors_log.txt', maxBytes=256000, backupCount=5)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

installed_sensors = operations_config.get_installed_sensors()
installed_config = operations_config.get_installed_config()
operations_db.check_database_trigger()

logger.info("Sensor Recording by Trigger Started")


def check_acc(new_data, old_data):
    write_to_db = False

    if (old_data.acc_x - installed_config.acc_variance) > new_data.acc_x or \
            new_data.acc_x > (old_data.acc_x + installed_config.acc_variance):
        write_to_db = True
    elif (old_data.acc_y - installed_config.acc_variance) > new_data.acc_y or \
            new_data.acc_y > (old_data.acc_y + installed_config.acc_variance):
        write_to_db = True
    elif (old_data.acc_z - installed_config.acc_variance) > new_data.acc_z or \
            new_data.acc_z > (old_data.acc_z + installed_config.acc_variance):
        write_to_db = True

    return write_to_db


def check_mag(new_data, old_data):
    write_to_db = False

    if (old_data.mag_x - installed_config.mag_variance) > new_data.mag_x or \
            new_data.mag_x > (old_data.mag_x + installed_config.mag_variance):
        write_to_db = True
    elif (old_data.mag_y - installed_config.mag_variance) > new_data.mag_y or \
            new_data.mag_y > (old_data.mag_y + installed_config.mag_variance):
        write_to_db = True
    elif (old_data.mag_z - installed_config.mag_variance) > new_data.mag_z or \
            new_data.mag_z > (old_data.mag_z + installed_config.mag_variance):
        write_to_db = True

    return write_to_db


def check_gyro(new_data, old_data):
    write_to_db = False

    if (old_data.gyro_x - installed_config.gyro_variance) > new_data.gyro_x or \
            new_data.gyro_x > (old_data.gyro_x + installed_config.gyro_variance):
        write_to_db = True
    elif (old_data.gyro_y - installed_config.gyro_variance) > new_data.gyro_y or \
            new_data.gyro_y > (old_data.gyro_y + installed_config.gyro_variance):
        write_to_db = True
    elif (old_data.gyro_z - installed_config.gyro_variance) > new_data.gyro_z or \
            new_data.gyro_z > (old_data.gyro_z + installed_config.gyro_variance):
        write_to_db = True

    return write_to_db


def write_to_database(trigger_data):
    sql_command = operations_db.CreateSQLCommandData()

    sql_command.database_location = trigger_data.database_location
    sql_command.sql_execute = trigger_data.sql_query_start + trigger_data.sensor_types + \
        trigger_data.sql_query_values_start + trigger_data.sensor_readings + trigger_data.sql_query_values_end

    operations_db.write_to_sql_database(sql_command)


if installed_config.write_to_db:
    start_trigger_data = operations_sensors.get_trigger_sensor_readings()
    write_to_database(start_trigger_data)
    print("Sensor Types: " + str(start_trigger_data.sensor_types))
    print("Sensor Readings: " + str(start_trigger_data.sensor_readings))

    while True:
        old_trigger_data = operations_sensors.get_trigger_sensor_readings()
        sleep(installed_config.sleep_duration_trigger)
        new_trigger_data = operations_sensors.get_trigger_sensor_readings()

        if installed_sensors.has_acc and check_acc(new_trigger_data, old_trigger_data):
            logger.debug("Old Accelerometer - X:" + str(old_trigger_data.acc_x) +
                         " Y:" + str(old_trigger_data.acc_y) + " Z:" + str(old_trigger_data.acc_z))
            logger.debug("New Accelerometer - X:" + str(new_trigger_data.acc_x) +
                         " Y:" + str(new_trigger_data.acc_y) + " Z:" + str(new_trigger_data.acc_z))

            write_to_database(old_trigger_data)
            write_to_database(new_trigger_data)

        elif installed_sensors.has_mag and check_mag(new_trigger_data, old_trigger_data):
            logger.debug("Old Magnetometer - X:" + str(old_trigger_data.mag_x) +
                         " Y:" + str(old_trigger_data.mag_y) + " Z:" + str(old_trigger_data.mag_z))
            logger.debug("New Magnetometer - X:" + str(new_trigger_data.mag_x) +
                         " Y:" + str(new_trigger_data.mag_y) + " Z:" + str(new_trigger_data.mag_z))

            write_to_database(old_trigger_data)
            write_to_database(new_trigger_data)

        elif installed_sensors.has_gyro and check_gyro(new_trigger_data, old_trigger_data):
            logger.debug("Old Gyroscope - X:" + str(old_trigger_data.gyro_x) +
                         " Y:" + str(old_trigger_data.gyro_y) + " Z:" + str(old_trigger_data.gyro_z))
            logger.debug("New Gyroscope - X:" + str(new_trigger_data.gyro_x) +
                         " Y:" + str(new_trigger_data.gyro_y) + " Z:" + str(new_trigger_data.gyro_z))

            write_to_database(old_trigger_data)
            write_to_database(new_trigger_data)
else:
    logger.warning("Write to Database Disabled in Config")
