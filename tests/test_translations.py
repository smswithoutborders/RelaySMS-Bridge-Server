"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import pytest
from translations import Localization

TEST_LOCALIZATION_DATA = """
[en]
greeting = Hello, welcome!
farewell = Goodbye, see you soon.

[fr]
greeting = Bonjour, bienvenue !
farewell = Au revoir, à bientôt.

[de]
greeting = Hallo, willkommen!
"""


@pytest.fixture
def temp_ini_file(tmp_path):
    """
    Creates a temporary localization INI file for testing.
    """
    ini_path = tmp_path / "localization.ini"
    with open(ini_path, "w", encoding="utf-8") as f:
        f.write(TEST_LOCALIZATION_DATA.strip())
    return ini_path


@pytest.fixture
def localization(temp_ini_file):
    """
    Returns a Localization instance using the temporary INI file.
    """
    return Localization(file_path=temp_ini_file, default_locale="en")


# --- TESTS ---


def test_translate_existing_key(localization):
    """
    Test retrieving valid translations.
    """
    assert localization.translate("greeting") == "Hello, welcome!"

    localization.set_locale("fr")
    assert localization.translate("greeting") == "Bonjour, bienvenue !"

    localization.set_locale("de")
    assert localization.translate("greeting") == "Hallo, willkommen!"


def test_translate_missing_key(localization):
    """
    Test behavior when requesting a missing translation key.
    """
    with pytest.raises(
        NotImplementedError,
        match="Translation key 'unknown_key' is not available under the 'en' locale",
    ):
        localization.translate("unknown_key")


def test_set_locale_valid(localization):
    """
    Test setting a valid locale.
    """
    localization.set_locale("fr")
    assert localization.translate("farewell") == "Au revoir, à bientôt."


def test_set_locale_invalid(localization):
    """
    Test behavior when setting an unsupported locale.
    """
    with pytest.raises(
        NotImplementedError, match="Localization for language 'es' is not implemented"
    ):
        localization.set_locale("es")


def test_missing_ini_file():
    """
    Test error handling when the INI file is missing.
    """
    with pytest.raises(
        FileNotFoundError, match="Localization file 'missing.ini' is missing"
    ):
        Localization(file_path="missing.ini")
