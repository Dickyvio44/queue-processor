# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Python wraps to windows/linux schema generation scripts for services
"""
from __future__ import print_function

import os

from build.utils.process_runner import run_process_and_log


PATH_TO_DIR = os.path.dirname(os.path.realpath(__file__))


def run_sql(connection, sql, logger):
    """
    Execute an SQL command and then commit the changes to the database
    :param connection: The connection to the database
    :param sql: The sql command to run as a string
    :param logger: Where to log the errors to
    :return: True / False depending on command success
    """
    from sqlalchemy.exc import OperationalError
    logger.info("Running sql: %s" % sql)
    try:
        connection.execute(sql)
        connection.commit()
    except OperationalError as exp:
        logger.error("SQL command failed with exception: %s" % exp)
        return False
    logger.info("SQL command completed successfully")
    return True


def get_sql_from_file(sql_file_location):
    """
    Runs a sql file using the database client
    :param sql_file_location: file path to the sql file
    :return: The contents of the sql file as a string
    """
    with open(sql_file_location, 'r') as sql_file:
        return " ".join(sql_file.readlines())


def get_test_user_sql():
    """
    Generate sql to add a new user to the database
    :return: True if process completed successfully
    """
    from utils.settings import MYSQL_SETTINGS
    user_to_add = MYSQL_SETTINGS.username
    sql_commands = ["GRANT ALL ON *.* TO '{0}'@'localhost' "
                    "IDENTIFIED BY '{1}';".format(user_to_add, MYSQL_SETTINGS.password),
                    "FLUSH PRIVILEGES;"]

    return '\n'.join(sql_commands)


def generate_schema(project_root_path, logger):
    """
    Call django migrations to create testing database schema
    :param project_root_path: The full path to the root directory of the project
    :param logger: log handler
    :return: True: exit code of script was 0
             False: exit code of script was non-zero
    """
    path_to_manage = os.path.join(project_root_path, 'WebApp', 'autoreduce_webapp', 'manage.py')
    for database in ['admin', 'sessions', 'auth', 'reduction_viewer', 'reduction_variables']:
        logger.info("Migrating %s" % database)
        if run_process_and_log(['python', path_to_manage, 'makemigrations', database]) is False:
            logger.error("Error encountered when makingmigrations for %s" % database)
            return False
        if run_process_and_log(['python', path_to_manage, 'migrate', database]) is False:
            logger.error("Error encountered when migrating %s" % database)
            return False

    logger.info("Adding super user")
    # Custom manage.py command
    if run_process_and_log(['python', path_to_manage, 'add_super']) is False:
        logger.error("Error encountered when adding super user")
        return False
    logger.info("Database migrated successfully")
    return True
