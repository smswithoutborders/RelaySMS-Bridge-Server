"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import base64
import struct
from collections import namedtuple

FormatSpec = namedtuple("FormatSpec", ["key", "fmt", "decoding"])


def parse_payload(payload: bytes, format_spec: list) -> dict:
    """
    Parses a binary payload based on the provided format specification.

    Args:
        payload (bytes): The binary data to parse.
        format_spec (list[FormatSpec]): List of FormatSpec named tuples defining parsing rules.

    Returns:
        dict: Parsed key-value pairs from the payload.
    """
    result, offset = {}, 0
    total_len = len(payload)

    for spec in format_spec:
        fmt = spec.fmt(result) if callable(spec.fmt) else spec.fmt
        if isinstance(fmt, int):
            fmt = f"{fmt}s"

        size = struct.calcsize(fmt)
        if offset + size > total_len:
            break

        (value,) = struct.unpack_from(fmt, payload, offset)
        offset += size

        if spec.decoding and isinstance(value, (bytes, bytearray)):
            value = value.decode(spec.decoding)

        result[spec.key] = value

    for spec in format_spec:
        if spec.key not in result:
            default = "" if spec.decoding else b""
            result[spec.key] = default

    return result


def decode_v0(payload: bytes) -> tuple:
    """Decodes version 0 content.

    Args:
        payload (bytes): The binary data to decode.

    Returns:
        tuple: A dictionary of parsed values and an optional error.
    """
    parsers = {
        0: [
            FormatSpec(key="len_public_key", fmt="<i", decoding=None),
            FormatSpec(
                key="public_key", fmt=lambda d: d["len_public_key"], decoding=None
            ),
        ],
        1: [
            FormatSpec(key="len_auth_code", fmt="<B", decoding=None),
            FormatSpec(
                key="auth_code", fmt=lambda d: d["len_auth_code"], decoding="utf-8"
            ),
        ],
        2: [
            FormatSpec(
                key="len_auth_code",
                fmt=1,
                decoding=None,
            ),
            FormatSpec(key="len_ciphertext", fmt="<i", decoding=None),
            FormatSpec(key="bridge_letter", fmt=1, decoding=None),
            FormatSpec(
                key="auth_code", fmt=lambda d: d["len_auth_code"], decoding="utf-8"
            ),
            FormatSpec(
                key="content_ciphertext",
                fmt=lambda d: d["len_ciphertext"],
                decoding=None,
            ),
        ],
        3: [
            FormatSpec(key="len_ciphertext", fmt="<i", decoding=None),
            FormatSpec(key="bridge_letter", fmt=1, decoding=None),
            FormatSpec(
                key="content_ciphertext",
                fmt=lambda d: d["len_ciphertext"],
                decoding=None,
            ),
        ],
    }

    switch_value = payload[0]
    if switch_value not in parsers:
        return None, ValueError(f"Invalid content switch: {switch_value}")

    result = parse_payload(payload[1:], parsers[switch_value])
    return result, None


def decode_v1(payload: bytes) -> tuple:
    """Decodes version 1 content.

    Args:
        payload (bytes): The binary data to decode.

    Returns:
        tuple: A dictionary of parsed values and an optional error.
    """
    version = f"v{payload[0] - 9}" if payload[0] == 10 else f"v{payload[0]}"
    switch_value = payload[1]
    parsers = {
        0: [
            FormatSpec(key="len_public_key", fmt="<B", decoding=None),
            FormatSpec(
                key="len_ciphertext",
                fmt="<H",
                decoding=None,
            ),
            FormatSpec(key="bridge_letter", fmt=1, decoding="ascii"),
            FormatSpec(key="skid", fmt="<B", decoding=None),
            FormatSpec(
                key="public_key",
                fmt=lambda d: d["len_public_key"],
                decoding=None,
            ),
            FormatSpec(
                key="content_ciphertext",
                fmt=lambda d: d["len_ciphertext"],
                decoding=None,
            ),
            FormatSpec(key="language", fmt=2, decoding="ascii"),
        ],
        1: [
            FormatSpec(key="len_ciphertext", fmt="<H", decoding=None),
            FormatSpec(key="bridge_letter", fmt=1, decoding="ascii"),
            FormatSpec(
                key="content_ciphertext",
                fmt=lambda d: d["len_ciphertext"],
                decoding=None,
            ),
            FormatSpec(key="language", fmt=2, decoding="ascii"),
        ],
    }

    if switch_value not in parsers:
        return None, ValueError(f"Invalid switch value: {switch_value}")

    result = parse_payload(payload[2:], parsers[switch_value])
    result["version"] = version
    return result, None


def decode_content(content: str) -> tuple:
    """Decodes a base64-encoded content payload.

    Args:
        content (str): The base64-encoded string to decode.

    Returns:
        tuple: A dictionary of parsed values and an optional error.
    """
    try:
        payload = base64.b64decode(content)
        version_marker = payload[0]
        if version_marker not in [3, 10]:
            return None, f"Unsupported version marker: {version_marker}"
        return decode_v1(payload)
    except Exception as e:
        return None, e


def extract_content(bridge_name: str, content: str) -> tuple:
    """Extracts components based on the specified bridge name.

    Args:
        bridge_name (str): The bridge identifier.
        content (str): The content string to extract from.

    Returns:
        tuple: A tuple of extracted values or an error message.
    """
    if bridge_name == "email_bridge":
        parts = content.split(":", 4)
        if len(parts) != 5:
            return None, "Email content must have exactly 5 parts."
        return tuple(parts), None
    return None, "Invalid bridge name."


def extract_content_v3(bridge_name: str, content: bytes) -> tuple:
    """Extracts components based on the specified bridge name for v3.

    Args:
        bridge_name (str): The bridge identifier.
        content (bytes): The binary content to extract from.

    Returns:
        tuple: A tuple of extracted values or an error message.
    """
    if bridge_name != "email_bridge":
        return None, "Invalid bridge name."

    bitmap = content[0]

    fields_present = {
        "cc": bool(bitmap & 0b00000001),
        "bcc": bool(bitmap & 0b00000010),
    }

    format_spec = [
        FormatSpec(key="length_to", fmt="<H", decoding=None),
    ]

    if fields_present["cc"]:
        format_spec.append(FormatSpec(key="length_cc", fmt="<H", decoding=None))
    if fields_present["bcc"]:
        format_spec.append(FormatSpec(key="length_bcc", fmt="<H", decoding=None))

    format_spec.extend(
        [
            FormatSpec(key="length_subject", fmt="<B", decoding=None),
            FormatSpec(key="length_body", fmt="<H", decoding=None),
        ]
    )

    format_spec.append(
        FormatSpec(key="to", fmt=lambda d: d["length_to"], decoding="utf-8")
    )
    if fields_present["cc"]:
        format_spec.append(
            FormatSpec(key="cc", fmt=lambda d: d["length_cc"], decoding="utf-8")
        )
    if fields_present["bcc"]:
        format_spec.append(
            FormatSpec(key="bcc", fmt=lambda d: d["length_bcc"], decoding="utf-8")
        )
    format_spec.extend(
        [
            FormatSpec(
                key="subject", fmt=lambda d: d["length_subject"], decoding="utf-8"
            ),
            FormatSpec(key="body", fmt=lambda d: d["length_body"], decoding="utf-8"),
        ]
    )

    try:
        result = parse_payload(content[1:], format_spec)
        return {
            "to": result.get("to", ""),
            "cc": result.get("cc", ""),
            "bcc": result.get("bcc", ""),
            "subject": result.get("subject", ""),
            "body": result.get("body", ""),
        }, None
    except Exception as e:
        return None, e
