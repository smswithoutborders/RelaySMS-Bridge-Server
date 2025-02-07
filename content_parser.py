"""
Content Parser.

This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import base64
import struct


def decode_v0(payload: bytes) -> tuple:
    """Decodes version 0 content.

    Args:
        payload (bytes): The payload to destructure.

    Returns:
        tuple: (result, error)
    """
    result = {}

    match payload[0]:
        case 0:
            len_public_key = struct.unpack("<i", payload[1:5])[0]
            public_key = payload[5 : 5 + len_public_key]
            result = {"public_key": public_key}

        case 1:
            len_auth_code = payload[1]
            auth_code = payload[2 : 2 + len_auth_code].decode("utf-8")
            result = {"auth_code": auth_code}

        case 2:
            len_auth_code = payload[1]
            len_ciphertext = struct.unpack("<i", payload[2:6])[0]
            bridge_letter = chr(payload[6])

            auth_code_start = 7
            auth_code_end = ciphertext_start = auth_code_start + len_auth_code
            ciphertext_end = ciphertext_start + len_ciphertext

            auth_code = payload[auth_code_start:auth_code_end].decode("utf-8")
            content_ciphertext = payload[ciphertext_start:ciphertext_end]

            result = {
                "auth_code": auth_code,
                "bridge_letter": bridge_letter,
                "content_ciphertext": content_ciphertext,
            }

        case 3:
            len_ciphertext = struct.unpack("<i", payload[1:5])[0]
            bridge_letter = chr(payload[5])
            content_ciphertext = payload[6 : 6 + len_ciphertext]

            result = {
                "bridge_letter": bridge_letter,
                "content_ciphertext": content_ciphertext,
            }

        case _:
            raise ValueError(
                f"Invalid content switch: {payload[0]}. "
                "Expected 0 (auth request), "
                "1 (auth code), "
                "2 (auth code and payload), "
                "or 3 (payload only)."
            )

    return result, None


def decode_v1(payload: bytes) -> tuple:
    """Decodes version 1 content.

    Args:
        payload (bytes): The payload to destructure.

    Returns:
        tuple: (result, error)
    """
    result = {}
    version = f"v{payload[0]-9}"
    switch_value = payload[1]

    match switch_value:
        case 0:
            len_public_key = payload[2]
            len_ciphertext = struct.unpack("<H", payload[3:5])[0]
            bridge_letter = chr(payload[5])
            skid = payload[6]

            public_key_start = 7
            public_key_end = ciphertext_start = public_key_start + len_public_key
            public_key = payload[public_key_start:public_key_end]

            ciphertext_end = ciphertext_start + len_ciphertext
            content_ciphertext = payload[ciphertext_start:ciphertext_end]

            result = {
                "version": version,
                "bridge_letter": bridge_letter,
                "content_ciphertext": content_ciphertext,
                "skid": skid,
                "public_key": public_key,
            }

        case 1:
            len_ciphertext = struct.unpack("<H", payload[2:4])[0]
            bridge_letter = chr(payload[4])

            ciphertext_start = 5
            content_ciphertext = payload[ciphertext_start:]

            result = {
                "version": version,
                "bridge_letter": bridge_letter,
                "content_ciphertext": content_ciphertext,
            }

        case _:
            raise ValueError(
                f"Invalid switch value: {switch_value}. "
                "Expected 0 (auth request and payload), "
                "or 1 (payload only)."
            )

    return result, None


def decode_content(content: str) -> tuple:
    """
    Decodes a base64-encoded content payload.

    Args:
        content (str): Base64 encoded string representing the content to be decoded.

    Returns:
        tuple:
            - result (dict): A dictionary with decoded content.
            - error (None or Exception): None if successful, or the exception
              if an error occurred.
    """
    try:
        payload = base64.b64decode(content)

        first_byte = payload[0]
        if first_byte >= 10:
            version = first_byte
            match version:
                case 10:
                    return decode_v1(payload)
                case _:
                    raise ValueError(f"Unsupported version {version}")

        return decode_v0(payload)

    except Exception as e:
        return None, e


def extract_content(bridge_name, content):
    """
    Extracts components from the given content based on the specified bridge name.

    Args:
        bridge_name (str): The name of the bridge.
        content (str): The content string to be parsed.

    Returns:
        tuple:
            - A tuple of extracted components if successful,
                or None if the bridge name is invalid or the content format is incorrect.
            - An error message (str) if there is an issue, or None if successful.
    """
    if bridge_name == "email_bridge":
        # Email format: 'to:cc:bcc:subject:body'
        parts = content.split(":", 4)
        if len(parts) != 5:
            return None, "Email content must have exactly 5 parts."
        to_email, cc_email, bcc_email, subject, body = parts
        return (to_email, cc_email, bcc_email, subject, body), None

    return None, "Invalid service_type. Must be 'email_bridge'."
