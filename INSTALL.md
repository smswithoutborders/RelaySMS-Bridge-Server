# Installation Guide

## Automated Installation

```bash
sudo ./install.sh
```

This will:

- Install system dependencies
- Clone repository to `/opt/relaysms/relaysms-bridge-server`
- Setup Python virtualenv
- Compile gRPC protos
- Install bridge packages
- Install and enable systemd services

## Manual Installation

### Install Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    libmariadb-dev git curl make
```

### Clone Repository

```bash
sudo git clone https://github.com/smswithoutborders/RelaySMS-Bridge-Server.git \
    /opt/relaysms/relaysms-bridge-server
cd /opt/relaysms/relaysms-bridge-server
```

### Setup Python Environment

```bash
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
```

### Build Application

```bash
source venv/bin/activate
make setup
```

This will:

- Download vault proto files
- Download bridge implementations
- Compile gRPC protos

### Install Bridge Packages

After downloading bridges, install their dependencies:

```bash
find bridges/ -type f -name "requirements.txt" -exec \
  pip install --disable-pip-version-check -r {} \;
```

### Configure Environment

```bash
cp template.env .env
vim .env
```

Edit the `.env` file to configure:

- Database settings (MySQL or SQLite)
- Vault gRPC connection settings
- Bridge email settings (SMTP/IMAP)
- SMS provider settings (Twilio)
- SimpleLogin API settings (optional)

### Initialize Runtime

```bash
mkdir -p data
set -a && source .env && set +a
# Database will be created automatically on first run
```

### Install Services

```bash
sudo cp relaysms-bridge-server.target relaysms-bridge-server-*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable relaysms-bridge-server.target
sudo systemctl start relaysms-bridge-server.target
```

## Service Management

```bash
./manage.sh start       # Start all services
./manage.sh stop        # Stop all services
./manage.sh restart     # Restart all services
./manage.sh status      # Check status
./manage.sh logs        # View logs
./manage.sh enable      # Enable on boot
./manage.sh disable     # Disable on boot
./manage.sh update      # Update installation
./manage.sh uninstall   # Remove installation
```

## Configuration

Edit `/opt/relaysms/relaysms-bridge-server/.env`:

### Server

Configure gRPC server settings:

```bash
# Mode
MODE=production         # development or production

# gRPC Server
GRPC_HOST=127.0.0.1
GRPC_PORT=10000
GRPC_SSL_PORT=10001

# SSL (Optional)
SSL_CERTIFICATE_FILE=
SSL_CERTIFICATE_KEY_FILE=
```

### Vault Connection

Configure connection to RelaySMS Vault:

```bash
VAULT_GRPC_HOST=localhost
VAULT_GRPC_PORT=8000
VAULT_GRPC_SSL_PORT=8001
VAULT_GRPC_INTERNAL_PORT=8443
VAULT_GRPC_INTERNAL_SSL_PORT=8444
```

### Database

Choose between MySQL and SQLite:

**SQLite (Default):**

```bash
SQLITE_DATABASE_PATH=data/bridges.sqlite
# Leave MySQL settings empty
MODE=development
```

**MySQL:**

```bash
MYSQL_HOST=127.0.0.1
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=relaysms_bridge_server
MODE=production
# Leave SQLITE_DATABASE_PATH empty
```

### Bridge Email Settings

Configure SMTP and IMAP for email bridge functionality:

```bash
# SMTP (Outgoing mail)
BRIDGE_SMTP_SERVER=smtp.example.com
BRIDGE_SMTP_PORT=587
BRIDGE_SMTP_USERNAME=your_email@example.com
BRIDGE_SMTP_PASSWORD=your_password

# IMAP (Incoming mail)
BRIDGE_IMAP_SERVER=imap.example.com
BRIDGE_IMAP_PORT=993
BRIDGE_IMAP_USERNAME=your_email@example.com
BRIDGE_IMAP_PASSWORD=your_password
BRIDGE_IMAP_MAIL_FOLDER=INBOX
```

### SimpleLogin Integration (Optional)

For email aliasing and privacy:

```bash
SL_API_KEY=your_simplelogin_api_key
SL_PRIMARY_EMAIL=your_email@example.com
SL_PRIMARY_DOMAIN=your_domain.com
```

See [SimpleLogin API Documentation](https://github.com/simple-login/app/blob/master/docs/api.md) for obtaining an API key.

### SMS Provider (Twilio)

Configure Twilio for SMS functionality:

```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_SERVICE_SID=your_service_sid
TWILIO_PHONE_NUMBER=+1234567890
```

See [Twilio Setup](#twilio-sms-provider) section below for detailed configuration.

### Logging & Monitoring

```bash
LOG_LEVEL=info          # debug, info, warning, error
MOCK_REPLY_SMS=false    # Set to true for development/testing
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

## Services

- `relaysms-bridge-server-grpc.service` - gRPC server (default port 10000)
- `relaysms-bridge-server-mail.service` - Mail inbound service (monitors IMAP)
- `relaysms-bridge-server.target` - Service group

## File Locations

- Installation: `/opt/relaysms/relaysms-bridge-server/`
- Configuration: `/opt/relaysms/relaysms-bridge-server/.env`
- Database: `/opt/relaysms/relaysms-bridge-server/data/bridges.sqlite`
- Service files: `/etc/systemd/system/relaysms-bridge-server*`

## External Dependencies

### RelaySMS Vault (Required)

The Bridge Server requires a running instance of RelaySMS Vault for authentication and token management.

**Installation:**

See [RelaySMS Vault Installation Guide](https://github.com/smswithoutborders/RelaySMS-Vault/blob/main/INSTALL.md)

Quick install:

```bash
curl -fsSL https://raw.githubusercontent.com/smswithoutborders/RelaySMS-Vault/main/install.sh | sudo bash
```

**Configuration:**

Ensure the Vault gRPC server is accessible and update the `VAULT_GRPC_*` variables in the Bridge Server's `.env` file accordingly.

### Twilio SMS Provider

Twilio is used for sending SMS messages.

**Setup:**

1. **Create a Twilio Account:**
   - Sign up at [https://www.twilio.com](https://www.twilio.com)
   - Navigate to the [Twilio Console](https://console.twilio.com/)

2. **Get Account Credentials:**
   - Find your `Account SID` and `Auth Token` on the console dashboard
   - Update `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` in `.env`

3. **Create a Messaging Service:**
   - Go to [Messaging Services](https://console.twilio.com/us1/develop/sms/services)
   - Create a new Messaging Service
   - Copy the `Service SID` and update `TWILIO_SERVICE_SID` in `.env`

4. **Get a Phone Number:**
   - Purchase a phone number from [Phone Numbers](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming)
   - Add the phone number to your Messaging Service
   - Update `TWILIO_PHONE_NUMBER` in `.env`

### SimpleLogin (Optional)

SimpleLogin provides email aliasing.

**Setup:**

1. **Create a SimpleLogin Account:**
   - Sign up at [https://simplelogin.io](https://simplelogin.io)
   - Or self-host: [SimpleLogin Self-Hosting Guide](https://github.com/simple-login/app/blob/master/docs/install.md)

2. **Get API Key:**
   - Go to [API Keys](https://app.simplelogin.io/dashboard/api_key)
   - Generate a new API key
   - Update `SL_API_KEY` in `.env`

3. **Configure Domain:**
   - Update `SL_PRIMARY_EMAIL` and `SL_PRIMARY_DOMAIN` in `.env`
   - Ensure your domain is verified in SimpleLogin

### Email Service Provider

For SMTP and IMAP, you can use:

**Configuration:**

- Update `BRIDGE_SMTP_*` and `BRIDGE_IMAP_*` variables in `.env`

## Bridges

The Bridge Server supports various bridge implementations. Available bridges are listed in [bridges.json](resources/bridges.json).

Bridge implementations are automatically downloaded during setup via `make setup`. See individual bridge documentation in the `bridges/` directory after installation.
