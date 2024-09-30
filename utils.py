"""
A module containing utility functions and helper methods.

This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import os
from logutils import get_logger

logger = get_logger(__name__)


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
