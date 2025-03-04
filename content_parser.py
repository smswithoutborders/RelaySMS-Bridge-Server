"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import base64
import struct
import types
from collections import namedtuple

FormatSpec = namedtuple("FormatSpec", ["key", "fmt", "decoding", "use_chr"])


def parse_payload(payload: bytes, format_spec: list) -> dict:
    """
    Parses a binary payload based on the provided format specification.

    Args:
        payload (bytes): The binary data to parse.
        format_spec (list[FormatSpec]): List of FormatSpec named tuples defining parsing rules.

    Returns:
        dict: Parsed key-value pairs from the payload.
    """
    result = {}
    offset = 1

    for spec in format_spec:
        fmt = spec.fmt
        if isinstance(fmt, types.FunctionType):
            fmt = fmt(result)

        if isinstance(fmt, int):
            value = payload[offset] if fmt == 1 else payload[offset : offset + fmt]
            offset += fmt
            if fmt == 1 and spec.use_chr:
                value = chr(value)
        else:
            size = struct.calcsize(fmt)
            value = struct.unpack(fmt, payload[offset : offset + size])[0]
            offset += size

        if spec.decoding:
            value = value.decode(spec.decoding)

        result[spec.key] = value

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
            FormatSpec(key="len_public_key", fmt="<i", decoding=None, use_chr=False),
            FormatSpec(
                key="public_key",
                fmt=lambda d: d["len_public_key"],
                decoding=None,
                use_chr=False,
            ),
        ],
        1: [
            FormatSpec(key="len_auth_code", fmt=1, decoding=None, use_chr=False),
            FormatSpec(
                key="auth_code",
                fmt=lambda d: d["len_auth_code"],
                decoding="utf-8",
                use_chr=False,
            ),
        ],
        2: [
            FormatSpec(key="len_auth_code", fmt=1, decoding=None, use_chr=False),
            FormatSpec(key="len_ciphertext", fmt="<i", decoding=None, use_chr=False),
            FormatSpec(key="bridge_letter", fmt=1, decoding=None, use_chr=True),
            FormatSpec(
                key="auth_code",
                fmt=lambda d: d["len_auth_code"],
                decoding="utf-8",
                use_chr=False,
            ),
            FormatSpec(
                key="content_ciphertext",
                fmt=lambda d: d["len_ciphertext"],
                decoding=None,
                use_chr=False,
            ),
        ],
        3: [
            FormatSpec(key="len_ciphertext", fmt="<i", decoding=None, use_chr=False),
            FormatSpec(key="bridge_letter", fmt=1, decoding=None, use_chr=True),
            FormatSpec(
                key="content_ciphertext",
                fmt=lambda d: d["len_ciphertext"],
                decoding=None,
                use_chr=False,
            ),
        ],
    }

    switch_value = payload[0]
    if switch_value not in parsers:
        return None, ValueError(f"Invalid content switch: {switch_value}")

    result = parse_payload(payload, parsers[switch_value])
    return result, None


def decode_v1(payload: bytes) -> tuple:
    """Decodes version 1 content.

    Args:
        payload (bytes): The binary data to decode.

    Returns:
        tuple: A dictionary of parsed values and an optional error.
    """
    version = f"v{payload[0] - 9}"
    switch_value = payload[1]
    parsers = {
        0: [
            FormatSpec(key="len_public_key", fmt=1, decoding=None, use_chr=False),
            FormatSpec(key="len_ciphertext", fmt="<H", decoding=None, use_chr=False),
            FormatSpec(key="bridge_letter", fmt=1, decoding=None, use_chr=True),
            FormatSpec(key="skid", fmt=1, decoding=None, use_chr=False),
            FormatSpec(
                key="public_key",
                fmt=lambda d: d["len_public_key"],
                decoding=None,
                use_chr=False,
            ),
            FormatSpec(
                key="content_ciphertext",
                fmt=lambda d: d["len_ciphertext"],
                decoding=None,
                use_chr=False,
            ),
        ],
        1: [
            FormatSpec(key="len_ciphertext", fmt="<H", decoding=None, use_chr=False),
            FormatSpec(key="bridge_letter", fmt=1, decoding=None, use_chr=True),
            FormatSpec(
                key="content_ciphertext",
                fmt=lambda d: d["len_ciphertext"],
                decoding=None,
                use_chr=False,
            ),
        ],
    }

    if switch_value not in parsers:
        return None, ValueError(f"Invalid switch value: {switch_value}")

    result = parse_payload(payload[1:], parsers[switch_value])
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
        first_byte = payload[0]
        if first_byte >= 10:
            return decode_v1(payload)
        return decode_v0(payload)
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
