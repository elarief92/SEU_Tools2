# Deployment Guide for SEU Tools Django Application

This guide provides detailed instructions for deploying the SEU Tools Django web application on both Windows and Linux servers with production-ready configurations.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Linux Deployment](#linux-deployment)
- [Windows Deployment](#windows-deployment)
- [Environment Configuration](#environment-configuration)
- [Security Configuration](#security-configuration)
- [SSL/HTTPS Setup](#sslhttps-setup)
- [Monitoring and Logging](#monitoring-and-logging)
- [Backup and Recovery](#backup-and-recovery)
- [Performance Tuning](#performance-tuning)
- [Maintenance and Updates](#maintenance-and-updates)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- Python 3.8 or higher
- Git
- pip (Python package manager)
- A production-grade WSGI server (Gunicorn for Linux, Waitress for Windows)
- A reverse proxy (Nginx or Apache)
- PostgreSQL (recommended for production) or SQLite (development)
- SSL certificate (Let's Encrypt recommended)

### System Requirements
- Minimum 2GB RAM (4GB recommended for production)
- 2 CPU cores (4+ recommended for production)
- 20GB available disk space
- Internet connectivity for package installation

### Dependencies Overview
```plaintext
# Django and related packages
django==4.2.7
djangorestframework==3.14.0
python-decouple==3.8

# PDF Processing
pdfplumber==0.11.7
pdf2image==1.16.3
pypdfium2==4.18.0

# Authentication and Security
python-jose[cryptography]==3.5.0
passlib[bcrypt]==1.7.4
bcrypt==4.3.0
PyJWT==2.8.0

# Environment and Configuration
python-dotenv==1.0.1

# Azure OpenAI
openai==1.93.2

# API Documentation
drf-yasg==1.21.7

# Production Server
gunicorn==21.2.0
```

## Pre-Deployment Checklist

Before starting deployment, ensure you have:

- [ ] Domain name configured (for SSL)
- [ ] Server IP address
- [ ] Database credentials (if using PostgreSQL)
- [ ] Azure OpenAI API credentials
- [ ] SSL certificate (or plan to use Let's Encrypt)
- [ ] Backup strategy planned
- [ ] Monitoring solution planned
- [ ] Firewall rules configured
- [ ] DNS records updated

## Linux Deployment

### 1. System Preparation

1. **Update System**:
   ```bash
   sudo apt update && sudo apt upgrade -y  # For Ubuntu/Debian
   # OR
   sudo yum update -y  # For CentOS/RHEL
   ```

2. **Install Required Packages**:
   ```bash
   # Ubuntu/Debian
   sudo apt install -y python3 python3-venv python3-pip git nginx postgresql postgresql-contrib curl wget unzip

   # CentOS/RHEL
   sudo yum install -y python3.8 python3-pip git nginx postgresql postgresql-contrib curl wget unzip
   ```

3. **Configure Firewall**:
   ```bash
   # Ubuntu/Debian (UFW)
   sudo ufw allow ssh
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable

   # CentOS/RHEL (firewalld)
   sudo firewall-cmd --permanent --add-service=ssh
   sudo firewall-cmd --permanent --add-service=http
   sudo firewall-cmd --permanent --add-service=https
   sudo firewall-cmd --reload
   ```

### 2. Database Setup (PostgreSQL)

1. **Install and Configure PostgreSQL**:
   ```bash
   # Start PostgreSQL service
   sudo systemctl start postgresql
   sudo systemctl enable postgresql

   # Create database and user
   sudo -u postgres psql
   ```

   ```sql
   CREATE DATABASE seu_tools_db;
   CREATE USER seu_tools_user WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE seu_tools_db TO seu_tools_user;
   ALTER USER seu_tools_user CREATEDB;
   \q
   ```

2. **Test Database Connection**:
   ```bash
   psql -h localhost -U seu_tools_user -d seu_tools_db
   ```

### 3. Application Setup

1. **Create Service User**:
   ```bash
   sudo useradd -r -s /bin/false seu-tools
   sudo mkdir -p /opt/seu-tools
   sudo chown seu-tools:seu-tools /opt/seu-tools
   ```

2. **Clone Repository**:
   ```bash
   sudo -u seu-tools git clone <repository-url> /opt/seu-tools
   cd /opt/seu-tools
   ```

3. **Create Virtual Environment**:
   ```bash
   sudo -u seu-tools python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install gunicorn
   ```

### 4. Environment Configuration

1. **Create Environment File**:
   ```bash
   sudo -u seu-tools cp .env.example .env
   sudo -u seu-tools nano .env
   ```

2. **Configure Production Settings**:
   ```env
   # Security Settings
   SECRET_KEY=your-generated-secret-key-here
   DEBUG=False
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # Database Configuration
   DATABASE_URL=postgresql://seu_tools_user:your_secure_password@localhost/seu_tools_db

   # Server Settings
   HOST=127.0.0.1
   PORT=8000
   WORKERS=4

   # CORS Settings
   ALLOWED_ORIGINS=https://your-domain.com
   ALLOWED_HOSTS=your-domain.com,your-server-ip,localhost,127.0.0.1

   # Azure OpenAI Configuration
   AZURE_OPENAI_API_KEY=your-azure-openai-key
   AZURE_OPENAI_ENDPOINT=your-azure-openai-endpoint

   # Logging
   LOG_LEVEL=INFO
   LOG_FILE=/var/log/seu-tools/django.log

   # File Upload Settings
   MAX_FILE_SIZE=10485760  # 10MB in bytes
   UPLOAD_DIR=/opt/seu-tools/media
   ```

3. **Set Proper Permissions**:
   ```bash
   sudo chown seu-tools:seu-tools /opt/seu-tools/.env
   sudo chmod 600 /opt/seu-tools/.env
   ```

### 5. Database Migration and Setup

1. **Run Migrations**:
   ```bash
   cd /opt/seu-tools
   source venv/bin/activate
   python manage.py migrate
   ```

2. **Create Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

3. **Collect Static Files**:
   ```bash
   python manage.py collectstatic --noinput
   ```

4. **Create Media Directory**:
   ```bash
   sudo mkdir -p /opt/seu-tools/media
   sudo chown -R seu-tools:seu-tools /opt/seu-tools/media
   sudo chmod -R 755 /opt/seu-tools/media
   ```

### 6. Systemd Service Configuration

1. **Create Service File**:
   ```bash
   sudo nano /etc/systemd/system/seu-tools.service
   ```

   Content:
   ```ini
   [Unit]
   Description=SEU Tools Django Application
   After=network.target postgresql.service
   Requires=postgresql.service

   [Service]
   User=seu-tools
   Group=seu-tools
   WorkingDirectory=/opt/seu-tools
   Environment="PATH=/opt/seu-tools/venv/bin"
   Environment="DJANGO_SETTINGS_MODULE=seu_tools.settings"
   ExecStart=/opt/seu-tools/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 --timeout 120 --max-requests 1000 --max-requests-jitter 100 seu_tools.wsgi:application
   Restart=always
   RestartSec=3
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable and Start Service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable seu-tools
   sudo systemctl start seu-tools
   sudo systemctl status seu-tools
   ```

### 7. Nginx Configuration

1. **Create Nginx Site Configuration**:
   ```bash
   sudo nano /etc/nginx/sites-available/seu-tools
   ```

   Content:
   ```nginx
   # Rate limiting
   limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
   limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

   server {
       listen 80;
       server_name your-domain.com;
       
       # Security headers
       add_header X-Frame-Options "SAMEORIGIN" always;
       add_header X-XSS-Protection "1; mode=block" always;
       add_header X-Content-Type-Options "nosniff" always;
       add_header Referrer-Policy "no-referrer-when-downgrade" always;
       add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
       add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

       # File upload size limit
       client_max_body_size 50M;

       # Static files
       location /static/ {
           alias /opt/seu-tools/staticfiles/;
           expires 30d;
           add_header Cache-Control "public, immutable";
           access_log off;
       }

       # Media files
       location /media/ {
           alias /opt/seu-tools/media/;
           expires 30d;
           access_log off;
       }

       # API rate limiting
       location /api/ {
           limit_req zone=api burst=20 nodelay;
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_connect_timeout 30s;
           proxy_send_timeout 30s;
           proxy_read_timeout 30s;
       }

       # Login rate limiting
       location /login/ {
           limit_req zone=login burst=5 nodelay;
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       # Health check
       location /health/ {
           proxy_pass http://127.0.0.1:8000;
           access_log off;
       }

       # Main application
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_connect_timeout 30s;
           proxy_send_timeout 30s;
           proxy_read_timeout 30s;
       }
   }
   ```

2. **Enable Site and Test Configuration**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/seu-tools /etc/nginx/sites-enabled/
   sudo rm -f /etc/nginx/sites-enabled/default
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### 8. Logging Configuration

1. **Create Log Directory**:
   ```bash
   sudo mkdir -p /var/log/seu-tools
   sudo chown seu-tools:seu-tools /var/log/seu-tools
   sudo chmod 755 /var/log/seu-tools
   ```

2. **Configure Log Rotation**:
   ```bash
   sudo nano /etc/logrotate.d/seu-tools
   ```

   Content:
   ```
   /var/log/seu-tools/*.log {
       daily
       rotate 14
       compress
       delaycompress
       notifempty
       create 0640 seu-tools seu-tools
       sharedscripts
       postrotate
           systemctl reload seu-tools
       endscript
   }
   ```

## Windows Deployment

### 1. Install Required Software

1. **Install Python 3.8+**:
   ```powershell
   # Download Python from official website
   # https://www.python.org/downloads/
   # During installation, check "Add Python to PATH"
   ```

2. **Install Git**:
   ```powershell
   # Download from https://git-scm.com/download/win
   # Use default installation options
   ```

3. **Install PostgreSQL**:
   ```powershell
   # Download from https://www.postgresql.org/download/windows/
   # Use default installation options
   ```

### 2. Setup Application

1. **Clone Repository**:
   ```powershell
   # Create application directory
   mkdir C:\apps
   cd C:\apps
   git clone <repository-url> seu-tools
   cd seu-tools
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

2. **Database Setup**:
   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic
   ```

### 4. Setup Windows Service

1. **Create Service Script** (`run_app.ps1`):
   ```powershell
   # Create file: C:\apps\seu-tools\run_app.ps1
   Set-Location C:\apps\seu-tools
   .\venv\Scripts\activate
   $env:PYTHONPATH = "C:\apps\seu-tools"
   waitress-serve --host=127.0.0.1 --port=8000 --max-request-body-size=52428800 seu_tools.wsgi:application
   ```

2. **Create Windows Service**:
   ```powershell
   # Using NSSM (Non-Sucking Service Manager)
   # Download NSSM from https://nssm.cc/
   nssm install SEUToolsService "powershell" "C:\apps\seu-tools\run_app.ps1"
   nssm set SEUToolsService AppDirectory "C:\apps\seu-tools"
   nssm set SEUToolsService Description "SEU Tools Django Application Service"
   nssm start SEUToolsService
   ```

## SSL/HTTPS Setup

### 1. Install Certbot

```bash
# Ubuntu/Debian
sudo apt install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx
```

### 2. Obtain SSL Certificate

```bash
# Get certificate
sudo certbot --nginx -d your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### 3. Configure Auto-Renewal

```bash
# Add to crontab
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring and Logging

### 1. Setup Basic Monitoring

```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Create monitoring script
sudo nano /opt/seu-tools/monitor.sh
```

Content:
```bash
#!/bin/bash
LOG_FILE="/var/log/seu-tools/monitor.log"

# Check if gunicorn is running
if ! pgrep gunicorn > /dev/null; then
    echo "$(date): Gunicorn is not running. Restarting..." >> $LOG_FILE
    sudo systemctl restart seu-tools
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): Disk usage is ${DISK_USAGE}%" >> $LOG_FILE
fi

# Check memory usage
MEM_USAGE=$(free | awk 'NR==2{printf "%.2f", $3*100/$2}')
if (( $(echo "$MEM_USAGE > 80" | bc -l) )); then
    echo "$(date): Memory usage is ${MEM_USAGE}%" >> $LOG_FILE
fi
```

```bash
sudo chmod +x /opt/seu-tools/monitor.sh
sudo crontab -e
# Add: */5 * * * * /opt/seu-tools/monitor.sh
```

### 2. Health Check Endpoint

Add to your Django `urls.py`:

```python
from django.http import HttpResponse
from django.db import connection

def health_check(request):
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return HttpResponse("OK", status=200)
    except Exception as e:
        return HttpResponse(f"ERROR: {str(e)}", status=500)

urlpatterns = [
    path('health/', health_check, name='health_check'),
    # ... other URLs
]
```

## Backup and Recovery

### 1. Setup Automated Backups

```bash
# Create backup script
sudo nano /opt/seu-tools/backup.sh
```

Content:
```bash
#!/bin/bash
BACKUP_DIR="/backup/seu-tools"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup application files
tar -czf $BACKUP_DIR/seu-tools-$DATE.tar.gz /opt/seu-tools --exclude=/opt/seu-tools/venv --exclude=/opt/seu-tools/media

# Backup environment file
cp /opt/seu-tools/.env $BACKUP_DIR/env-$DATE.bak

# Backup PostgreSQL database
pg_dump seu_tools_db > $BACKUP_DIR/db-$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media-$DATE.tar.gz /opt/seu-tools/media

# Remove backups older than 7 days
find $BACKUP_DIR -type f -mtime +7 -delete

# Log backup completion
echo "$(date): Backup completed successfully" >> /var/log/seu-tools/backup.log
```

```bash
sudo chmod +x /opt/seu-tools/backup.sh
sudo crontab -e
# Add: 0 2 * * * /opt/seu-tools/backup.sh
```

### 2. Recovery Procedures

```bash
# Restore application files
sudo tar -xzf /backup/seu-tools/seu-tools-YYYYMMDD_HHMMSS.tar.gz -C /

# Restore database
psql seu_tools_db < /backup/seu-tools/db-YYYYMMDD_HHMMSS.sql

# Restore environment file
sudo cp /backup/seu-tools/env-YYYYMMDD_HHMMSS.bak /opt/seu-tools/.env

# Restart services
sudo systemctl restart seu-tools
sudo systemctl restart nginx
```

## Performance Tuning

### 1. Gunicorn Optimization

```bash
# Update systemd service with optimized settings
sudo nano /etc/systemd/system/seu-tools.service
```

Optimized ExecStart:
```ini
ExecStart=/opt/seu-tools/venv/bin/gunicorn --workers 4 --worker-class sync --worker-connections 1000 --max-requests 1000 --max-requests-jitter 100 --timeout 120 --keep-alive 2 --bind 127.0.0.1:8000 seu_tools.wsgi:application
```

### 2. Nginx Optimization

Add to nginx configuration:
```nginx
# Enable gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

# Cache static files
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. Database Optimization

```sql
-- PostgreSQL optimization
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
SELECT pg_reload_conf();
```

## Maintenance and Updates

### 1. Application Updates

```bash
# Create update script
sudo nano /opt/seu-tools/update.sh
```

Content:
```bash
#!/bin/bash
cd /opt/seu-tools

# Backup before update
/opt/seu-tools/backup.sh

# Pull latest changes
sudo -u seu-tools git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart seu-tools
sudo systemctl reload nginx

echo "$(date): Update completed successfully" >> /var/log/seu-tools/update.log
```

### 2. System Updates

```bash
# Create system update script
sudo nano /opt/seu-tools/system-update.sh
```

Content:
```bash
#!/bin/bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Restart services if needed
sudo systemctl restart seu-tools
sudo systemctl restart nginx
sudo systemctl restart postgresql

echo "$(date): System update completed" >> /var/log/seu-tools/system-update.log
```

## Troubleshooting

### Common Issues and Solutions

1. **Service Won't Start**:
   ```bash
   # Check logs
   sudo journalctl -u seu-tools -n 100
   
   # Check permissions
   ls -la /opt/seu-tools/
   
   # Test manually
   cd /opt/seu-tools/
   source venv/bin/activate
   gunicorn --bind 127.0.0.1:8000 seu_tools.wsgi:application
   ```

2. **Permission Issues**:
   ```bash
   sudo chown -R seu-tools:seu-tools /opt/seu-tools/
   sudo chmod -R 755 /opt/seu-tools/
   sudo chmod 600 /opt/seu-tools/.env
   ```

3. **Nginx 502 Bad Gateway**:
   ```bash
   # Check if gunicorn is running
   ps aux | grep gunicorn
   
   # Check nginx logs
   sudo tail -f /var/log/nginx/error.log
   
   # Test application directly
   curl http://127.0.0.1:8000/
   ```

4. **Database Connection Issues**:
   ```bash
   # Test database connection
   psql -h localhost -U seu_tools_user -d seu_tools_db
   
   # Check PostgreSQL status
   sudo systemctl status postgresql
   ```

5. **SSL Certificate Issues**:
   ```bash
   # Check certificate status
   sudo certbot certificates
   
   # Renew certificate manually
   sudo certbot renew
   ```

### Maintenance Commands

```bash
# Restart all services
sudo systemctl restart seu-tools
sudo systemctl restart nginx
sudo systemctl restart postgresql

# View logs
sudo journalctl -u seu-tools -f
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Check service status
sudo systemctl status seu-tools
sudo systemctl status nginx
sudo systemctl status postgresql

# Check disk usage
df -h
du -sh /opt/seu-tools/

# Check memory usage
free -h
htop
```

### Emergency Procedures

1. **Service Down**:
   ```bash
   sudo systemctl restart seu-tools
   sudo systemctl restart nginx
   ```

2. **Database Issues**:
   ```bash
   sudo systemctl restart postgresql
   sudo -u postgres pg_ctl reload
   ```

3. **Full System Recovery**:
   ```bash
   # Restore from backup
   /opt/seu-tools/backup.sh restore
   
   # Restart all services
   sudo systemctl restart seu-tools nginx postgresql
   ```

For additional support or questions, please contact the development team or refer to the project's documentation. 