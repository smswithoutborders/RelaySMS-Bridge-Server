# Bridge Specification

## Table of Contents

- [Content Format](#content-format)
  - [Content Format V0](#content-format-v0)
  - [Content Format V1](#content-format-v1)
  - [Content Format V2](#content-format-v2)
- [Payload Format](#supported-payload-versions)
  - [Payload Format V0](#payload-format-v0)
  - [Payload Format V1](#payload-format-v1)
  - [Payload Format V2](#payload-format-v2)
- [Reply Data Format](#reply-data-format)
- [SMS Payload Format](#sms-payload-format)

## Content Format

### Content Format V0

> [!NOTE]
>
> For detailed instructions on encrypting the content format using the Double Ratchet algorithm, refer to the [smswithoutborders_lib_sig documentation](https://github.com/smswithoutborders/lib_signal_double_ratchet_python?tab=readme-ov-file#double-ratchet-implementations).

1. **Email**: `to:cc:bcc:subject:body`
   - Example: Email Bridge

### Content Format V1

> [!NOTE]
>
> For detailed instructions on encrypting the content format using the Double Ratchet algorithm, refer to the [smswithoutborders_lib_sig documentation](https://github.com/smswithoutborders/lib_signal_double_ratchet_python?tab=readme-ov-file#double-ratchet-implementations).

> [!NOTE]
>
> **All 2-byte length fields are encoded as unsigned little-endian.**

#### Field Bitmap Definition

The bitmap is a single byte where each bit represents the presence of a specific field:

- **Bit 0 (0x01)**: `from` field
- **Bit 1 (0x02)**: `to` field
- **Bit 2 (0x04)**: `cc` field
- **Bit 3 (0x08)**: `bcc` field
- **Bit 4 (0x10)**: `subject` field
- **Bit 5 (0x20)**: `body` field
- **Bit 6 (0x40)**: Text content present
- **Bit 7 (0x80)**: Image content present

1. **Email format**: Binary-encoded fields with the following structure:

   - **1 byte**: Field presence bitmap
   - **1 byte**: Length of `from` field (if bit 0 is set and bit 6 is set)
   - **2 bytes**: Length of `to` field (if bit 1 is set and bit 6 is set)
   - **2 bytes**: Length of `cc` field (if bit 2 is set and bit 6 is set)
   - **2 bytes**: Length of `bcc` field (if bit 3 is set and bit 6 is set)
   - **1 byte**: Length of `subject` field (if bit 4 is set and bit 6 is set)
   - **2 bytes**: Length of `body` field (if bit 5 is set and bit 6 is set)
   - **2 bytes**: `Image Session ID` (if bit 7 is set)
   - **1 byte**: `Image Segment info` (if bit 7 is set)
   - **2 bytes**: Length of `Image` (if bit 7 is set)
   - **Variable**: Value of `from` field (if present)
   - **Variable**: Value of `to` field (if present)
   - **Variable**: Value of `cc` field (if present)
   - **Variable**: Value of `bcc` field (if present)
   - **Variable**: Value of `subject` field (if present)
   - **Variable**: Value of `body` field (if present)
   - **Variable**: Value of `Image` (if present)

## Supported Payload Versions

| **Version**              | **Hexadecimal Value** | **Decimal Value** | **Description**                                             |
| ------------------------ | --------------------- | ----------------- | ----------------------------------------------------------- |
| [v0](#payload-format-v0) | `None`                | `None`            | No explicit version marker, backward-compatible formats.    |
| [v1](#payload-format-v1) | `0x0A`                | `10`              | Includes a version marker as the first byte of the payload. |
| [v2](#payload-format-v2) | `0x02`                | `2`               | Uses bitmap field mapping for efficient field indication.   |

## Payload Format V0

> [!WARN]
>
> This payload format is deprecated.

> [!NOTE]
>
> ### Versioning Scheme
>
> - **Old Formats**: If the first byte is between `0x00` and `0x03` (decimal `0` to `3`), the payload is considered to be from **Version 0 (V0)**, and no versioning is present.

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
content_switch = b'\x00'
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
content_switch = b'\x01'
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
  - Variable: Ciphertext (encrypted [Content Format V0](#content-format-v0)).

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
content_switch = b'\x02'
auth_code = b"123456"
bridge_letter = b"e"
ciphertext = b"..."

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
  - Variable: Ciphertext (encrypted [Content Format V0](#content-format-v0)).

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
content_switch = b'\x03'
bridge_letter = b"e"
ciphertext = b"..."

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
> - **Version Marker**: The first byte of the payload is `0x0A` (decimal `10`) to indicate **Version 1 (V1)** format, which includes a version marker.

| **Payload Type**                                      | **Switch** | **Description**                 |
| ----------------------------------------------------- | ---------- | ------------------------------- |
| [Auth Request and Payload](#auth-request-and-payload) | `0`        | Contains a client public key    |
| [Payload Only](#payload-only-1)                       | `1`        | Contains encrypted content only |

### Auth Request and Payload

- **Switch**: `0`
- **Format**:
  - 1 byte: Version Marker (`0x0A`)
  - 1 byte: Switch Value
  - 1 byte: Client Public Key Length (integer)
  - 2 bytes: Ciphertext Length (integer)
  - 1 byte: Bridge Letter
  - 1 byte: Server Key Identifier (integer)
  - Variable: Client Public Key
  - Variable: Ciphertext (encrypted [Content Format V0](#content-format-v0)).
  - 2 byte: Language Code (ISO 639-1 format)

> [!NOTE]
>
> For detailed instructions on using the Double Ratchet algorithm to create ciphertext, refer to the [smswithoutborders_lib_sig documentation](https://github.com/smswithoutborders/lib_signal_double_ratchet_python?tab=readme-ov-file#double-ratchet-implementations).

#### Visual Representation:

```
+----------------+--------------+-----------------------------+----------------------+---------------+-----------------------+-------------------+-----------------+---------------+
| Version Marker | Switch Value | Length of Client Public Key | Length of Ciphertext | Bridge Letter | Server Key Identifier | Client Public Key | Ciphertext      | Language Code |
| (1 byte)       | (1 byte)     | (1 byte)                    | (2 bytes)            | (1 byte)      | (1 byte)              | (variable size)   | (variable size) | (2 bytes)     |
+----------------+--------------+-----------------------------+----------------------+---------------+-----------------------+-------------------+-----------------+---------------+
```

```python
version = b'\x0A'
switch_value = b'\x00'
server_key_id = b'\x00'
bridge_letter = b"e"
client_public_key = b"client_pub_key"
ciphertext = b"Hello world!"
language = b"en"

payload = (
    version +
    switch_value +
    bytes([len(client_public_key)]) +
    struct.pack("<H", len(ciphertext)) +
    bridge_letter +
    server_key_id +
    client_public_key +
    ciphertext +
    language
)
encoded = base64.b64encode(payload).decode("utf-8")
print(encoded)
```

### Payload Only

- **Switch**: `1`
- **Format**:
  - 1 byte: Version Marker (`0x0A`)
  - 1 byte: Switch Value
  - 2 bytes: Ciphertext Length (integer)
  - 1 byte: Bridge Letter
  - Variable: Ciphertext (encrypted [Content Format V0](#content-format-v0)).
  - 2 byte: Language Code (ISO 639-1 format)

> [!NOTE]
>
> For detailed instructions on using the Double Ratchet algorithm to create ciphertext, refer to the [smswithoutborders_lib_sig documentation](https://github.com/smswithoutborders/lib_signal_double_ratchet_python?tab=readme-ov-file#double-ratchet-implementations).

#### Visual Representation:

```
+----------------+--------------+--------------------- +---------------+---------------- +---------------+
| Version Marker | Switch Value | Length of Ciphertext | Bridge Letter | Ciphertext      | Language Code |
| (1 byte)       | (1 byte)     | (2 bytes)            | (1 byte)      | (variable size) | (2 bytes)     |
+----------------+--------------+--------------------- +---------------+---------------- +---------------+
```

```python
version = b'\x0A'
switch_value = b'\x01'
bridge_letter = b"e"
ciphertext = b"..."
language = b"en"

payload = (
    version +
    switch_value +
    struct.pack("<H", len(ciphertext)) +
    bridge_letter +
    ciphertext +
    language
)
encoded = base64.b64encode(payload).decode("utf-8")
print(encoded)
```

## Payload Format V2

> [!NOTE]
>
> ### Versioning Scheme
>
> - **Version Marker**: The first byte of the payload is `0x02` (decimal `2`) to indicate **Version 2 (V2)** format.
> - **Content Format**: Uses [Content Format V2](#content-format-v2).

| **Payload Type**                                        | **Switch** | **Description**                 |
| ------------------------------------------------------- | ---------- | ------------------------------- |
| [Auth Request and Payload](#auth-request-and-payload-1) | `0`        | Contains a client public key    |
| [Payload Only](#payload-only-2)                         | `1`        | Contains encrypted content only |

### Auth Request and Payload

- **Switch**: `0`
- **Format**:
  - 1 byte: Version Marker (`0x02`)
  - 1 byte: Switch Value
  - 1 byte: Client Public Key Length (integer)
  - 2 bytes: Ciphertext Length (integer)
  - 1 byte: Bridge Letter
  - 1 byte: Server Key Identifier (integer)
  - Variable: Client Public Key
  - Variable: Ciphertext (encrypted [Content Format V1](#content-format-v1)).
  - 2 byte: Language Code (ISO 639-1 format)

> [!NOTE]
>
> For detailed instructions on using the Double Ratchet algorithm to create ciphertext, refer to the [smswithoutborders_lib_sig documentation](https://github.com/smswithoutborders/lib_signal_double_ratchet_python?tab=readme-ov-file#double-ratchet-implementations).

#### Visual Representation:

```
+----------------+--------------+-----------------------------+----------------------+---------------+-----------------------+-------------------+-----------------+---------------+
| Version Marker | Switch Value | Length of Client Public Key | Length of Ciphertext | Bridge Letter | Server Key Identifier | Client Public Key | Ciphertext      | Language Code |
| (1 byte)       | (1 byte)     | (1 byte)                    | (2 bytes)            | (1 byte)      | (1 byte)              | (variable size)   | (variable size) | (2 bytes)     |
+----------------+--------------+-----------------------------+----------------------+---------------+-----------------------+-------------------+-----------------+---------------+
```

```python
version = b'\x02'
switch_value = b'\x00'
server_key_id = b'\x00'
bridge_letter = b"e"
client_public_key = b"client_pub_key"
ciphertext = b"..."
language = b"en"

payload = (
    version +
    switch_value +
    bytes([len(client_public_key)]) +
    struct.pack("<H", len(ciphertext)) +
    bridge_letter +
    server_key_id +
    client_public_key +
    ciphertext +
    language
)
encoded = base64.b64encode(payload).decode("utf-8")
print(encoded)
```

### Payload Only

- **Switch**: `1`
- **Format**:
  - 1 byte: Version Marker (`0x02`)
  - 1 byte: Switch Value
  - 2 bytes: Ciphertext Length (integer)
  - 1 byte: Bridge Letter
  - Variable: Ciphertext (encrypted [Content Format V1](#content-format-v1)).
  - 2 byte: Language Code (ISO 639-1 format)

> [!NOTE]
>
> For detailed instructions on using the Double Ratchet algorithm to create ciphertext, refer to the [smswithoutborders_lib_sig documentation](https://github.com/smswithoutborders/lib_signal_double_ratchet_python?tab=readme-ov-file#double-ratchet-implementations).

#### Visual Representation:

```
+----------------+--------------+----------------------+---------------+-----------------+---------------+
| Version Marker | Switch Value | Length of Ciphertext | Bridge Letter | Ciphertext      | Language Code |
| (1 byte)       | (1 byte)     | (2 bytes)            | (1 byte)      | (variable size) | (2 bytes)     |
+----------------+--------------+----------------------+---------------+-----------------+---------------+
```

```python
version = b'\x02'
switch_value = b'\x01'
bridge_letter = b"e"
ciphertext = b"..."
language = b"en"

payload = (
    version +
    switch_value +
    struct.pack("<H", len(ciphertext)) +
    bridge_letter +
    ciphertext +
    language
)
encoded = base64.b64encode(payload).decode("utf-8")
print(encoded)
```

## Reply Data Format

### Content Format

The Bridge supports the following reply content formats:

1. **Email**: `alias_address | sender | cc | bcc | subject | body`
   - Example: Email Bridge

- **alias_address**: The unique email alias that maps to the recipient's phone number.
- **sender**: The email address of the sender, formatted as `Name <email>` if the sender's name is available.
- **cc**: A comma-separated list of CC recipients, formatted as `Name <email>` if available.
- **bcc**: A comma-separated list of BCC recipients, formatted as `Name <email>` if available.
- **subject**: The subject line of the email.
- **body**: The reply message body.

> [!NOTE]
>
> The `|` separators are only used in this documentation for readability. In actual content, the fields are concatenated **without any delimiters**.

#### Example:

```
123456789_bridge@relaysms.me | John Doe <john.doe@example.com> | jane.doe@example.com | michael.smith@example.com | Hello World | It works!.
```

### Payload Format

- **Format**:
  - 1 byte: Length of `alias_address`
  - 1 byte: Length of `sender`
  - 1 byte: Length of `cc`
  - 1 byte: Length of `bcc`
  - 1 byte: Length of `subject`
  - 2 bytes: Length of `body`
  - 2 bytes: Length of `ciphertext`
  - 1 byte: Bridge Letter
  - Variable: Ciphertext

> [!NOTE]
>
> For detailed instructions on using the Double Ratchet algorithm to create ciphertext, refer to the [smswithoutborders_lib_sig documentation](https://github.com/smswithoutborders/lib_signal_double_ratchet_python?tab=readme-ov-file#double-ratchet-implementations).

#### Visual Representation:

```
+-------------------------+--------------------------+----------------------+-----------------------+-------------------+--------------------+----------------------+---------------+-----------------+
| Length of Alias Address | Length of Sender Address | Length of CC Address | Length of BCC Address | Length of Subject | Length of Body     | Length of Ciphertext | Bridge Letter | Ciphertext      |
| (1 byte, integer)       | (1 byte, integer)        | (1 byte, integer)    | (1 byte, integer)     | (1 byte, integer) | (2 bytes, integer) | (2 bytes, integer)   | (1 byte)      | (variable size) |
+-------------------------+--------------------------+----------------------+-----------------------+-------------------+--------------------+----------------------+---------------+-----------------+
```

```python
bridge_letter = b"e"
ciphertext = (
    alias_address + sender + cc_recipients + bcc_recipients + subject + message_body
).encode()

payload = (
    bytes([len(alias_address)])
    + bytes([len(sender)])
    + bytes([len(cc_recipients)])
    + bytes([len(bcc_recipients)])
    + bytes([len(subject)])
    + struct.pack("<H", len(message_body))
    + struct.pack("<H", len(ciphertext))
    + bridge_letter
    + ciphertext
)
encoded = base64.b64encode(payload).decode("utf-8")
print(encoded)
```

## SMS Payload Format

The SMS payload is used for transmitting the encrypted reply message to the RelaySMS app.

### Payload Format

```
RelaySMS Reply Please paste this entire message in your RelaySMS app\n
<base64_encoded_payload>\n
<email_timestamp>
```

Refer to [Reply Payload Format](#payload-format) for how to generate the `<base64_encoded_payload>`.
