"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import asyncio
import base64
import datetime
import imaplib
import re
import socket
import ssl
import struct
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import sentry_sdk
from email_reply_parser import EmailReplyParser
from imap_tools import (
    AND,
    MailBox,
    MailboxLoginError,
    MailboxLogoutError,
    MailMessage,
)

from sms_outbound import (
    QUEUEDROID_SUPPORTED_REGION_CODES,
    get_phonenumber_region_code,
    send_with_queuedroid,
    send_with_twilio,
)
from translations import Localization
from utils import get_config_value, get_env_var, get_logger
from vault_grpc_client import authenticate_bridge_entity, encrypt_payload

IMAP_SERVER = get_env_var("BRIDGE_IMAP_SERVER", strict=True)
IMAP_PORT = int(get_env_var("BRIDGE_IMAP_PORT", 993))
IMAP_USERNAME = get_env_var("BRIDGE_IMAP_USERNAME", strict=True)
IMAP_PASSWORD = get_env_var("BRIDGE_IMAP_PASSWORD", strict=True)
MAIL_FOLDERS = [
    folder.strip()
    for folder in get_env_var("BRIDGE_IMAP_MAIL_FOLDER", "INBOX").split(",")
]
SSL_CERTIFICATE = get_env_var("SSL_CERTIFICATE_FILE", strict=True)
SSL_KEY = get_env_var("SSL_CERTIFICATE_KEY_FILE", strict=True)
MOCK_REPLY_SMS = get_env_var("MOCK_REPLY_SMS")
MOCK_REPLY_SMS = (
    MOCK_REPLY_SMS.lower() == "true" if MOCK_REPLY_SMS is not None else False
)

ALIAS_PHONENUMBER_PREFIX = get_env_var("ALIAS_PHONE_NUMBER_PREFIX", "")
ALIAS_PHONENUMBER_SUFFIX = get_env_var("ALIAS_PHONE_NUMBER_SUFFIX", "")
SIMPLELOGIN_PRIMARY_DOMAIN = get_env_var("SL_PRIMARY_DOMAIN", "relaysms.me")

ALIAS_EMAIL_PATTERNS = re.compile(
    get_config_value("patterns", "alias_email").format(
        suffix=re.escape(ALIAS_PHONENUMBER_SUFFIX),
        prefix=re.escape(ALIAS_PHONENUMBER_PREFIX),
        domain=re.escape(SIMPLELOGIN_PRIMARY_DOMAIN),
    )
)

SMS_REPLY_TEMPLATE = get_config_value("templates", "sms_reply")

logger = get_logger("mail.inbound")

loc = Localization()
t = loc.translate

sentry_sdk.init(
    dsn=get_env_var("SENTRY_DSN"),
    server_name="Bridge",
    traces_sample_rate=float(
        get_env_var("SENTRY_TRACES_SAMPLE_RATE", default_value=1.0)
    ),
    profiles_sample_rate=float(
        get_env_var("SENTRY_PROFILES_SAMPLE_RATE", default_value=1.0)
    ),
)

sentry_sdk.set_tag("project", "Bridge")
sentry_sdk.set_tag("service_name", "Bridge Service")


def authenticate_phonenumber(phone_number: str):
    """
    Authenticate a phone number using the bridge entity.

    Args:
        phone_number (str): The phone number to authenticate.
    """
    response, error = authenticate_bridge_entity(phone_number=phone_number)

    if error:
        return (None, f"{error.details()} -- {error.code()}")

    return response, None


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
    receivers = email.to

    if not email.from_:
        logger.warning("No valid 'From' found. Discarding email.")
        delete_email(mailbox, email_uid)
        return

    if not receivers:
        logger.warning("No valid 'To' found. Discarding email.")
        delete_email(mailbox, email_uid)
        return

    sender = (
        f"{email.from_values.name} <{email.from_values.email}>"
        if email.from_values.name
        else email.from_values.email
    )
    cc_recipients = ",".join(format_recipients(email.cc_values))
    bcc_recipients = ",".join(format_recipients(email.bcc_values))
    email_timestamp = email.date.timestamp()

    phone_number = None
    alias_address = None

    for receiver in receivers:
        match = ALIAS_EMAIL_PATTERNS.search(receiver)
        if match:
            phone_number = match.group(1)
            alias_address = receiver
            break

        logger.debug("Invalid alias email: %s.", receiver)

    if not phone_number:
        logger.info("Invalid alias reply. Discarding message.")
        delete_email(mailbox, email_uid)
        return

    e_164_phonenumber = f"+{phone_number}"

    authenticated, auth_error = authenticate_phonenumber(e_164_phonenumber)

    if not authenticated or not authenticated.success:
        logger.error("Authentication failed: %s", auth_error or authenticated.message)
        delete_email(mailbox, email_uid)
        return

    reply_payload = (
        alias_address + sender + cc_recipients + bcc_recipients + subject + message_body
    )

    logger.debug("Constructed Payload: %s", reply_payload)

    encrypted_payload, encryption_error = encrypt_payload(
        phone_number=e_164_phonenumber, payload_plaintext=reply_payload
    )

    if encryption_error:
        logger.error("Encryption failed: %s", encryption_error)
        delete_email(mailbox, email_uid)
        return

    logger.debug("Encrypted Payload: %s", encrypted_payload.payload_ciphertext)

    bridge_letter = b"e"
    content_ciphertext = base64.b64decode(encrypted_payload.payload_ciphertext)

    try:
        loc.set_locale(authenticated.language)
    except ValueError as e:
        logger.error(e)

    sms_payload = SMS_REPLY_TEMPLATE.format(
        reply_prompt=t("sms_reply_prompt"),
        payload=base64.b64encode(
            bytes([len(alias_address)])
            + bytes([len(sender)])
            + bytes([len(cc_recipients)])
            + bytes([len(bcc_recipients)])
            + bytes([len(subject)])
            + struct.pack("<H", len(message_body))
            + struct.pack("<H", len(content_ciphertext))
            + bridge_letter
            + content_ciphertext
        ).decode("utf-8"),
        timestamp=email_timestamp,
    ).replace("\\n", "\n")

    region_code = get_phonenumber_region_code(e_164_phonenumber)

    if MOCK_REPLY_SMS:
        is_sent = True
        sentry_sdk.capture_message(sms_payload, level="info")
    elif region_code in QUEUEDROID_SUPPORTED_REGION_CODES:
        is_sent = False
        is_sent = send_with_queuedroid(e_164_phonenumber, message=sms_payload)
    else:
        is_sent = False
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            logger.info("Attempting to send SMS (attempt %d/%d)", attempt, max_retries)
            is_sent = send_with_twilio(e_164_phonenumber, message=sms_payload)

            if is_sent:
                logger.info("SMS sent successfully on attempt %d", attempt)
                break

            logger.warning("SMS sending failed on attempt %d", attempt)
            if attempt < max_retries:
                logger.info("Retrying SMS sending...")
                time.sleep(2)
            else:
                logger.error("All %d SMS sending attempts failed", max_retries)

    if is_sent:
        delete_email(mailbox, email_uid)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        publish_alert = f"Successfully processed and sent reply at {timestamp}."
        sentry_sdk.capture_message(publish_alert, level="info")
        logger.info(publish_alert)
    else:
        delete_email(mailbox, email_uid)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        failure_alert = (
            f"Failed to send SMS after {max_retries} attempts. "
            f"Email deleted at {timestamp}."
        )
        sentry_sdk.capture_message(failure_alert, level="warning")
        logger.warning(failure_alert)


def check_folder(folder: str, ssl_context) -> None:
    """
    Check a specific folder for emails.

    Args:
        folder (str): The folder name to check.
        ssl_context: The SSL context for the connection.
    """
    try:
        with MailBox(IMAP_SERVER, IMAP_PORT, ssl_context=ssl_context).login(
            IMAP_USERNAME, IMAP_PASSWORD
        ) as mailbox:
            mailbox.folder.set(folder)
            logger.debug("Checking folder: %s", folder)

            for msg in mailbox.fetch(
                criteria=AND(seen=False),
                bulk=50,
                mark_seen=False,
            ):
                process_incoming_email(mailbox, msg)
    except Exception as e:
        logger.error("Error checking folder %s: %s", folder, e)


async def check_all_folders_async(ssl_context) -> None:
    """
    Check all folders asynchronously.

    Args:
        ssl_context: The SSL context for the connection.
    """
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=len(MAIL_FOLDERS)) as executor:
        tasks = [
            loop.run_in_executor(executor, check_folder, folder, ssl_context)
            for folder in MAIL_FOLDERS
        ]
        await asyncio.gather(*tasks)


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
                IMAP_USERNAME, IMAP_PASSWORD
            ) as mailbox:
                logger.info(
                    "Connected to mailbox %s on %s", IMAP_SERVER, time.asctime()
                )
                while connection_live_time < 29 * 60:
                    try:
                        responses = mailbox.idle.wait(timeout=20)
                        if responses:
                            logger.debug("IMAP IDLE responses: %s", responses)

                        asyncio.run(check_all_folders_async(ssl_context))

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
