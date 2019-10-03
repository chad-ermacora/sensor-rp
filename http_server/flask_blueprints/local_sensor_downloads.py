import os
from flask import Blueprint, send_file, request
from operations_modules import logger
from operations_modules import file_locations
from operations_modules import app_cached_variables
from operations_modules import app_generic_functions
from http_server import server_http_generic_functions

html_local_download_routes = Blueprint("html_local_download_routes", __name__)


@html_local_download_routes.route("/DownloadSQLDatabase")
def download_sensors_sql_database_zipped():
    logger.network_logger.debug("* Download SQL Database Accessed by " + str(request.remote_addr))
    try:
        file_name_part1 = app_cached_variables.ip.split(".")[-1] + app_cached_variables.hostname
        sql_filename = file_name_part1 + "SensorDatabase.sqlite"
        zip_filename = file_name_part1 + "SensorDatabase.zip"

        zip_content = app_generic_functions.get_file_content(file_locations.sensor_database, open_type="rb")
        app_generic_functions.zip_files([sql_filename], [zip_content], save_type="save_to_disk",
                                        file_location=file_locations.database_zipped)

        logger.network_logger.info("* Sensor SQL Database Sent to " + str(request.remote_addr))
        return send_file(file_locations.database_zipped, as_attachment=True,
                         attachment_filename=zip_filename)
    except Exception as error:
        logger.primary_logger.error("* Unable to Send Database to " + str(request.remote_addr) + ": " + str(error))
        return server_http_generic_functions.message_and_return("Error sending Database - " + str(error))


@html_local_download_routes.route("/DownloadZippedLogs")
def download_zipped_logs():
    logger.network_logger.debug("* Download Zip of all Logs Accessed by " + str(request.remote_addr))
    zip_name = "Logs_" + app_cached_variables.ip.split(".")[-1] + app_cached_variables.hostname + ".zip"
    try:
        primary_log = app_generic_functions.get_file_content(file_locations.primary_log)
        network_log = app_generic_functions.get_file_content(file_locations.network_log)
        sensors_log = app_generic_functions.get_file_content(file_locations.sensors_log)

        return_zip_file = app_generic_functions.zip_files([os.path.basename(file_locations.primary_log),
                                                           os.path.basename(file_locations.network_log),
                                                           os.path.basename(file_locations.sensors_log)],
                                                          [primary_log, network_log, sensors_log])

        return send_file(return_zip_file, as_attachment=True, attachment_filename=zip_name)
    except Exception as error:
        logger.primary_logger.error("* Unable to Zip Logs: " + str(error))
        return server_http_generic_functions.message_and_return("Unable to zip logs for Download", url="/GetLogsHTML")


@html_local_download_routes.route("/DownloadZippedEverything")
def download_zipped_everything():
    logger.network_logger.debug("* Download Zip of Everything Accessed by " + str(request.remote_addr))
    zip_name = "Everything_" + app_cached_variables.ip.split(".")[-1] + app_cached_variables.hostname + ".zip"
    database_name = "Database_" + app_cached_variables.hostname + ".sqlite"
    try:
        return_names = [database_name,
                        os.path.basename(file_locations.primary_log),
                        os.path.basename(file_locations.network_log),
                        os.path.basename(file_locations.sensors_log)]
        return_files = [app_generic_functions.get_file_content(file_locations.sensor_database, open_type="rb"),
                        app_generic_functions.get_file_content(file_locations.primary_log),
                        app_generic_functions.get_file_content(file_locations.network_log),
                        app_generic_functions.get_file_content(file_locations.sensors_log)]

        return_zip_file = app_generic_functions.zip_files(return_names, return_files)
        return send_file(return_zip_file, attachment_filename=zip_name, as_attachment=True)
    except Exception as error:
        logger.primary_logger.error("* Unable to Zip Logs: " + str(error))
        return server_http_generic_functions.message_and_return("Unable to zip logs for Download", url="/GetLogsHTML")