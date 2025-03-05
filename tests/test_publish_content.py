"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import os
import smtplib
import base64
import struct

import pytest
import requests
from smswithoutborders_libsig.keypairs import x25519
from smswithoutborders_libsig.ratchets import Ratchets, States, HEADERS

from logutils import get_logger

logger = get_logger(__name__)


def load_binary(file_path):
    """Load binary data from a file."""
    try:
        with open(file_path, "rb") as fb:
            return fb.read()
    except IOError as e:
        logger.error("Error reading from %s: %s", file_path, e)
        raise


def encrypt_and_encode_payload(publish_shared_key, peer_publish_pub_key, content):
    state_file_path = "client_state.bin"
    if not os.path.isfile(state_file_path):
        state = States()
        Ratchets.alice_init(
            state, publish_shared_key, peer_publish_pub_key, "client.db"
        )
    else:
        state = States.deserialize(load_binary(state_file_path))

    header, content_ciphertext = Ratchets.encrypt(
        state=state, data=content.encode("utf-8"), AD=peer_publish_pub_key
    )
    serialized_header = header.serialize()
    len_header = len(serialized_header)
    return (
        base64.b64encode(
            struct.pack("<i", len_header) + serialized_header + content_ciphertext
        ).decode("utf-8"),
        state.serialize(),
    )


def send_via_http(url, payload):
    response = requests.post(url, json={"data": payload})
    return response.status_code, response.text


def send_via_smtp(smtp_server, port, sender_email, recipient_email, payload):
    try:
        with smtplib.SMTP(smtp_server, port) as server:
            message = f"Subject: Encrypted Payload\n\n{payload}"
            server.sendmail(sender_email, recipient_email, message)
        return "Email sent successfully"
    except Exception as e:
        return f"Error sending email: {e}"


@pytest.fixture
def keypair(tmp_path):
    key_path = tmp_path / "test_keystore"
    return x25519(str(key_path))


@pytest.fixture
def shared_keys(keypair):
    pk = keypair.init()
    return pk, keypair


def test_encryption(shared_keys):
    pub_pk, keypair = shared_keys
    shared_key = keypair.agree(pub_pk)
    message = "Test message"
    encrypted_payload, _ = encrypt_and_encode_payload(shared_key, pub_pk, message)
    assert isinstance(encrypted_payload, str)


@pytest.fixture
def http_payload():
    return "test_payload"


def test_send_http(http_payload):
    url = ""
    status_code, response_text = send_via_http(url, http_payload)
    assert status_code in [200, 201, 400, 404]


@pytest.fixture
def smtp_payload():
    return "test_payload"


def test_send_smtp(smtp_payload):
    response = send_via_smtp(
        "smtp.example.com",
        587,
        "sender@example.com",
        "receiver@example.com",
        smtp_payload,
    )
    assert "Error" not in response
