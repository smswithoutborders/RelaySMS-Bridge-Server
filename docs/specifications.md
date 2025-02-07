# Bridge Specification

## Table of Contents

- [Content Format](#content-format)
- [Supported Payload Versions](#supported-payload-versions)
- [Payload Format V0](#payload-format-v0)
  - [Auth Request Payload](#auth-request-payload)
  - [Auth Code Payload](#auth-code-payload)
  - [Auth Code and Payload](#auth-code-and-payload)
  - [Payload Only](#payload-only)
- [Payload Format V1](#payload-format-v1)
  - [Auth Request and Payload](#auth-request-and-payload)
  - [Payload Only](#payload-only-1)
- [Reply Data Format](#reply-data-format)
  - [Content Format](#content-format-1)
  - [Payload Format](#payload-format)
- [SMS Payload Format](#sms-payload-format)
  - [Payload Format](#payload-format-1)

## Content Format

The Bridge supports the following content formats:

1. **Email**: `to:cc:bcc:subject:body`
   - Example: Email Bridge

## Supported Payload Versions

| **Version**              | **Hexadecimal Value** | **Decimal Value** | **Description**                                             |
| ------------------------ | --------------------- | ----------------- | ----------------------------------------------------------- |
| [v0](#payload-format-v0) | `None`                | `None`            | No explicit version marker, backward-compatible formats.    |
| [v1](#payload-format-v1) | `0x0A`                | `10`              | Includes a version marker as the first byte of the payload. |

## Payload Format V0

| **Payload Type**                                | **Switch** | **Description**                                       |
| ----------------------------------------------- | ---------- | ----------------------------------------------------- |
| [Auth Request Payload](#auth-request-payload)   | `0`        | Contains a client public key                          |
| [Auth Code Payload](#auth-code-payload)         | `1`        | Contains an authentication code                       |
| [Auth Code and Payload](#auth-code-and-payload) | `2`        | Contains an authentication code and encrypted content |
| [Payload Only](#payload-only)                   | `3`        | Contains encrypted content only                       |

### Auth Request Payload

- **Switch**: `0`
- **Format**:
  - 1 byte: Content Switch
  - 4 bytes: Public Key Length (integer)
  - Variable: Client Public Key

#### Visual Representation:

```
+------------------+----------------------------+-------------------+
| Content Switch   | Length of Client Public Key| Client Public Key |
| (1 byte)         | (4 bytes, integer)         | (variable size)   |
+------------------+----------------------------+-------------------+
```

```python
content_switch = bytes([0])  # b'\x00'
client_public_key = b"client_pub_key"

payload = (
    content_switch +
    struct.pack("<i", len(client_public_key)) +
    client_public_key
)
encoded = base64.b64encode(payload).decode("utf-8")
print(encoded)
```

### Auth Code Payload

- **Switch**: `1`
- **Format**:
  - 1 byte: Content Switch
  - 1 byte: Auth Code Length (integer)
  - Variable: Auth Code

#### Visual Representation:

```
+------------------+---------------------------+-----------------+
| Content Switch   | Length of Auth Code       | Auth Code       |
| (1 byte)         | (1 byte, integer)         | (variable size) |
+------------------+---------------------------+-----------------+
```

```python
content_switch = bytes([1])  # b'\x01'
auth_code = b"123456"

payload = (
    content_switch +
    bytes([len(auth_code)]) +
    auth_code
)
encoded = base64.b64encode(payload).decode("utf-8")
print(encoded)
```

### Auth Code and Payload

- **Switch**: `2`
- **Format**:
  - 1 byte: Content Switch
  - 1 byte: Auth Code Length (integer)
  - 4 bytes: Ciphertext Length (integer)
  - 1 byte: Bridge Letter
  - Variable: Auth Code
  - Variable: Ciphertext

> [!NOTE]
>
> For detailed instructions on using the Double Ratchet algorithm to create ciphertext, refer to the [smswithoutborders_lib_sig documentation](https://github.com/smswithoutborders/lib_signal_double_ratchet_python?tab=readme-ov-file#double-ratchet-implementations).

#### Visual Representation:

```
+------------------+---------------------------+----------------------------+-------------------+------------------+----------------------------+
| Content Switch   | Length of Auth Code       | Length of Ciphertext       | Bridge Letter     | Auth Code        | Ciphertext                 |
| (1 byte)         | (1 byte, integer)         | (4 bytes, integer)         | (1 byte)          | (variable size)  | (variable size)            |
+------------------+---------------------------+----------------------------+-------------------+------------------+----------------------------+
```

```python
content_switch = bytes([2])  # b'\x02'
auth_code = b"123456"
bridge_letter = b"e"
ciphertext = b"Hello world!"

payload = (
    content_switch +
    bytes([len(auth_code)]) +
    struct.pack("<i", len(ciphertext)) +
    bridge_letter +
    auth_code +
    ciphertext
)
encoded = base64.b64encode(payload).decode("utf-8")
print(encoded)
```

### Payload Only

- **Switch**: `3`
- **Format**:
  - 1 byte: Content Switch
  - 4 bytes: Ciphertext Length (integer)
  - 1 byte: Bridge Letter
  - Variable: Ciphertext

> [!NOTE]
>
> For detailed instructions on using the Double Ratchet algorithm to create ciphertext, refer to the [smswithoutborders_lib_sig documentation](https://github.com/smswithoutborders/lib_signal_double_ratchet_python?tab=readme-ov-file#double-ratchet-implementations).

#### Visual Representation:

```
+------------------+-----------------------------+------------------+----------------------------+
| Content Switch   | Length of Ciphertext        | Bridge Letter    | Ciphertext                 |
| (1 byte)         | (4 bytes, integer)          | (1 byte)         | (variable size)            |
+------------------+-----------------------------+------------------+----------------------------+
```

```python
content_switch = bytes([3])  # b'\x03'
bridge_letter = b"e"
ciphertext = b"Hello world!"

payload = (
    content_switch +
    struct.pack("<i", len(ciphertext)) +
    bridge_letter +
    ciphertext
)
encoded = base64.b64encode(payload).decode("utf-8")
print(encoded)
```

## Payload Format V1

> [!NOTE]
>
> ### Versioning Scheme
>
> - **Version Marker**: The first byte of the payload now indicates the version format. If the first byte is `0x0A` (decimal `10`), the payload follows the **Version 1 (V1)** format, which includes a version marker. [See available versions](#supported-payload-versions).
> - **Old Formats**: If the first byte is between `0x00` and `0x03` (decimal `0` to `3`), the payload is considered to be from **Version 0 (V0)**, and no versioning is present.

| **Payload Type**                                      | **Switch** | **Description**                 |
| ----------------------------------------------------- | ---------- | ------------------------------- |
| [Auth Request and Payload](#auth-request-and-payload) | `0`        | Contains a client public key    |
| [Payload Only](#payload-only-1)                       | `1`        | Contains encrypted content only |

### Auth Request and Payload

- **Switch**: `0`
- **Format**:
  - 1 byte: Version Marker (e.g., `0x0A`)
  - 1 byte: Switch Value
  - 1 byte: Client Public Key Length (integer)
  - 2 bytes: Ciphertext Length (integer)
  - 1 byte: Bridge Letter
  - 1 byte: Server Key Identifier (integer)
  - Variable: Client Public Key
  - Variable: Ciphertext

> [!NOTE]
>
> For detailed instructions on using the Double Ratchet algorithm to create ciphertext, refer to the [smswithoutborders_lib_sig documentation](https://github.com/smswithoutborders/lib_signal_double_ratchet_python?tab=readme-ov-file#double-ratchet-implementations).

#### Visual Representation:

```
+----------------+--------------+-----------------------------+----------------------+---------------+-----------------------+-------------------+-----------------+
| Version Marker | Switch Value | Length of Client Public Key | Length of Ciphertext | Bridge Letter | Server Key Identifier | Client Public Key | Ciphertext      |
| (1 byte)       | (1 byte)     | (1 byte)                    | (2 bytes)            | (1 byte)      | (1 byte)              | (variable size)   | (variable size) |
+----------------+--------------+-----------------------------+----------------------+---------------+-----------------------+-------------------+-----------------+
```

```python
version = bytes([10])  # b'\x0A'
switch_value = bytes([0])  # b'\x00'
server_key_id = bytes([0])  # b'\x00'
bridge_letter = b"e"
client_public_key = b"client_pub_key"
ciphertext = b"Hello world!"

payload = (
    version +
    switch_value +
    bytes([len(client_public_key)]) +
    struct.pack("<H", len(ciphertext)) +
    bridge_letter +
    server_key_id +
    client_public_key +
    ciphertext
)
encoded = base64.b64encode(payload).decode("utf-8")
print(encoded)
```

### Payload Only

- **Switch**: `1`
- **Format**:
  - 1 byte: Version Marker (e.g., `0x0A`)
  - 1 byte: Switch Value
  - 2 bytes: Ciphertext Length (integer)
  - 1 byte: Bridge Letter
  - Variable: Ciphertext

> [!NOTE]
>
> For detailed instructions on using the Double Ratchet algorithm to create ciphertext, refer to the [smswithoutborders_lib_sig documentation](https://github.com/smswithoutborders/lib_signal_double_ratchet_python?tab=readme-ov-file#double-ratchet-implementations).

#### Visual Representation:

```
+----------------+--------------+--------------------- +---------------+---------------- +
| Version Marker | Switch Value | Length of Ciphertext | Bridge Letter | Ciphertext      |
| (1 byte)       | (1 byte)     | (2 bytes)            | (1 byte)      | (variable size) |
+----------------+--------------+--------------------- +---------------+---------------- +
```

```python
version = bytes([10])  # b'\x0A'
switch_value = bytes([1])  # b'\x01'
bridge_letter = b"e"
ciphertext = b"Hello world!"

payload = (
    version +
    switch_value +
    struct.pack("<H", len(ciphertext)) +
    bridge_letter +
    ciphertext
)
encoded = base64.b64encode(payload).decode("utf-8")
print(encoded)
```

## Reply Data Format

### Content Format

The Bridge supports the following reply content formats:

1. **Email**: `sender:cc:bcc:subject:body`
   - Example: Email Bridge

- **sender**: The email address of the sender, formatted as `Name <email>` if the sender's name is available.
- **cc**: A comma-separated list of CC recipients, formatted as `Name <email>` if available.
- **bcc**: A comma-separated list of BCC recipients, formatted as `Name <email>` if available.
- **subject**: The subject line of the email.
- **body**: The reply message body (parsed to exclude quoted text).

#### Example:

```
John Doe <john.doe@example.com>:jane.doe@example.com:michael.smith@example.com:Meeting Update:Thank you for the update.
```

### Payload Format

- **Format**:
  - 4 bytes: Ciphertext Length (integer)
  - 1 byte: Bridge Letter
  - Variable: Ciphertext

> [!NOTE]
>
> For detailed instructions on using the Double Ratchet algorithm to create ciphertext, refer to the [smswithoutborders_lib_sig documentation](https://github.com/smswithoutborders/lib_signal_double_ratchet_python?tab=readme-ov-file#double-ratchet-implementations).

#### Visual Representation:

```
+-----------------------------+------------------+----------------------------+
| Length of Ciphertext        | Bridge Letter    | Ciphertext                 |
| (4 bytes, integer)          | (1 byte)         | (variable size)            |
+-----------------------------+------------------+----------------------------+
```

```python
bridge_letter = b"e"
ciphertext = b"John Doe <john.doe@example.com>:jane.doe@example.com::Meeting Update:Thank you for the update."

payload = (
    struct.pack("<i", len(ciphertext)) +
    bridge_letter +
    ciphertext
)
encoded = base64.b64encode(payload).decode("utf-8")
print(encoded)
```

## SMS Payload Format

The SMS payload is used for transmitting the encrypted reply message to the RelaySMS app.

### Payload Format

```
RelaySMS Reply Please paste this entire message in your RelaySMS app \n
<base64_encoded_payload>
```

Refer to [Reply Payload Format](#payload-format) for how to generate the `<base64_encoded_payload>`
