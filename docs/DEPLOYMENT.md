# Deployment Guide for SEU GOSI Certificate Parser API

This guide provides detailed instructions for deploying the SEU GOSI Certificate Parser API on both Windows and Linux servers.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Windows Deployment](#windows-deployment)
- [Linux Deployment](#linux-deployment)
- [Environment Configuration](#environment-configuration)
- [Production Best Practices](#production-best-practices)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- Python 3.12 or higher
- Git
- pip (Python package manager)
- A production-grade WSGI server (e.g., Gunicorn for Linux or Waitress for Windows)
- A reverse proxy (e.g., Nginx or Apache)

### System Requirements
- Minimum 2GB RAM
- 2 CPU cores
- 10GB available disk space
- Internet connectivity for package installation

### Dependencies Overview
```plaintext
# FastAPI and dependencies
fastapi==0.109.2        # Main web framework
uvicorn==0.27.1         # ASGI server
python-multipart==0.0.9 # File upload handling

# PDF Processing
pdfplumber==0.11.7      # PDF text extraction

# Authentication and Security
python-jose[cryptography]==3.5.0  # JWT tokens
passlib[bcrypt]==1.7.4           # Password hashing
bcrypt==4.3.0                    # Password hashing algorithm

# Environment and Configuration
python-dotenv==1.0.1    # Environment variables management
```

## Windows Deployment

### 1. Install Required Software

1. **Install Python 3.12**:
   ```powershell
   # Download Python 3.12 from official website
   # https://www.python.org/downloads/
   # During installation, check "Add Python to PATH"
   ```

2. **Install Git**:
   ```powershell
   # Download from https://git-scm.com/download/win
   # Use default installation options
   ```

### 2. Setup Application

1. **Clone Repository**:
   ```powershell
   # Create application directory
   mkdir C:\apps
   cd C:\apps
   git clone <repository-url> seu-gosi
   cd seu-gosi
   ```

2. **Create Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   pip install waitress  # Windows production server
   ```

### 3. Configure Environment

1. **Create `.env` File**:
   ```powershell
   copy .env.example .env
   # Edit .env with appropriate values
   ```

2. **Generate Secret Key**:
   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   # Copy output to SECRET_KEY in .env
   ```

### 4. Setup Windows Service

1. **Create Service Script** (`run_app.ps1`):
   ```powershell
   # Create file: C:\apps\seu-gosi\run_app.ps1
   Set-Location C:\apps\seu-gosi
   .\venv\Scripts\activate
   $env:PYTHONPATH = "C:\apps\seu-gosi"
   waitress-serve --host=127.0.0.1 --port=8000 --call app.main:app
   ```

2. **Create Windows Service**:
   ```powershell
   # Using NSSM (Non-Sucking Service Manager)
   # Download NSSM from https://nssm.cc/
   nssm install SEUGOSIService "powershell" "C:\apps\seu-gosi\run_app.ps1"
   nssm set SEUGOSIService AppDirectory "C:\apps\seu-gosi"
   nssm set SEUGOSIService Description "SEU GOSI Certificate Parser API Service"
   nssm start SEUGOSIService
   ```

## Linux Deployment

### 1. Install Required Software

1. **Update System**:
   ```bash
   sudo apt update && sudo apt upgrade -y  # For Ubuntu/Debian
   # OR
   sudo yum update -y  # For CentOS/RHEL
   ```

2. **Install Python and Dependencies**:
   ```bash
   # Ubuntu/Debian
   sudo apt install -y python3.12 python3.12-venv python3-pip git nginx tesseract-ocr

   # CentOS/RHEL
   sudo yum install -y python3.12 python3-pip git nginx tesseract
   ```

### 2. Setup Application

1. **Create Service User**:
   ```bash
   sudo useradd -r -s /bin/false seu-gosi
   sudo mkdir /opt/seu-gosi
   sudo chown seu-gosi:seu-gosi /opt/seu-gosi
   ```

2. **Clone Repository**:
   ```bash
   sudo -u seu-gosi git clone <repository-url> /opt/seu-gosi
   cd /opt/seu-gosi
   ```

3. **Create Virtual Environment**:
   ```bash
   sudo -u seu-gosi python3.12 -m venv venv
   source venv/bin/activate
   ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install gunicorn
   ```

### 3. Configure Environment

1. **Create `.env` File**:
   ```bash
   sudo -u seu-gosi cp .env.example .env
   sudo -u seu-gosi nano .env
   ```

2. **Generate Secret Key**:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   # Copy output to SECRET_KEY in .env
   ```

### 4. Setup Systemd Service

1. **Create Service File**:
   ```bash
   sudo nano /etc/systemd/system/seu-gosi.service
   ```

   Content:
   ```ini
   [Unit]
   Description=SEU GOSI API Service
   After=network.target

   [Service]
   User=seu-gosi
   Group=seu-gosi
   WorkingDirectory=/opt/seu-gosi
   Environment="PATH=/opt/seu-gosi/venv/bin"
   EnvironmentFile=/opt/seu-gosi/.env
   ExecStart=/opt/seu-gosi/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app -b 127.0.0.1:8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. **Start Service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start seu-gosi
   sudo systemctl enable seu-gosi
   ```

### 5. Configure Nginx Reverse Proxy

1. **Create Nginx Configuration**:
   ```bash
   sudo nano /etc/nginx/sites-available/seu-gosi
   ```

   Content:
   ```nginx
   server {
       listen 80;
       server_name your_domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

2. **Enable Site**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/seu-gosi /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## Environment Configuration

### Required Environment Variables

Update your `.env` file with production values:

```env
# Security Settings
SECRET_KEY=<your-generated-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Authentication
ADMIN_USERNAME=<production-admin-username>
ADMIN_PASSWORD=<strong-production-password>

# Server Settings
HOST=127.0.0.1
PORT=8000
WORKERS=4

# CORS Settings
ALLOWED_ORIGINS=https://your-domain.com

# Allowed IP Addresses
ALLOWED_IPS=<production-ip-ranges>

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# PDF Processing
MIN_SUBSCRIPTION_MONTHS=170
MAX_SUBSCRIPTION_MONTHS=180
```

## Production Best Practices

### Security

1. **SSL/TLS Configuration**:
   - Always use HTTPS in production
   - Install SSL certificate (Let's Encrypt recommended)
   - Configure SSL in Nginx

2. **Firewall Configuration**:
   ```bash
   # Ubuntu/Debian
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable

   # CentOS/RHEL
   sudo firewall-cmd --permanent --add-service=http
   sudo firewall-cmd --permanent --add-service=https
   sudo firewall-cmd --reload
   ```

3. **Regular Updates**:
   ```bash
   # Update system packages weekly
   # Update Python packages monthly
   # Rotate logs regularly
   ```

### Monitoring

1. **Setup Basic Monitoring**:
   ```bash
   # Install monitoring tools
   sudo apt install -y prometheus node-exporter
   # OR
   sudo yum install -y prometheus node-exporter
   ```

2. **Configure Log Rotation**:
   ```bash
   sudo nano /etc/logrotate.d/seu-gosi
   ```

   Content:
   ```
   /var/log/seu-gosi/*.log {
       daily
       rotate 14
       compress
       delaycompress
       notifempty
       create 0640 seu-gosi seu-gosi
       sharedscripts
       postrotate
           systemctl reload seu-gosi
       endscript
   }
   ```

### Backup

1. **Setup Daily Backups**:
   ```bash
   # Create backup script
   sudo nano /opt/seu-gosi/backup.sh
   ```

   Content:
   ```bash
   #!/bin/bash
   BACKUP_DIR="/backup/seu-gosi"
   DATE=$(date +%Y%m%d)
   mkdir -p $BACKUP_DIR
   
   # Backup application files
   tar -czf $BACKUP_DIR/seu-gosi-$DATE.tar.gz /opt/seu-gosi
   
   # Backup environment file separately
   cp /opt/seu-gosi/.env $BACKUP_DIR/env-$DATE.bak
   
   # Remove backups older than 7 days
   find $BACKUP_DIR -type f -mtime +7 -delete
   ```

2. **Schedule Backup**:
   ```bash
   sudo chmod +x /opt/seu-gosi/backup.sh
   sudo crontab -e
   # Add: 0 2 * * * /opt/seu-gosi/backup.sh
   ```

## Troubleshooting

### Common Issues

1. **Service Won't Start**:
   - Check logs: `sudo journalctl -u seu-gosi -n 100`
   - Verify permissions: `ls -la /opt/seu-gosi`
   - Check Python path: `which python3`

2. **Permission Issues**:
   ```bash
   sudo chown -R seu-gosi:seu-gosi /opt/seu-gosi
   sudo chmod -R 755 /opt/seu-gosi
   sudo chmod 600 /opt/seu-gosi/.env
   ```

3. **Nginx 502 Bad Gateway**:
   - Check if gunicorn is running: `ps aux | grep gunicorn`
   - Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
   - Verify Nginx configuration: `sudo nginx -t`

### Maintenance Commands

1. **Restart Services**:
   ```bash
   # Linux
   sudo systemctl restart seu-gosi
   sudo systemctl restart nginx

   # Windows
   nssm restart SEUGOSIService
   ```

2. **View Logs**:
   ```bash
   # Linux
   sudo journalctl -u seu-gosi -f
   sudo tail -f /var/log/nginx/access.log

   # Windows
   Get-EventLog -LogName Application -Source SEUGOSIService
   ```

3. **Update Application**:
   ```bash
   # Linux
   cd /opt/seu-gosi
   sudo -u seu-gosi git pull
   source venv/bin/activate
   pip install -r requirements.txt
   sudo systemctl restart seu-gosi

   # Windows
   cd C:\apps\seu-gosi
   git pull
   .\venv\Scripts\activate
   pip install -r requirements.txt
   nssm restart SEUGOSIService
   ```

For additional support or questions, please contact the development team or refer to the project's documentation. 