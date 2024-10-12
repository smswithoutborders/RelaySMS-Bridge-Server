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
        tuple: A tuple containing:
            - result (dict): A dictionary with decoded content.
            - error (None or Exception): None if successful, or the exception
              if an error occurred.
    """
    try:
        payload = base64.b64decode(content)
        result = {}

        content_switch = chr(payload[0])

        if content_switch == "0":
            len_public_key = struct.unpack("<i", payload[1:5])[0]
            result = {"public_key": payload[5 : 5 + len_public_key]}
        elif content_switch == "1":
            len_auth_code = struct.unpack("<i", payload[1:5])[0]
            auth_code = payload[5 : 5 + len_auth_code].decode("utf-8")
            bridge_letter = chr(payload[5 + len_auth_code])
            result = {
                "auth_code": auth_code,
                "bridge_letter": bridge_letter,
                "content_ciphertext": payload[6 + len_auth_code :],
            }
        elif content_switch == "2":
            result = {
                "bridge_letter": chr(payload[1]),
                "content_ciphertext": payload[2:],
            }
        else:
            raise ValueError(
                f"Invalid starting byte value: {content_switch}. Expected one of '0' (public key), "
                "'1' (auth code), or '2' (ciphertext)."
            )

        return result, None

    except Exception as e:
        return None, e
