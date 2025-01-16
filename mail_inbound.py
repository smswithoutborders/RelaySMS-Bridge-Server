"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import ssl
import re
import time
import socket
import imaplib
import traceback

from imap_tools import (
    AND,
    MailBox,
    MailboxLoginError,
    MailboxLogoutError,
    MailMessage,
)
from email_reply_parser import EmailReplyParser
from vault_grpc_client import authenticate_bridge_entity, encrypt_payload
from utils import get_logger, get_env_var

IMAP_SERVER = get_env_var("BRIDGE_IMAP_SERVER", strict=True)
IMAP_PORT = int(get_env_var("BRIDGE_IMAP_PORT", 993))
IMAP_USERNAME = get_env_var("BRIDGE_IMAP_USERNAME", strict=True)
IMAP_PASSWORD = get_env_var("BRIDGE_IMAP_PASSWORD", strict=True)
MAIL_FOLDER = get_env_var("BRIDGE_MAIL_FOLDER", "INBOX")
SSL_CERTIFICATE = get_env_var("SSL_CERTIFICATE_FILE", strict=True)
SSL_KEY = get_env_var("SSL_CERTIFICATE_KEY_FILE", strict=True)

logger = get_logger("mail.inbound")

PHONE_NUMBER_REGEX = re.compile(r"<(\d+)_bridge@relaysms\.me>")


def authenticate_phonenumber(phone_number: str) -> tuple[bool, str]:
    """
    Authenticate a phone number using the bridge entity.

    Args:
        phone_number (str): The phone number to authenticate.

    Returns:
        tuple[bool, str]: Authentication success status and message.
    """
    authentication_response, authentication_error = authenticate_bridge_entity(
        phone_number=phone_number
    )

    if authentication_error:
        raise RuntimeError(
            f"{authentication_error.details()} -- {authentication_error.code()}"
        )

    return authentication_response.success, authentication_response.message


def delete_email(mailbox: MailBox, email_uid: int) -> None:
    """
    Delete an email from the mailbox.

    Args:
        mailbox (MailBox): The mailbox object.
        email_uid (int): The UID of the email to delete.
    """
    try:
        if email_uid:
            mailbox.delete(email_uid)
            logger.debug("Successfully deleted email UID: %s", email_uid)
    except Exception as e:
        logger.error("Error deleting email UID %s: %s", email_uid, e)
        raise


def format_recipients(recipients: list) -> list[str]:
    """
    Format recipients into readable strings.

    Args:
        recipients (list): List of recipient objects.

    Returns:
        list[str]: Formatted recipient strings.
    """
    return [
        f"{recipient.name} <{recipient.email}>" if recipient.name else recipient.email
        for recipient in (recipients or [])
    ]


def process_incoming_email(mailbox: MailBox, email: MailMessage) -> None:
    """
    Process an incoming email.

    Args:
        mailbox (MailBox): The mailbox object.
        email (MailMessage): The email object to process.
    """
    email_uid = email.uid
    message_body = EmailReplyParser.parse_reply(email.text)
    subject = email.subject
    sender = (
        f"{email.from_values.name} <{email.from_values.email}>"
        if email.from_values.name
        else email.from_values.email
    )
    to_recipients = format_recipients(email.to_values)
    cc_recipients = format_recipients(email.cc_values)
    bcc_recipients = format_recipients(email.bcc_values)

    if not to_recipients:
        logger.warning("No valid 'To' recipients found. Discarding email.")
        delete_email(mailbox, email_uid)
        return

    regex_match = PHONE_NUMBER_REGEX.search(to_recipients[0])
    phone_number = regex_match.group(1) if regex_match else None

    if not phone_number:
        logger.info(
            "Invalid alias reply address detected: '%s'. Discarding message.",
            to_recipients[0],
        )
        delete_email(mailbox, email_uid)
        return

    try:
        authenticated, auth_message = authenticate_phonenumber(f"+{phone_number}")
        if not authenticated:
            logger.error("Authentication failed: %s", auth_message)
            delete_email(mailbox, email_uid)
            return
    except RuntimeError as err:
        logger.error("Authentication error: %s", err)
        return

    payload = f"{sender}:{','.join(cc_recipients)}:{','.join(bcc_recipients)}:{subject}:{message_body}"
    logger.debug("Constructed Payload: %s", payload)

    encrypted_payload = encrypt_payload(payload)
    logger.debug("Encrypted Payload: %s", encrypted_payload)


def main() -> None:
    """
    Main function to run the email processing loop.
    """
    ssl_context = ssl.create_default_context()
    ssl_context.load_cert_chain(certfile=SSL_CERTIFICATE, keyfile=SSL_KEY)

    while True:
        connection_start_time = time.monotonic()
        connection_live_time = 0.0
        try:
            with MailBox(IMAP_SERVER, IMAP_PORT, ssl_context=ssl_context).login(
                IMAP_USERNAME, IMAP_PASSWORD, MAIL_FOLDER
            ) as mailbox:
                logger.info(
                    "Connected to mailbox %s on %s", IMAP_SERVER, time.asctime()
                )
                while connection_live_time < 29 * 60:
                    try:
                        responses = mailbox.idle.wait(timeout=20)
                        if responses:
                            logger.debug("IMAP IDLE responses: %s", responses)

                        for msg in mailbox.fetch(
                            criteria=AND(seen=False),
                            bulk=50,
                            mark_seen=False,
                        ):
                            process_incoming_email(mailbox, msg)

                    except KeyboardInterrupt:
                        logger.info("Exiting gracefully...")
                        return
                    connection_live_time = time.monotonic() - connection_start_time
        except (
            TimeoutError,
            ConnectionError,
            imaplib.IMAP4.abort,
            MailboxLoginError,
            MailboxLogoutError,
            socket.herror,
            socket.gaierror,
            socket.timeout,
        ) as e:
            logger.error("Error occurred: %s", e)
            logger.error(traceback.format_exc())
            logger.info("Reconnecting in a minute...")
            time.sleep(60)


if __name__ == "__main__":
    main()
