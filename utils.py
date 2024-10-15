"""
A module containing utility functions and helper methods.

This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import importlib.util
import json
from logutils import get_logger

logger = get_logger(__name__)

BRIDGES_FILE_PATH = os.path.join("resources", "bridges.json")


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
