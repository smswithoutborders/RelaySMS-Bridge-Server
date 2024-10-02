"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import os
import subprocess
import argparse
from utils import load_bridges_from_file, get_logger

logger = get_logger("scripts.download_bridges")

BRIDGES_FILE_PATH = os.path.join("resources", "bridges.json")
BRIDGE_DIRECTORY = "bridges"


def download_bridge(bridge_name=None):
    """Download all bridges or a single bridge by name.

    Args:
        bridge_name (str, optional): The name of a bridge to download. If not provided,
            all bridges will be downloaded.

    Returns:
        None
    """
    bridges = load_bridges_from_file(BRIDGES_FILE_PATH)

    if bridge_name:
        bridges = [bridge for bridge in bridges if bridge["name"] == bridge_name]

        if not bridges:
            raise ValueError(f"Bridge with name '{bridge_name}' not found.")

    os.makedirs(BRIDGE_DIRECTORY, exist_ok=True)

    for bridge in bridges:
        bridge_path = os.path.join(BRIDGE_DIRECTORY, bridge["name"])

        if os.path.exists(bridge_path):
            logger.info("Updating bridge '%s' ...", bridge["name"])
            subprocess.run(["git", "-C", bridge_path, "pull"], check=True)
        else:
            logger.info("Downloading bridge '%s' ...", bridge["name"])
            subprocess.run(["git", "clone", bridge["url"], bridge_path], check=True)


def main():
    """Main function to handle argument parsing and execute the download."""
    parser = argparse.ArgumentParser(description="Download or update bridges.")
    parser.add_argument(
        "bridge_name",
        nargs="?",
        default=None,
        help="Name of the bridge to download. If not provided, all bridges will be downloaded.",
    )
    args = parser.parse_args()

    download_bridge(args.bridge_name)


if __name__ == "__main__":
    main()
