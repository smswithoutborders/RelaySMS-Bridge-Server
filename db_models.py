"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import datetime
from peewee import Model, CharField, DateTimeField
from db import connect
from utils import create_tables, get_logger

logger = get_logger(__name__)

database = connect()


class Publications(Model):
    """Model representing the Publications Table."""

    country_code = CharField(null=True)
    platform_name = CharField()
    source = CharField()
    status = CharField()
    gateway_client = CharField(null=True)
    date_created = DateTimeField(default=datetime.datetime.now)

    class Meta:
        """Meta class to define database connection and table name."""

        database = database
        table_name = "publications"

    @classmethod
    def create_publication(cls, **kwargs):
        """
        Creates a new publication entry in the database.

        Args:
            **kwargs: Key-value pairs for publication attributes.

        Returns:
            Publications: The created publication entry.
        """
        cls.create(**kwargs)
        logger.info("Successfully created publication entry.")


create_tables([Publications])
