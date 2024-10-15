# Bridge Specification Documentation

## Table of Contents

- [Content Format](#content-format)
- [Payload Format](#payload-format)

## Content Format

The Bridge supports the following content formats:

1. **Email format**: `to:cc:bcc:subject:body`

   - Example: Email Bridge

## Payload Format

### 1.1 Public Key Payload

The public key payload is structured as follows:

- **Content Switch**: A single byte indicating the type of payload.
  - Value: `0` (indicates that the payload contains a public key)
- **Length of Public Key**: A 4-byte integer representing the length of the public key.
- **Public Key**: The public key data (variable length based on the length specified).

### Example Layout

```
+------------------+------------------------+------------------+
| Content Switch   | Length of Public Key    | Public Key      |
| (1 byte)         | (4 bytes, integer)      | (variable size) |
+------------------+------------------------+------------------+
```

#### Example Encoding

```python
content_switch = b"0"
public_key = b"pub_key"  # Example public key
public_key_data = content_switch + struct.pack("<i", len(public_key)) + public_key
public_key_payload = base64.b64encode(public_key_data).decode("utf-8")
```

### 1.2 Authentication Code Payload

The authentication code payload is structured as follows:

- **Content Switch**: A single byte indicating the type of payload.
  - Value: `1` (indicates that the payload contains an authentication code and ciphertext)
- **Length of Authentication Code**: A 4-byte integer representing the length of the authentication code.
- **Authentication Code**: The authentication code data.
- **Bridge Letter**: A single byte representing the bridge letter.
- **Ciphertext**: The encrypted content (variable length).

### Example Layout

```
+----------------+-------------------------------+---------------------+-----------------+-----------------+
| Content Switch | Length of Authentication Code | Authentication Code | Bridge Letter   | Ciphertext      |
| (1 byte)       | (4 bytes, integer)            | (variable size)     | (1 byte)        | (variable size) |
+----------------+-------------------------------+---------------------+-----------------+-----------------+
```

#### Example Encoding

```python
content_switch = b"1"
auth_code = b"123456"  # Example authentication code
bl = b"e"               # Example bridge letter
enc_content = b"Hello world!"  # Example content to encrypt

auth_code_data = content_switch + struct.pack("<i", len(auth_code)) + auth_code + bl + enc_content
auth_code_payload = base64.b64encode(auth_code_data).decode("utf-8")
```

### 1.3 Encrypted Content Only Payload (No Auth Code)

The encrypted content only payload is structured as follows:

- **Content Switch**: A single byte indicating the type of payload.
  - Value: `2` (indicates that the payload contains only ciphertext)
- **Bridge Letter**: A single byte representing the bridge letter.
- **Ciphertext**: The encrypted content (variable length).

### Example Layout

```
+------------------+-----------------+-----------------------------------+
| Content Switch   | Bridge Letter   | Ciphertext (variable size)        |
| (1 byte)         | (1 byte)        |                                   |
+------------------+-----------------+-----------------------------------+
```

#### Example Encoding

```python
content_switch = b"2"
bl = b"e"               # Example bridge letter
enc_content = b"Hello world!"  # Example encrypted content
content_data = content_switch + bl + enc_content
enc_content_only_payload = base64.b64encode(content_data).decode("utf-8")
```
