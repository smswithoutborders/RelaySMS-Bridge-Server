"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import base64
import struct
import pytest
from content_parser import (
    decode_v0,
    decode_v1,
    decode_content,
    extract_content,
    extract_content_v2,
    extract_content_v3,
)


@pytest.mark.parametrize(
    "payload, expected",
    [
        (
            b"\x00" + struct.pack("<i", 4) + b"key1",
            {"len_public_key": 4, "public_key": b"key1"},
        ),
        (b"\x01\x03abc", {"len_auth_code": 3, "auth_code": "abc"}),
    ],
)
def test_decode_v0_valid(payload, expected):
    result, error = decode_v0(payload)
    assert error is None
    assert result == expected


@pytest.mark.parametrize("payload", [b"\x05someinvaliddata"])
def test_decode_v0_invalid(payload):
    result, error = decode_v0(payload)
    assert result is None
    assert isinstance(error, ValueError)


@pytest.mark.parametrize(
    "payload, expected",
    [
        (
            b"\x0a\x00\x05" + struct.pack("<H", 10) + b"e\x02key12ciphertext",
            {
                "version": "v1",
                "len_public_key": 5,
                "len_ciphertext": 10,
                "bridge_letter": "e",
                "skid": 2,
                "public_key": b"key12",
                "content_ciphertext": b"ciphertext",
                "language": "",
            },
        ),
        (
            b"\x0a\x01" + struct.pack("<H", 4) + b"edatafr",
            {
                "version": "v1",
                "len_ciphertext": 4,
                "bridge_letter": "e",
                "content_ciphertext": b"data",
                "language": "fr",
            },
        ),
        (
            b"\x0a\x00\x05" + struct.pack("<H", 10) + b"e\x02key12ciphertext",
            {
                "version": "v1",
                "len_public_key": 5,
                "len_ciphertext": 10,
                "bridge_letter": "e",
                "skid": 2,
                "public_key": b"key12",
                "content_ciphertext": b"ciphertext",
                "language": "",
            },
        ),
        (
            b"\x0a\x01" + struct.pack("<H", 4) + b"edatafr",
            {
                "version": "v1",
                "len_ciphertext": 4,
                "bridge_letter": "e",
                "content_ciphertext": b"data",
                "language": "fr",
            },
        ),
    ],
)
def test_decode_v1_valid(payload, expected):
    result, error = decode_v1(payload)
    assert error is None
    assert result == expected


@pytest.mark.parametrize("payload", [b"\x0a\x05invalid"])
def test_decode_v1_invalid(payload):
    result, error = decode_v1(payload)
    assert result is None
    assert isinstance(error, ValueError)


@pytest.mark.parametrize(
    "content, expected",
    [
        (
            base64.b64encode(b"\x03\x01" + struct.pack("<H", 6) + b"tabcdef").decode(),
            {
                "version": "v3",
                "len_ciphertext": 6,
                "bridge_letter": "t",
                "content_ciphertext": b"abcdef",
                "language": "",
            },
        ),
        (
            base64.b64encode(b"\x0a\x01" + struct.pack("<H", 6) + b"tabcdef").decode(),
            {
                "version": "v1",
                "len_ciphertext": 6,
                "bridge_letter": "t",
                "content_ciphertext": b"abcdef",
                "language": "",
            },
        ),
    ],
)
def test_decode_content_valid(content, expected):
    result, error = decode_content(content)
    assert error is None
    assert result == expected


@pytest.mark.parametrize(
    "content, expected",
    [
        (
            base64.b64encode(b"\x00" + struct.pack("<i", 3) + b"xyz").decode(),
            "Unsupported version marker: 0",
        ),
    ],
)
def test_decode_content_v0_deprecated(content, expected):
    result, error = decode_content(content)
    assert error == expected
    assert result is None


@pytest.mark.parametrize("content", ["invalidbase64=="])
def test_decode_content_invalid(content):
    result, error = decode_content(content)
    assert result is None
    assert error is not None


@pytest.mark.parametrize(
    "bridge_name, content, expected",
    [
        (
            "email_bridge",
            "part1:part2:part3:part4:part5",
            ("part1", "part2", "part3", "part4", "part5"),
        ),
        ("email_bridge", "wrong:format:data", None),
        ("unknown_bridge", "part1:part2:part3:part4:part5", None),
    ],
)
def test_extract_content(bridge_name, content, expected):
    result, error = extract_content(bridge_name, content)
    if expected is None:
        assert result is None
        assert isinstance(error, str)
    else:
        assert result == expected
        assert error is None


@pytest.mark.parametrize(
    "bridge_name, content, image_length, expected",
    [
        (
            "email_bridge",
            struct.pack("<HHHBH", 2, 2, 3, 7, 4) + b"toccbccsubjectbody",
            0,
            {
                "to": "to",
                "cc": "cc",
                "bcc": "bcc",
                "subject": "subject",
                "body": "body",
                "image": b"",
            },
        ),
        (
            "email_bridge",
            b"imagedata" + struct.pack("<HHHBH", 2, 0, 0, 7, 4) + b"tosubjectbody",
            9,
            {
                "to": "to",
                "cc": "",
                "bcc": "",
                "subject": "subject",
                "body": "body",
                "image": b"imagedata",
            },
        ),
    ],
)
def test_extract_content_v2(bridge_name, content, image_length, expected):
    result, error = extract_content_v2(bridge_name, content, image_length)
    assert error is None
    assert result == expected


@pytest.mark.parametrize(
    "bridge_name, content, expected",
    [
        (
            "email_bridge",
            struct.pack("<BHBH", 0b00000000, 2, 7, 4) + b"tosubjectbody",
            {"to": "to", "cc": "", "bcc": "", "subject": "subject", "body": "body"},
        ),
        (
            "email_bridge",
            struct.pack("<BHHHBH", 0b00000011, 2, 2, 3, 7, 4) + b"toccbccsubjectbody",
            {
                "to": "to",
                "cc": "cc",
                "bcc": "bcc",
                "subject": "subject",
                "body": "body",
            },
        ),
        (
            "email_bridge",
            struct.pack("<BHHBH", 0b00000001, 2, 2, 7, 4) + b"toccsubjectbody",
            {
                "to": "to",
                "cc": "cc",
                "bcc": "",
                "subject": "subject",
                "body": "body",
            },
        ),
        (
            "email_bridge",
            struct.pack("<BHHBH", 0b00000010, 2, 3, 7, 4) + b"tobccsubjectbody",
            {
                "to": "to",
                "cc": "",
                "bcc": "bcc",
                "subject": "subject",
                "body": "body",
            },
        ),
    ],
)
def test_extract_content_v3(bridge_name, content, expected):
    result, error = extract_content_v3(bridge_name, content)
    assert error is None
    assert result == expected
