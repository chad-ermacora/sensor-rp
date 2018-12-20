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
import os
import sqlite3

from operations_modules import operations_config
from operations_modules import operations_logger
from operations_modules import operations_upgrades

create_important_files = [operations_config.last_updated_file_location,
                          operations_config.old_version_file_location]


class CreateRefinedVersion:
    def __init__(self):
        self.major_version = 0
        self.feature_version = 0
        self.minor_version = 0

    def get_version(self, version):
        try:
            old_version_split = version.split(".")
            self.major_version = old_version_split[0]
            self.feature_version = int(old_version_split[1])
            self.minor_version = int(old_version_split[2])
        except Exception as error:
            operations_logger.primary_logger.warning("Missing version file or Invalid format: " +
                                                     operations_config.old_version_file_location +
                                                     " - Configuration files reset to defaults")
            operations_logger.primary_logger.debug(str(error))

    def get_version_str(self):
        version_str = str(self.major_version) + "." + str(self.feature_version) + "." + str(self.minor_version)
        return version_str


def check_database_structure():
    operations_logger.primary_logger.info("Running DB Checks")
    try:
        db_connection = sqlite3.connect(operations_config.sensor_database_location)
        db_cursor = db_connection.cursor()

        for table in operations_config.sql_tables:
            try:
                # Create or update table
                db_cursor.execute("CREATE TABLE {tn} ({nf} {ft})".format(tn=table, nf="DateTime", ft="TEXT"))
                operations_logger.primary_logger.debug("Table '" + table + "' - Created")

            except Exception as error:
                operations_logger.primary_logger.debug("Error on Table '" + table + "' - " + str(error))

            for column in operations_config.sensor_sql_columns:
                # Create or update table columns
                _check_sql_table_and_column(table, column, db_cursor)

        table = operations_config.other_sql_table
        try:
            # Create or update 'Other' table
            db_cursor.execute("CREATE TABLE {tn} ({nf} {ft})".format(tn=table, nf="DateTime", ft="TEXT"))
            operations_logger.primary_logger.debug("Table '" + table + "' - Created")

        except Exception as error:
            operations_logger.primary_logger.debug("Error on Table '" + table + "' - " + str(error))

        for column in operations_config.other_sql_columns:
            # Create or update table columns
            _check_sql_table_and_column(table, column, db_cursor)

        db_connection.commit()
        db_connection.close()
    except Exception as error:
        operations_logger.primary_logger.error("DB Connection Failed: " + str(error))


def _check_sql_table_and_column(table_name, column_name, db_cursor):
    try:
        db_cursor.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}".format(tn=table_name,
                                                                           cn=column_name,
                                                                           ct="TEXT"))
        operations_logger.primary_logger.debug("COLUMN " + column_name + " - Created")
    except Exception as error:
        operations_logger.primary_logger.debug("COLUMN " + column_name + " - " + str(error))


def run_upgrade_checks():
    operations_logger.primary_logger.debug("Checking required packages")
    old_version = CreateRefinedVersion()
    old_version.get_version(operations_config.get_old_version())
    no_changes = True

    if old_version.major_version == "Alpha":
        if old_version.feature_version == 22:
            if old_version.minor_version < 9:
                no_changes = False
                operations_upgrades.update_ver_a_22_8()
                operations_logger.primary_logger.info("Upgraded: " + old_version.get_version_str() +
                                                      " || New: " + operations_config.version)
            elif 21 > old_version.minor_version > 8:
                no_changes = False
                operations_upgrades.update_ver_a_22_20()
                operations_logger.primary_logger.info("Upgraded Old: " + old_version.get_version_str() +
                                                      " || New: " + operations_config.version)

    if no_changes:
        operations_logger.primary_logger.info("Upgrade detected || No configuration changes || Old: " +
                                              old_version.get_version_str() + " New: " + operations_config.version)
    _write_program_version_to_file()
    restart_services()


def restart_services():
    """ Reloads systemd service files & restarts all sensor program services. """
    os.system(operations_config.restart_sensor_services_command)


def _write_program_version_to_file():
    operations_logger.primary_logger.debug("Current version file updating")
    current_version_file = open(operations_config.old_version_file_location, 'w')
    current_version_file.write(operations_config.version)
    current_version_file.close()


def check_missing_files():
    for file in create_important_files:
        if os.path.isfile(file):
            pass
        else:
            operations_logger.primary_logger.warning("Added missing file: " + file)
            os.system("touch " + file)

    os.system("bash /opt/kootnet-sensors/scripts/set_permissions.sh")
