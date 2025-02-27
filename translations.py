"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import configparser
import os


class Localization:
    """A class to manage translations."""

    def __init__(self, file_path=None, default_locale="en"):
        """Initialize the Localization manager.

        Args:
            file_path (str): Path to the localization file. Defaults to "configs/localization.ini"
            default_locale (str): Default language code.
        """
        self.file_path = file_path or os.path.join("configs", "localization.ini")
        self.set_locale(default_locale)

    def set_locale(self, locale_code):
        """
        Set the active locale for translations.

        Args:
            locale_code (str): The language code to use.

        Raises:
            NotImplementedError: If the specified locale is not available in the INI file.
        """
        self.locale_code = locale_code
        config = configparser.ConfigParser()

        if not os.path.exists(self.file_path):
            raise FileNotFoundError(
                f"Localization file '{self.file_path}' is missing. Please provide a valid file."
            )

        config.read(self.file_path)

        if locale_code not in config:
            raise NotImplementedError(
                f"Localization for language '{locale_code}' is not implemented. "
                f"Available options: {', '.join(config.sections())}"
            )

    def translate(self, key):
        """
        Retrieve the translation for a given key.

        Args:
            key (str): The translation key.

        Returns:
            str: The translated string.

        Raises:
            NotImplementedError: If the key is not found in the specified locale section.
        """
        config = configparser.ConfigParser()
        config.read(self.file_path)

        if not config.has_section(self.locale_code):
            raise NotImplementedError(
                f"Localization for language '{self.locale_code}' is missing in '{self.file_path}'."
            )

        if not config.has_option(self.locale_code, key):
            raise NotImplementedError(
                f"Translation key '{key}' is not available under the '{self.locale_code}' locale. "
                f"Ensure it is defined in '{self.file_path}'."
            )

        return config.get(self.locale_code, key)
