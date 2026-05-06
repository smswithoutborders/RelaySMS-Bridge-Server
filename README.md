# RelaySMS Bridge Server

The bridge is a technology designed to allow users to communicate with online platforms via SMS, even without an active internet connection. It enables a secure handshake and encrypted message exchange entirely over SMS, eliminating the need for internet access.

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Supported Bridges](#supported-bridges)
- [Documentation](#documentation)
- [Testing](#testing)
- [License](#license)

## Requirements

- **Python:** ≥ 3.8.10
- **Database:** MySQL (≥ 8.0.28), MariaDB, or SQLite
- **External Services:**
  - [RelaySMS Vault](https://github.com/smswithoutborders/RelaySMS-Vault) (required)
  - SMTP/IMAP email service (required for email bridge)
  - [Twilio](https://www.twilio.com) (required for SMS functionality)
  - [SimpleLogin](https://simplelogin.io) (optional, for email aliasing)

**Ubuntu Dependencies:**

```bash
sudo apt install python3-dev build-essential libmysqlclient-dev make
```

## Installation

### Production

Quick install:

```bash
curl -fsSL https://raw.githubusercontent.com/smswithoutborders/RelaySMS-Bridge-Server/main/install.sh | sudo bash
```

Manage services:

```bash
cd /opt/relaysms/relaysms-bridge-server
./manage.sh {start|stop|restart|status|logs|update}
```

See [INSTALL.md](INSTALL.md) for manual installation and detailed configuration.

### Development

```bash
# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp template.env .env
# Edit .env as needed

# Build
make setup

# Install bridge packages
find bridges/ -type f -name "requirements.txt" -exec \
  pip install --disable-pip-version-check -r {} \;

# Start services
python3 grpc_server.py        # Terminal 1
python3 mail_inbound.py        # Terminal 2
```

### Docker

```bash
# Build
docker build -t relaysms-bridge-server:latest .

# Configure
cp template.env .env
# Edit .env as needed

# Run
docker run -d \
  --name relaysms-bridge-server \
  --env-file .env \
  -p 10000:10000 \
  -v $(pwd)/data:/app/data \
  relaysms-bridge-server:latest
```

> [!TIP]
> Update `GRPC_HOST=0.0.0.0` in `.env` for external container access.

## Configuration

Configure via environment variables in `.env` file:

### Server

```bash
MODE=production                 # development or production
GRPC_HOST=127.0.0.1            # gRPC server host
GRPC_PORT=10000                 # gRPC server port
GRPC_SSL_PORT=10001            # gRPC SSL port
SSL_CERTIFICATE_FILE=           # SSL certificate path (optional)
SSL_CERTIFICATE_KEY_FILE=       # SSL key path (optional)
```

### Vault Connection

```bash
VAULT_GRPC_HOST=localhost
VAULT_GRPC_PORT=8000
VAULT_GRPC_SSL_PORT=8001
VAULT_GRPC_INTERNAL_PORT=8443
VAULT_GRPC_INTERNAL_SSL_PORT=8444
```

> [!IMPORTANT]
> RelaySMS Vault must be installed and running. See [RelaySMS Vault Installation](https://github.com/smswithoutborders/RelaySMS-Vault/blob/main/INSTALL.md)

### Database

**SQLite (default):**

```bash
SQLITE_DATABASE_PATH=data/bridges.sqlite
MODE=development
```

**MySQL:**

```bash
MYSQL_HOST=127.0.0.1
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=relaysms_bridge_server
MODE=production
```

### Bridge Email Settings

```bash
# SMTP (Outgoing)
BRIDGE_SMTP_SERVER=smtp.example.com
BRIDGE_SMTP_PORT=587
BRIDGE_SMTP_USERNAME=your_email@example.com
BRIDGE_SMTP_PASSWORD=your_password

# IMAP (Incoming)
BRIDGE_IMAP_SERVER=imap.example.com
BRIDGE_IMAP_PORT=993
BRIDGE_IMAP_USERNAME=your_email@example.com
BRIDGE_IMAP_PASSWORD=your_password
BRIDGE_IMAP_MAIL_FOLDER=INBOX
```

### SMS Provider (Twilio)

```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_SERVICE_SID=your_service_sid
TWILIO_PHONE_NUMBER=+1234567890
```

See [INSTALL.md](INSTALL.md#twilio-sms-provider) for Twilio setup instructions.

### SimpleLogin (Optional)

```bash
SL_API_KEY=your_simplelogin_api_key
SL_PRIMARY_EMAIL=your_email@example.com
SL_PRIMARY_DOMAIN=your_domain.com
```

See [INSTALL.md](INSTALL.md#simplelogin-optional) for SimpleLogin setup instructions.

### Logging & Monitoring

```bash
LOG_LEVEL=info                  # debug, info, warning, error
MOCK_REPLY_SMS=false           # Set to true for development/testing
```

**Error Tracking (Optional):**

Bridge Server supports Sentry-compatible error tracking:

```bash
SENTRY_DSN=https://your-dsn@sentry.io/project-id
```

> [!NOTE]
> **Using GlitchTip:** GlitchTip is a Sentry-compatible open-source error tracker. The `SENTRY_DSN` variable works with both Sentry and GlitchTip.
>
> See [GlitchTip Installation Guide](https://glitchtip.com/documentation/install) to set up your own instance.

## Supported Bridges

The list of supported bridges is available in [bridges.json](resources/bridges.json).

Bridge implementations are automatically downloaded during setup. See individual bridge documentation in the `bridges/` directory.

## Documentation

- [Installation Guide](INSTALL.md) - Detailed setup instructions
- [Specifications Documentation](docs/specifications.md) - Content and payload format specs
  - [Content Format](docs/specifications.md#content-format)
  - [Payload Format](docs/specifications.md#payload-format)
- [gRPC API](docs/grpc.md) - gRPC interface documentation (if available)

## Testing

See [Test Documentation](tests/README.md) for running tests.

## License

Licensed under the GNU General Public License (GPL) v3. See [LICENSE](LICENSE) for details.
