"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import logging
from db_models import Publications

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_publication_entry(
    platform_name,
    source,
    status,
    country_code=None,
    gateway_client=None,
    date_created=None,
):
    """
    Store a new publication entry with correct status.
    Args:
        country_code (str): Country code.
        platform_name (str): Platform name.
        source (str): Source of publication.
        gateway_client (str): Gateway client.
        status (str): "published" if successful, "failed" if not.
    """
    publication = Publications.create(
        country_code=country_code,
        platform_name=platform_name,
        source=source,
        status=status,
        gateway_client=gateway_client,
    )

    logger.info("Successfully logged publication")

    return publication
