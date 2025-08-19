"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import requests
import phonenumbers
from phonenumbers import geocoder
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from utils import get_env_var, get_logger

TWILIO_ACCOUNT_SID = get_env_var("TWILIO_ACCOUNT_SID", strict=True)
TWILIO_AUTH_TOKEN = get_env_var("TWILIO_AUTH_TOKEN", strict=True)
TWILIO_SERVICE_SID = get_env_var("TWILIO_SERVICE_SID", strict=True)
TWILIO_PHONE_NUMBER = get_env_var("TWILIO_PHONE_NUMBER", strict=True)

QUEUEDROID_API_URL = get_env_var(
    "QUEUEDROID_API_URL", default_value="https://api.queuedroid.com/v1/messages/send"
)
QUEUEDROID_API_KEY = get_env_var("QUEUEDROID_API_KEY")
QUEUEDROID_EXCHANGE_ID = get_env_var("QUEUEDROID_EXCHANGE_ID")
QUEUEDROID_SUPPORTED_REGION_CODES = get_env_var("QUEUEDROID_SUPPORTED_REGION_CODES")

logger = get_logger(__name__)


def send_with_twilio(phone_number: str, message: str) -> bool:
    """
    Sends a message using Twilio to a specified phone number.

    Args:
        phone_number (str): The recipient's phone number in E.164 format (e.g., +237123456789).
        message (str): The content to be sent to the specified phone number.

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    try:
        message_response = client.messages.create(
            body=message, from_=TWILIO_PHONE_NUMBER, to=phone_number
        )
        status = message_response.status

        if status in ("accepted", "pending", "queued"):
            logger.info("Message sent successfully.")
            return True

        logger.error("Failed to send message. Twilio status: %s", status)

        return True
    except TwilioRestException as exc:
        logger.error("Error sending message with Twilio: %s", exc)
        return False


def send_with_queuedroid(phone_number: str, message: str) -> bool:
    """
    Sends a message using Queuedroid to a specified phone number.

    Args:
        phone_number (str): The recipient's phone number in E.164 format (e.g., +237123456789).
        message (str): The content to be sent to the specified phone number.

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    try:
        data = {
            "content": message,
            "exchange_id": QUEUEDROID_EXCHANGE_ID,
            "phone_number": phone_number,
        }
        headers = {"Authorization": f"Bearer {QUEUEDROID_API_KEY}"}
        response = requests.post(
            QUEUEDROID_API_URL, json=data, headers=headers, timeout=10
        )

        if response.ok:
            logger.info("Message sent successfully via Queuedroid.")
            return True
        response.raise_for_status()
        return False
    except requests.RequestException as exc:
        logger.exception("Error sending message via Queuedroid: %s", exc)
        return False


def get_phonenumber_region_code(phone_number: str) -> str:
    """
    Get the region code for a given phone number.

    Args:
        phone_number (str): The phone number in E.164 format.

    Returns:
        str: The ISO 3166-1 alpha-2 region code corresponding to the phone number.
    """
    parsed_number = phonenumbers.parse(phone_number)
    return geocoder.region_code_for_number(parsed_number)
