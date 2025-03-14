"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import importlib.util
import json
import configparser
from functools import wraps
from peewee import DatabaseError
import pymysql
from logutils import get_logger

logger = get_logger(__name__)

BRIDGES_FILE_PATH = os.path.join("resources", "bridges.json")
CONFIG_PATH = os.path.join("configs", "config.ini")

config = configparser.ConfigParser()
config.read(CONFIG_PATH)


def get_config_value(section: str, key: str, fallback: str = None) -> str:
    """
    Retrieves a value from the config file.

    Args:
        section (str): The section in the config file.
        key (str): The key to retrieve the value for.
        fallback (str, optional): The fallback value if the key is not found. Defaults to None.

    Returns:
        str: The retrieved value or the fallback if not found.
    """
    try:
        return config.get(section, key, fallback=fallback)
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logger.error("Error retrieving config value [%s] %s: %s", section, key, str(e))
        return fallback


def get_env_var(env_name: str, default_value: str = None, strict: bool = False) -> str:
    """
    Retrieves the value of an environment variable.

    Args:
        env_name (str): The name of the environment variable to retrieve.
        default_value (str, optional): The value to return if the variable is not found
            and strict is False. Defaults to None.
        strict (bool, optional): If True, raises an error if the variable is not found.
            Defaults to False.

    Returns:
        str: The value of the environment variable, or default_value if not found and
        strict is False.
    """

    try:
        value = (
            os.environ[env_name]
            if strict
            else os.environ.get(env_name) or default_value
        )

        if strict and (value is None or value.strip() == ""):
            raise ValueError(f"Environment variable {env_name} is missing or empty.")

        return value
    except KeyError as error:
        logger.error("Environment variable '%s' not found: %s", env_name, error)
        raise
    except ValueError as error:
        logger.error("Environment variable '%s' is empty or None: %s", env_name, error)
        raise


def load_bridges_from_file(file_path):
    """Load bridges from a JSON file.

    Args:
        file_path (str): The path to the file containing the bridge data.

    Returns:
        dict: A dictionary containing the bridge data.
    """

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            bridge_data = json.load(file)
        return bridge_data
    except FileNotFoundError:
        logger.exception("File '%s' not found.", file_path)
        return {}
    except json.JSONDecodeError:
        logger.exception("Error decoding JSON from '%s'.", file_path)
        return {}


def mask_sensitive_info(value):
    """
    Masks all but the last three digits of the given value.

    Args:
        value (str): The string to be masked.

    Returns:
        str: The masked string with all but the last three digits replaced by '*'.
    """
    if not value:
        return value
    return "*" * (len(value) - 3) + value[-3:]


def get_bridge_details_by_shortcode(shortcode):
    """
    Get the bridge details corresponding to the given shortcode.

    Args:
        shortcode (str): The shortcode to look up.

    Returns:
        tuple:
            - bridge_details (dict): Details of the bridge if found.
            - error_message (str): Error message if bridge is not found,
    """
    bridge_details = load_bridges_from_file(BRIDGES_FILE_PATH)

    for bridge in bridge_details:
        if bridge.get("shortcode") == shortcode:
            return bridge, None

    available_bridges = ", ".join(
        f"'{bridge['shortcode']}' for {bridge['name']}" for bridge in bridge_details
    )
    error_message = (
        f"No bridge found for shortcode '{shortcode}'. "
        f"Available shortcodes: {available_bridges}"
    )

    return None, error_message


def import_module_dynamically(module_name, module_file_path, bridge_directory):
    """
    Dynamically imports a module from a specified file path.

    Args:
        module_name (str): The name of the module to import.
        module_file_path (str): The file path to the module.
        bridge_directory (str): The directory to be added to sys.path for importing the module.

    Returns:
        module: The imported module.
    """
    if bridge_directory not in sys.path:
        sys.path.insert(0, bridge_directory)

    spec = importlib.util.spec_from_file_location(module_name, module_file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return module


def create_tables(models):
    """
    Creates tables for the given models if they don't
        exist in their specified database.

    Args:
        models(list): A list of Peewee Model classes.
    """
    if not models:
        logger.warning("No models provided for table creation.")
        return

    try:
        databases = {}
        for model in models:
            database = model._meta.database
            if database not in databases:
                databases[database] = []
            databases[database].append(model)

        for database, db_models in databases.items():
            with database.atomic():
                existing_tables = set(database.get_tables())
                tables_to_create = [
                    model
                    for model in db_models
                    if model._meta.table_name not in existing_tables
                ]

                if tables_to_create:
                    database.create_tables(tables_to_create)
                    logger.info(
                        "Created tables: %s",
                        [model._meta.table_name for model in tables_to_create],
                    )
                else:
                    logger.debug("No new tables to create.")

    except DatabaseError as e:
        logger.error("An error occurred while creating tables: %s", e)


def ensure_database_exists(host, user, password, database_name):
    """
    Decorator that ensures a MySQL database exists before executing a function.

    Args:
        host (str): The host address of the MySQL server.
        user (str): The username for connecting to the MySQL server.
        password (str): The password for connecting to the MySQL server.
        database_name (str): The name of the database to ensure existence.

    Returns:
        function: Decorated function.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                connection = pymysql.connect(
                    host=host,
                    user=user,
                    password=password,
                    charset="utf8mb4",
                    collation="utf8mb4_unicode_ci",
                )
                with connection.cursor() as cursor:
                    sql = "CREATE DATABASE IF NOT EXISTS " + database_name
                    cursor.execute(sql)

                logger.debug(
                    "Database %s created successfully (if it didn't exist)",
                    database_name,
                )

            except pymysql.MySQLError as error:
                logger.error("Failed to create database: %s", error)

            finally:
                connection.close()

            return func(*args, **kwargs)

        return wrapper

    return decorator
