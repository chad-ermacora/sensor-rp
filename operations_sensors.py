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
from datetime import datetime

import operations_config
import operations_db
import sensor_modules.Linux_OS
import sensor_modules.Pimoroni_BH1745
import sensor_modules.Pimoroni_BME680
import sensor_modules.Pimoroni_Enviro
import sensor_modules.Pimoroni_LSM303D
import sensor_modules.RaspberryPi_SenseHAT
import sensor_modules.RaspberryPi_System
import sensor_modules.Temperature_Offsets

# import sensor_modules.Pimoroni_VL53L1X

installed_sensors = operations_config.get_installed_sensors()
current_config = operations_config.get_installed_config()

# Initialize sensor access, based on installed sensors file
if installed_sensors.linux_system:
    os_sensor_access = sensor_modules.Linux_OS.CreateLinuxSystem()
if installed_sensors.raspberry_pi_zero_w or installed_sensors.raspberry_pi_3b_plus:
    system_sensor_access = sensor_modules.RaspberryPi_System.CreateRPSystem()
if installed_sensors.raspberry_pi_sense_hat:
    rp_sense_hat_sensor_access = sensor_modules.RaspberryPi_SenseHAT.CreateRPSenseHAT()
if installed_sensors.pimoroni_enviro:
    pimoroni_enviro_sensor_access = sensor_modules.Pimoroni_Enviro.CreateEnviro()
if installed_sensors.pimoroni_bme680:
    bme680_sensor_access = sensor_modules.Pimoroni_BME680.CreateBME680()
if installed_sensors.pimoroni_bh1745:
    pimoroni_bh1745_sensor_access = sensor_modules.Pimoroni_BH1745.CreateBH1745()
if installed_sensors.pimoroni_lsm303d:
    lsm303d_sensor_access = sensor_modules.Pimoroni_LSM303D.CreateLSM303D()
if installed_sensors.pimoroni_vl53l1x:
    pass


def get_interval_sensor_readings():
    """ Returns Interval sensor readings from installed sensors (set in installed sensors file). """
    interval_data = operations_db.CreateIntervalDatabaseData()

    interval_data.sensor_types = "DateTime, "
    interval_data.sensor_readings = "'" + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "', "

    if installed_sensors.linux_system:
        interval_data.sensor_types += "SensorName, IP, SensorUpTime, SystemTemp, "

        if installed_sensors.raspberry_pi_3b_plus or installed_sensors.raspberry_pi_zero_w:
            cpu_temp = str(system_sensor_access.cpu_temperature())
        else:
            cpu_temp = "NA"

        interval_data.sensor_readings += "'" + str(os_sensor_access.get_hostname()) + "', '" + \
                                         str(os_sensor_access.get_ip()) + "', '" + \
                                         str(os_sensor_access.get_uptime()) + "', '" + \
                                         cpu_temp + "', "

    if installed_sensors.raspberry_pi_sense_hat:
        interval_data.sensor_types += "EnvironmentTemp, " \
                                      "EnvTempOffset, " \
                                      "Pressure, " \
                                      "Humidity, "
        interval_data.sensor_readings += "'" + str(rp_sense_hat_sensor_access.temperature()) + "', '" + \
                                         str(get_sensor_temperature_offset()) + "', '" + \
                                         str(rp_sense_hat_sensor_access.pressure()) + "', '" + \
                                         str(rp_sense_hat_sensor_access.humidity()) + "', "

    if installed_sensors.pimoroni_enviro:
        rgb_colour = pimoroni_enviro_sensor_access.rgb()

        interval_data.sensor_types += \
            "EnvironmentTemp, " \
            "EnvTempOffset, " \
            "Pressure, " \
            "Lumen, " \
            "Red, " \
            "Green, " \
            "Blue, "
        interval_data.sensor_readings += "'" + str(pimoroni_enviro_sensor_access.temperature()) + "', '" + \
                                         str(get_sensor_temperature_offset()) + "', '" + \
                                         str(pimoroni_enviro_sensor_access.pressure()) + "', '" + \
                                         str(pimoroni_enviro_sensor_access.lumen()) + "', '" + \
                                         str(rgb_colour[0]) + "', '" + \
                                         str(rgb_colour[1]) + "', '" + \
                                         str(rgb_colour[2]) + "', "

    if installed_sensors.pimoroni_bme680:
        interval_data.sensor_types += "EnvironmentTemp, EnvTempOffset, Pressure, Humidity, "

        interval_data.sensor_readings += "'" + str(bme680_sensor_access.temperature()) + "', '" + \
                                         str(get_sensor_temperature_offset()) + "', '" + \
                                         str(bme680_sensor_access.pressure()) + "', '" + \
                                         str(bme680_sensor_access.humidity()) + "', "

    if installed_sensors.pimoroni_bh1745:
        rgb_colour = pimoroni_bh1745_sensor_access.rgb()

        interval_data.sensor_types += "Lumen, Red, Green, Blue, "
        interval_data.sensor_readings += "'" + str(pimoroni_bh1745_sensor_access.lumen()) + "', '" + \
                                         str(rgb_colour[0]) + "', '" + \
                                         str(rgb_colour[1]) + "', '" + \
                                         str(rgb_colour[2]) + "', "

    interval_data.sensor_types = interval_data.sensor_types[:-2]
    interval_data.sensor_readings = interval_data.sensor_readings[:-2]

    if interval_data.sensor_types != "DateTime":
        return interval_data


def get_trigger_sensor_readings():
    """ Returns Trigger sensor readings from installed sensors (set in installed sensors file). """
    trigger_data = operations_db.CreateTriggerDatabaseData()
    trigger_data.sensor_types = "DateTime, "
    trigger_data.sensor_readings = "'" + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "', "

    if installed_sensors.linux_system:
        sensor_types = "SensorName, IP, "
        sensor_readings = "'" + str(os_sensor_access.get_hostname()) + "', '" + str(os_sensor_access.get_ip()) + "', "

        trigger_data.sensor_types += sensor_types
        trigger_data.sensor_readings += sensor_readings

    if installed_sensors.raspberry_pi_sense_hat:
        sensor_types = "Acc_X, Acc_Y, Acc_Z, Mag_X, Mag_Y, Mag_Z, Gyro_X, Gyro_Y, Gyro_Z, "

        acc_x, acc_y, acc_z = rp_sense_hat_sensor_access.accelerometer_xyz()
        mag_x, mag_y, mag_z = rp_sense_hat_sensor_access.magnetometer_xyz()
        gyro_x, gyro_y, gyro_z = rp_sense_hat_sensor_access.gyroscope_xyz()

        sensor_readings = "'" + str(acc_x) + "', '" + \
                          str(acc_y) + "', '" + \
                          str(acc_z) + "', '" + \
                          str(mag_x) + "', '" + \
                          str(mag_y) + "', '" + \
                          str(mag_z) + "', '" + \
                          str(gyro_x) + "', '" + \
                          str(gyro_y) + "', '" + \
                          str(gyro_z) + "', "

        trigger_data.sensor_types += sensor_types
        trigger_data.sensor_readings += sensor_readings

    if installed_sensors.pimoroni_enviro:
        sensor_types = "Acc_X ,Acc_Y ,Acc_Z ,Mag_X ,Mag_Y ,Mag_Z, "

        acc_x, acc_y, acc_z = pimoroni_enviro_sensor_access.accelerometer_xyz()
        mag_x, mag_y, mag_z = pimoroni_enviro_sensor_access.magnetometer_xyz()

        sensor_readings = "'" + str(acc_x) + "', '" + \
                          str(acc_y) + "', '" + \
                          str(acc_z) + "', '" + \
                          str(mag_x) + "', '" + \
                          str(mag_y) + "', '" + \
                          str(mag_z) + "', "

        trigger_data.sensor_types += sensor_types
        trigger_data.sensor_readings += sensor_readings

    if installed_sensors.pimoroni_lsm303d:
        sensor_types = "Acc_X ,Acc_Y ,Acc_Z ,Mag_X ,Mag_Y ,Mag_Z, "

        acc_x, acc_y, acc_z = lsm303d_sensor_access.accelerometer_xyz()
        mag_x, mag_y, mag_z = lsm303d_sensor_access.magnetometer_xyz()

        sensor_readings = "'" + str(acc_x) + "', '" + \
                          str(acc_y) + "', '" + \
                          str(acc_z) + "', '" + \
                          str(mag_x) + "', '" + \
                          str(mag_y) + "', '" + \
                          str(mag_z) + "', "

        trigger_data.sensor_types += sensor_types
        trigger_data.sensor_readings += sensor_readings

    trigger_data.sensor_types = trigger_data.sensor_types[:-2]
    trigger_data.sensor_readings = trigger_data.sensor_readings[:-2]

    if trigger_data.sensor_types != "DateTime":
        return trigger_data


def get_hostname():
    """ Returns sensors hostname. """
    if installed_sensors.linux_system:
        sensor_name = os_sensor_access.get_hostname()
        return sensor_name
    else:
        return "NoSensor"


def get_system_uptime():
    """ Returns sensors system UpTime. """
    if installed_sensors.linux_system:
        sensor_uptime = os_sensor_access.get_uptime()
        return sensor_uptime
    else:
        return "NoSensor"


def get_cpu_temperature():
    """ Returns sensors CPU temperature. """
    if installed_sensors.raspberry_pi_zero_w or installed_sensors.raspberry_pi_3b_plus:
        temperature = system_sensor_access.cpu_temperature()
        return temperature
    else:
        return "NoSensor"


def get_sensor_temperature():
    """ Returns sensors Environmental temperature. """
    if installed_sensors.pimoroni_enviro:
        temperature = pimoroni_enviro_sensor_access.temperature()
        return temperature
    elif installed_sensors.pimoroni_bme680:
        temperature = bme680_sensor_access.temperature()
        return temperature
    elif installed_sensors.raspberry_pi_sense_hat:
        temperature = rp_sense_hat_sensor_access.temperature()
        return temperature
    else:
        return "NoSensor"


def get_sensor_temperature_offset():
    """
     Returns sensors Environmental temperature offset based on system board and sensor.
     You can set an override in the main sensor configuration file.
    """
    if installed_sensors.raspberry_pi_3b_plus:
        sensor_temp_offset = sensor_modules.Temperature_Offsets.CreateRP3BPlusTemperatureOffsets()
    elif installed_sensors.raspberry_pi_zero_w:
        sensor_temp_offset = sensor_modules.Temperature_Offsets.CreateRPZeroWTemperatureOffsets()
    else:
        # This should probably be replaced by something more.. generic?
        sensor_temp_offset = sensor_modules.Temperature_Offsets.CreateRPZeroWTemperatureOffsets()

    if current_config.enable_custom_temp:
        return current_config.custom_temperature_offset
    elif installed_sensors.pimoroni_enviro:
        return sensor_temp_offset.pimoroni_enviro
    elif installed_sensors.pimoroni_bme680:
        return sensor_temp_offset.pimoroni_bme680
    elif installed_sensors.raspberry_pi_sense_hat:
        return sensor_temp_offset.rp_sense_hat
    else:
        return 0.0


def get_pressure():
    """ Returns sensors pressure. """
    if installed_sensors.pimoroni_enviro:
        pressure = pimoroni_enviro_sensor_access.pressure()
        return pressure
    elif installed_sensors.pimoroni_bme680:
        pressure = bme680_sensor_access.pressure()
        return pressure
    elif installed_sensors.raspberry_pi_sense_hat:
        pressure = rp_sense_hat_sensor_access.pressure()
        return pressure
    else:
        return "NoSensor"


def get_humidity():
    """ Returns sensors humidity. """
    if installed_sensors.pimoroni_bme680:
        humidity = bme680_sensor_access.humidity()
        return humidity
    elif installed_sensors.raspberry_pi_sense_hat:
        humidity = rp_sense_hat_sensor_access.humidity()
        return humidity
    else:
        return "NoSensor"


def get_lumen():
    """ Returns sensors lumen. """
    if installed_sensors.pimoroni_enviro:
        lumen = pimoroni_enviro_sensor_access.lumen()
        return lumen
    elif installed_sensors.pimoroni_bh1745:
        lumen = pimoroni_bh1745_sensor_access.lumen()
        return lumen
    else:
        return "NoSensor"


def get_rgb():
    """ Returns sensors Red, Green, Blue spectrum. """
    if installed_sensors.pimoroni_enviro:
        rgb = pimoroni_enviro_sensor_access.rgb()
        return rgb
    elif installed_sensors.pimoroni_bh1745:
        rgb = pimoroni_bh1745_sensor_access.rgb()
        return rgb
    else:
        return "NoSensor"


def get_accelerometer_xyz():
    """ Returns sensors Accelerometer XYZ. """
    if installed_sensors.raspberry_pi_sense_hat:
        xyz = rp_sense_hat_sensor_access.accelerometer_xyz()
        return xyz
    elif installed_sensors.pimoroni_enviro:
        xyz = pimoroni_enviro_sensor_access.accelerometer_xyz()
        return xyz
    elif installed_sensors.pimoroni_lsm303d:
        xyz = lsm303d_sensor_access.accelerometer_xyz()
        return xyz
    else:
        return "NoSensor"


def get_magnetometer_xyz():
    """ Returns sensors Magnetometer XYZ. """
    if installed_sensors.raspberry_pi_sense_hat:
        xyz = rp_sense_hat_sensor_access.magnetometer_xyz()
        return xyz
    elif installed_sensors.pimoroni_enviro:
        xyz = pimoroni_enviro_sensor_access.magnetometer_xyz()
        return xyz
    elif installed_sensors.pimoroni_lsm303d:
        xyz = lsm303d_sensor_access.magnetometer_xyz()
        return xyz
    else:
        return "NoSensor"


def get_gyroscope_xyz():
    """ Returns sensors Gyroscope XYZ. """
    if installed_sensors.raspberry_pi_sense_hat:
        xyz = rp_sense_hat_sensor_access.gyroscope_xyz()
        return xyz
    else:
        return "NoSensor"
