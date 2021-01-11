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
from paho.mqtt import subscribe
import sqlite3
from operations_modules import logger
from operations_modules.app_generic_functions import thread_function
from operations_modules import app_cached_variables
from configuration_modules import app_config_access
from operations_modules.sqlite_database import write_to_sql_database
from operations_modules.file_locations import mqtt_subscriber_database as mqtt_sub_db_location


class CreateMQTTSubscriberTopicsRetrieval:
    def __init__(self):
        subscribed_topics_list = app_config_access.mqtt_subscriber_config.subscribed_topics_list
        broker_address = app_config_access.mqtt_subscriber_config.broker_address
        broker_server_port = app_config_access.mqtt_subscriber_config.broker_server_port
        mqtt_qos = app_config_access.mqtt_subscriber_config.mqtt_subscriber_qos
        cb_auth = None

        if app_config_access.mqtt_subscriber_config.enable_broker_auth:
            broker_user = app_config_access.mqtt_subscriber_config.broker_user
            broker_password = None
            if app_config_access.mqtt_subscriber_config.broker_user != "":
                if app_config_access.mqtt_subscriber_config.broker_password != "":
                    broker_password = app_config_access.mqtt_subscriber_config.broker_password
                cb_auth = {'username': broker_user, 'password': broker_password}

        subscribe.callback(self._on_mqtt_message, subscribed_topics_list, hostname=broker_address,
                           port=broker_server_port, auth=cb_auth, tls=None, qos=mqtt_qos)

    @staticmethod
    def _on_mqtt_message(client, userdata, message):
        logger.mqtt_subscriber_logger.info(str(message.topic) + " = " + str(message.payload.decode("UTF-8")))
        if app_config_access.mqtt_subscriber_config.enable_mqtt_sql_recording:
            _write_mqtt_message_to_sql_database(message)


def start_mqtt_subscriber_server():
    """ Starts MQTT Subscriber server. """
    if app_config_access.mqtt_subscriber_config.enable_mqtt_subscriber:
        thread_function(CreateMQTTSubscriberTopicsRetrieval)
        logger.primary_logger.info(" -- MQTT Subscriber Started")
    else:
        logger.primary_logger.debug("MQTT Subscriber Disabled in Configuration")


def _write_mqtt_message_to_sql_database(mqtt_message):
    try:
        sensor_topic_as_list = str(mqtt_message.topic).strip().split("/")
        if len(sensor_topic_as_list) > 0:
            current_utc_datetime = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            sensor_id_str = sensor_topic_as_list[0]
            try:
                column_and_data_dic = eval(str(mqtt_message.payload.decode("UTF-8")))
                if type(column_and_data_dic) != dict:
                    column_and_data_dic = {sensor_topic_as_list[-1]: str(mqtt_message.payload.decode("UTF-8"))}
            except Exception as error:
                log_msg = "Unable to Convert MQTT subscription data to writable SQL data: "
                logger.network_logger.warning(log_msg + str(error))
                column_and_data_dic = {"Decode": "Error"}

            columns_sql_str = ""
            data_sql_value_place_marks = ""
            data_list = [current_utc_datetime]
            for column_name, column_data in column_and_data_dic.items():
                if column_name.replace("_", "JJ").isalnum():
                    _check_sql_table_column_exists(sensor_id_str, column_name)
                    columns_sql_str += column_name + ","
                    data_sql_value_place_marks += "?,"
                    data_list.append(str(column_data))
                else:
                    log_msg = "MQTT Subscriber SQL Recording: Incorrect sensor ID or Type - "
                    logger.network_logger.warning(log_msg + "Must be Alphanumeric")

            if len(columns_sql_str) > 0:
                columns_sql_str = columns_sql_str[:-1]
                data_sql_value_place_marks = data_sql_value_place_marks[:-1]
                sql_string = "INSERT OR IGNORE INTO " + sensor_id_str + " (" + \
                             app_cached_variables.database_variables.all_tables_datetime + "," + \
                             columns_sql_str + ") VALUES (?," + data_sql_value_place_marks + ")"
                write_to_sql_database(sql_string, data_list, sql_database_location=mqtt_sub_db_location)
    except Exception as error:
        logger.primary_logger.error("MQTT Subscriber Recording Failure: " + str(error))


def _check_sql_table_column_exists(table_name, column_text):
    db_connection = sqlite3.connect(mqtt_sub_db_location)
    db_cursor = db_connection.cursor()
    sql_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='" + table_name + "';"
    db_cursor.execute(sql_query)

    if len(db_cursor.fetchall()) == 0:
        db_cursor.execute("CREATE TABLE {tn} ({nf} {ft})".format(tn=table_name, nf="DateTime", ft="TEXT"))
        for column in app_cached_variables.database_variables.get_sensor_columns_list():
            try:
                db_cursor.execute("ALTER TABLE '" + table_name + "' ADD COLUMN " + column + " TEXT")
            except Exception as error:
                if str(error)[:21] != "duplicate column name":
                    logger.primary_logger.error("MQTT Subscriber SQL Database Error: " + str(error))

    try:
        db_cursor.execute("ALTER TABLE '" + table_name + "' ADD COLUMN " + column_text + " TEXT")
    except Exception as error:
        if str(error)[:21] != "duplicate column name":
            logger.primary_logger.error("MQTT Subscriber SQL Database Error: " + str(error))
    db_connection.commit()
    db_connection.close()
