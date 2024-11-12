"""
Content Parser.

This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import base64
import struct


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
