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
from multiprocessing import Process
from operations_modules import app_cached_variables
from operations_modules import logger
from operations_modules import file_locations
from operations_modules.app_generic_functions import adjust_datetime
from operations_modules.sqlite_database import sql_execute_get_data
from http_server import server_plotly_graph_extras
from http_server import server_plotly_graph_variables
try:
    from plotly import subplots, offline, io as plotly_io
except ImportError as import_error:
    subplots, offline, plotly_io = None, None, None
    log_message = "**** Missing Plotly Graph Dependencies - There may be unintended side effects as a result: "
    logger.primary_logger.error(log_message + str(import_error))

plotly_io.templates.default = app_cached_variables.plotly_theme


def create_plotly_graph(new_graph_data):
    """ Create Plotly offline HTML Graph, based on user selections in the Web Portal Graphing section. """
    server_plotly_graph_variables.graph_creation_in_progress = True

    if new_graph_data.graph_table is "Triggers":
        new_graph_data.bypass_sql_skip = True

    logger.primary_logger.info("Plotly Graph Generation Started")
    graph_multiprocess = Process(target=_start_plotly_graph, args=(new_graph_data,))
    graph_multiprocess.start()
    graph_multiprocess.join()
    logger.primary_logger.info("Plotly Graph Generation Complete")
    server_plotly_graph_variables.graph_creation_in_progress = False


def _start_plotly_graph(graph_data):
    """ Creates a Offline Plotly graph from a SQL database. """
    logger.primary_logger.debug("SQL Columns: " + str(graph_data.graph_columns))
    logger.primary_logger.debug("SQL Table(s): " + graph_data.graph_table)
    logger.primary_logger.debug("SQL Start DateTime: " + graph_data.graph_start)
    logger.primary_logger.debug("SQL End DateTime: " + graph_data.graph_end)

    # Adjust dates to Database timezone in UTC 0
    sql_column_names = app_cached_variables.database_variables
    new_time_offset = graph_data.datetime_offset * -1
    get_sql_graph_start = adjust_datetime(graph_data.graph_start, new_time_offset)
    get_sql_graph_end = adjust_datetime(graph_data.graph_end, new_time_offset)

    for var_column in graph_data.graph_columns:
        var_sql_query = "SELECT " + var_column + \
                        " FROM " + graph_data.graph_table + \
                        " WHERE " + var_column + \
                        " IS NOT NULL AND DateTime BETWEEN datetime('" + get_sql_graph_start + \
                        "') AND datetime('" + get_sql_graph_end + \
                        "') AND ROWID % " + str(graph_data.sql_queries_skip + 1) + " = 0" + \
                        " LIMIT " + str(graph_data.max_sql_queries)

        var_time_sql_query = "SELECT " + sql_column_names.all_tables_datetime + \
                             " FROM " + graph_data.graph_table + \
                             " WHERE " + var_column + \
                             " IS NOT NULL AND DateTime BETWEEN datetime('" + get_sql_graph_start + \
                             "') AND datetime('" + get_sql_graph_end + \
                             "') AND ROWID % " + str(graph_data.sql_queries_skip + 1) + " = 0" + \
                             " LIMIT " + str(graph_data.max_sql_queries)

        # Get accompanying DateTime based on sensor data actually being present
        original_sql_column_date_time = sql_execute_get_data(var_time_sql_query)
        sql_column_date_time = []
        for var_d_time in original_sql_column_date_time:
            sql_column_date_time.append(adjust_datetime(var_d_time[0], graph_data.datetime_offset))
        if var_column == sql_column_names.all_tables_datetime:
            graph_data.sql_time = sql_column_date_time
        elif var_column == sql_column_names.ip:
            graph_data.sql_ip = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_ip_date_time = sql_column_date_time
        elif var_column == sql_column_names.sensor_name:
            graph_data.sql_host_name = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_host_name_date_time = sql_column_date_time
        elif var_column == sql_column_names.sensor_uptime:
            graph_data.sql_up_time = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_up_time_date_time = sql_column_date_time
        elif var_column == sql_column_names.system_temperature:
            graph_data.sql_cpu_temp = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_cpu_temp_date_time = sql_column_date_time
        elif var_column == sql_column_names.env_temperature:
            graph_data.sql_hat_temp = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_hat_temp_date_time = sql_column_date_time
        elif var_column == sql_column_names.pressure:
            graph_data.sql_pressure = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_pressure_date_time = sql_column_date_time
        elif var_column == sql_column_names.altitude:
            graph_data.sql_altitude = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_altitude_date_time = sql_column_date_time
        elif var_column == sql_column_names.humidity:
            graph_data.sql_humidity = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_humidity_date_time = sql_column_date_time
        elif var_column == sql_column_names.distance:
            graph_data.sql_distance = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_distance_date_time = sql_column_date_time
        elif var_column == sql_column_names.gas_resistance_index:
            graph_data.sql_gas_resistance = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_gas_resistance_date_time = sql_column_date_time
        elif var_column == sql_column_names.gas_oxidising:
            graph_data.sql_gas_oxidising = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_gas_oxidising_date_time = sql_column_date_time
        elif var_column == sql_column_names.gas_reducing:
            graph_data.sql_gas_reducing = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_gas_reducing_date_time = sql_column_date_time
        elif var_column == sql_column_names.gas_nh3:
            graph_data.sql_gas_nh3 = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_gas_nh3_date_time = sql_column_date_time
        elif var_column == sql_column_names.particulate_matter_1:
            graph_data.sql_pm_1 = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_pm_1_date_time = sql_column_date_time
        elif var_column == sql_column_names.particulate_matter_2_5:
            graph_data.sql_pm_2_5 = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_pm_2_5_date_time = sql_column_date_time
        elif var_column == sql_column_names.particulate_matter_10:
            graph_data.sql_pm_10 = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_pm_10_date_time = sql_column_date_time
        elif var_column == sql_column_names.lumen:
            graph_data.sql_lumen = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_lumen_date_time = sql_column_date_time
        elif var_column == sql_column_names.red:
            graph_data.sql_red = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_red_date_time = sql_column_date_time
        elif var_column == sql_column_names.orange:
            graph_data.sql_orange = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_orange_date_time = sql_column_date_time
        elif var_column == sql_column_names.yellow:
            graph_data.sql_yellow = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_yellow_date_time = sql_column_date_time
        elif var_column == sql_column_names.green:
            graph_data.sql_green = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_green_date_time = sql_column_date_time
        elif var_column == sql_column_names.blue:
            graph_data.sql_blue = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_blue_date_time = sql_column_date_time
        elif var_column == sql_column_names.violet:
            graph_data.sql_violet = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_violet_date_time = sql_column_date_time
        elif var_column == sql_column_names.ultra_violet_index:
            graph_data.sql_uv_index = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_uv_index_date_time = sql_column_date_time
        elif var_column == sql_column_names.ultra_violet_a:
            graph_data.sql_uv_a = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_uv_a_date_time = sql_column_date_time
        elif var_column == sql_column_names.ultra_violet_b:
            graph_data.sql_uv_b = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_uv_b_date_time = sql_column_date_time
        elif var_column == sql_column_names.acc_x:
            graph_data.sql_acc_x = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_acc_x_date_time = sql_column_date_time
        elif var_column == sql_column_names.acc_y:
            graph_data.sql_acc_y = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_acc_y_date_time = sql_column_date_time
        elif var_column == sql_column_names.acc_z:
            graph_data.sql_acc_z = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_acc_z_date_time = sql_column_date_time
        elif var_column == sql_column_names.mag_x:
            graph_data.sql_mg_x = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_mg_x_date_time = sql_column_date_time
        elif var_column == sql_column_names.mag_y:
            graph_data.sql_mg_y = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_mg_y_date_time = sql_column_date_time
        elif var_column == sql_column_names.mag_z:
            graph_data.sql_mg_z = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_mg_z_date_time = sql_column_date_time
        elif var_column == sql_column_names.gyro_x:
            graph_data.sql_gyro_x = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_gyro_x_date_time = sql_column_date_time
        elif var_column == sql_column_names.gyro_y:
            graph_data.sql_gyro_y = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_gyro_y_date_time = sql_column_date_time
        elif var_column == sql_column_names.gyro_z:
            graph_data.sql_gyro_z = _clean_sql_query_return(sql_execute_get_data(var_sql_query))
            graph_data.sql_gyro_z_date_time = sql_column_date_time
        else:
            logger.primary_logger.error(var_column + " - Does Not Exist")
    _plotly_graph(graph_data)


def _plotly_graph(graph_data):
    """ Create and open a HTML offline Plotly graph with the data provided. """
    graph_data.sub_plots = []
    graph_data.row_count = 0
    graph_data.graph_collection = []

    if len(graph_data.sql_time) > 1:
        try:
            server_plotly_graph_extras.add_plots(graph_data)

            fig = subplots.make_subplots(rows=graph_data.row_count, cols=1, subplot_titles=graph_data.sub_plots)

            for graph in graph_data.graph_collection:
                fig.add_trace(graph[0], graph[1], graph[2])
            if len(graph_data.sql_ip) > 1:
                start_text = "Plotly Graph for Sensor IP: "
                fig['layout'].update(title=start_text + str(graph_data.sql_ip[0]), title_font_size=25)

            if graph_data.row_count > 4:
                fig['layout'].update(height=2048)

            if graph_data.graph_table == app_cached_variables.database_variables.table_interval:
                plot_file_location = file_locations.plotly_graph_interval
            else:
                plot_file_location = file_locations.plotly_graph_triggers
            offline.plot(fig, filename=plot_file_location, auto_open=False)
            logger.primary_logger.debug("Plotly Graph Creation - OK")
        except Exception as error:
            logger.primary_logger.error("Plotly Graph Creation - Failed: " + str(error))
    else:
        logger.primary_logger.error("Graph Plot Failed - No SQL data found in Database within the selected Time Frame")


def check_form_columns(form_request):
    sql_column_selection = [app_cached_variables.database_variables.all_tables_datetime,
                            app_cached_variables.database_variables.sensor_name,
                            app_cached_variables.database_variables.ip]
    if form_request.get("SensorUptime") is not None:
        sql_column_selection.append(app_cached_variables.database_variables.sensor_uptime)

    if form_request.get("CPUTemp") is not None:
        sql_column_selection.append(app_cached_variables.database_variables.system_temperature)

    if form_request.get("EnvTemp") is not None:
        sql_column_selection.append(app_cached_variables.database_variables.env_temperature)

    if form_request.get("Pressure") is not None:
        sql_column_selection.append(app_cached_variables.database_variables.pressure)

    if form_request.get("Altitude") is not None:
        sql_column_selection.append(app_cached_variables.database_variables.altitude)

    if form_request.get("Humidity") is not None:
        sql_column_selection.append(app_cached_variables.database_variables.humidity)

    if form_request.get("Distance") is not None:
        sql_column_selection.append(app_cached_variables.database_variables.distance)

    if form_request.get("Gas") is not None:
        sql_column_selection.append(app_cached_variables.database_variables.gas_resistance_index)
        sql_column_selection.append(app_cached_variables.database_variables.gas_nh3)
        sql_column_selection.append(app_cached_variables.database_variables.gas_oxidising)
        sql_column_selection.append(app_cached_variables.database_variables.gas_reducing)

    if form_request.get("ParticulateMatter") is not None:
        sql_column_selection.append(app_cached_variables.database_variables.particulate_matter_1)
        sql_column_selection.append(app_cached_variables.database_variables.particulate_matter_2_5)
        sql_column_selection.append(app_cached_variables.database_variables.particulate_matter_10)

    if form_request.get("Lumen") is not None:
        sql_column_selection.append(app_cached_variables.database_variables.lumen)

    if form_request.get("Colours") is not None:
        sql_column_selection.append(app_cached_variables.database_variables.red)
        sql_column_selection.append(app_cached_variables.database_variables.orange)
        sql_column_selection.append(app_cached_variables.database_variables.yellow)
        sql_column_selection.append(app_cached_variables.database_variables.green)
        sql_column_selection.append(app_cached_variables.database_variables.blue)
        sql_column_selection.append(app_cached_variables.database_variables.violet)

    if form_request.get("UltraViolet") is not None:
        sql_column_selection.append(app_cached_variables.database_variables.ultra_violet_index)
        sql_column_selection.append(app_cached_variables.database_variables.ultra_violet_a)
        sql_column_selection.append(app_cached_variables.database_variables.ultra_violet_b)

    if form_request.get("Accelerometer") is not None:
        sql_column_selection.append(app_cached_variables.database_variables.acc_x)
        sql_column_selection.append(app_cached_variables.database_variables.acc_y)
        sql_column_selection.append(app_cached_variables.database_variables.acc_z)

    if form_request.get("Magnetometer") is not None:
        sql_column_selection.append(app_cached_variables.database_variables.mag_x)
        sql_column_selection.append(app_cached_variables.database_variables.mag_y)
        sql_column_selection.append(app_cached_variables.database_variables.mag_z)

    if form_request.get("Gyroscope") is not None:
        sql_column_selection.append(app_cached_variables.database_variables.gyro_x)
        sql_column_selection.append(app_cached_variables.database_variables.gyro_y)
        sql_column_selection.append(app_cached_variables.database_variables.gyro_z)
    return sql_column_selection


def _clean_sql_query_return(sql_data_tuple):
    cleaned_list = []
    for data in sql_data_tuple:
        cleaned_list.append(data[0])
    return cleaned_list
