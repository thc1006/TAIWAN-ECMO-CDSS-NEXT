# TAIWAN ECMO CDSS - Deployment Guide

**Production deployment guide for Taiwan medical centers**

Version: 1.0.0
Last Updated: 2025-10-05

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Start](#quick-start)
3. [Database Setup](#database-setup)
4. [Application Installation](#application-installation)
5. [Model Training](#model-training)
6. [Production Deployment](#production-deployment)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Security Considerations](#security-considerations)
9. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
10. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware Requirements

**Minimum (Development)**
- CPU: 4 cores (x86_64)
- RAM: 8 GB
- Storage: 50 GB SSD
- Network: 100 Mbps

**Recommended (Production)**
- CPU: 8+ cores (x86_64)
- RAM: 32 GB
- Storage: 500 GB SSD (NVMe preferred)
- Network: 1 Gbps
- GPU: Optional (for accelerated training)

### Software Requirements

**Operating System**
- Ubuntu 20.04 LTS or 22.04 LTS (recommended)
- CentOS 8+
- Windows Server 2019+ (limited support)

**Database**
- PostgreSQL 13+ (required for MIMIC-IV)
- Minimum 100 GB storage for MIMIC-IV 3.1

**Runtime**
- Python 3.11 or 3.12
- pip 23+
- virtualenv or conda

**Optional**
- Docker 24+
- Docker Compose 2.20+
- Nginx 1.18+
- Supervisor 4.2+

---

## Quick Start

### Option 1: Docker Deployment (Recommended)

```bash
# Clone repository
git clone https://github.com/your-org/TAIWAN-ECMO-CDSS-NEXT.git
cd TAIWAN-ECMO-CDSS-NEXT

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

Access services:
- Dashboard: http://localhost:8501
- SMART App: http://localhost:5000
- PostgreSQL: localhost:5432

### Option 2: Manual Installation

```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run basic tests
python -m pytest tests/ -v

# Start dashboard
streamlit run econ/dashboard.py
```

---

## Database Setup

### PostgreSQL Installation

**Ubuntu/Debian**
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql-13 postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database user
sudo -u postgres createuser --interactive --pwprompt ecmo_admin

# Create database
sudo -u postgres createdb -O ecmo_admin mimic4
```

**Docker**
```bash
docker run -d \
  --name postgres-mimic \
  -e POSTGRES_PASSWORD=your_secure_password \
  -e POSTGRES_DB=mimic4 \
  -v pgdata:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:13
```

### MIMIC-IV 3.1 Installation

**Prerequisites**
1. Obtain access to MIMIC-IV from PhysioNet: https://physionet.org/content/mimiciv/3.1/
2. Complete CITI Data or Specimens Only Research training
3. Sign data use agreement

**Load MIMIC-IV Data**

```bash
# Download MIMIC-IV 3.1
cd /data/mimic4
wget -r -N -c -np --user YOUR_USERNAME --ask-password \
  https://physionet.org/files/mimiciv/3.1/

# Install MIMIC-Code repository
git clone https://github.com/MIT-LCP/mimic-code.git
cd mimic-code/mimic-iv/buildmimic/postgres

# Configure database connection
export DBHOST=localhost
export DBPORT=5432
export DBNAME=mimic4
export DBUSER=ecmo_admin
export DBPASS=your_password
export DATADIR=/data/mimic4/physionet.org/files/mimiciv/3.1

# Run loader script
make mimic-gz datadir=${DATADIR}

# Verify installation
psql -h localhost -U ecmo_admin -d mimic4 -c "\dt mimiciv_hosp.*"
psql -h localhost -U ecmo_admin -d mimic4 -c "\dt mimiciv_icu.*"
```

**Expected Schema**
```
mimiciv_hosp.patients
mimiciv_hosp.admissions
mimiciv_hosp.diagnoses_icd
mimiciv_hosp.procedures_icd
mimiciv_hosp.labevents
mimiciv_icu.icustays
mimiciv_icu.chartevents
mimiciv_icu.procedureevents
mimiciv_icu.inputevents
mimiciv_icu.outputevents
```

### Initialize ECMO-Specific Schema

```bash
# Run ECMO identification query
psql -h localhost -U ecmo_admin -d mimic4 -f sql/identify_ecmo.sql

# Extract ECMO features
psql -h localhost -U ecmo_admin -d mimic4 -f sql/extract_ecmo_features.sql

# Verify ECMO cohort
psql -h localhost -U ecmo_admin -d mimic4 -c \
  "SELECT COUNT(*) FROM ecmo_episodes;"
```

Expected output: ~300-500 ECMO episodes in MIMIC-IV 3.1

---

## Application Installation

### Python Environment Setup

```bash
# Create isolated environment
python3.11 -m venv /opt/ecmo-cdss/.venv
source /opt/ecmo-cdss/.venv/bin/activate

# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import pandas, numpy, sklearn, streamlit; print('OK')"
```

### Configuration

Create `.env` file in project root:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mimic4
DB_USER=ecmo_admin
DB_PASSWORD=your_secure_password
DB_SCHEMA=mimiciv_icu,mimiciv_hosp

# Application Settings
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your_random_secret_key_change_this

# SMART on FHIR Configuration
FHIR_BASE_URL=https://your-fhir-server.hospital.org/fhir
SMART_CLIENT_ID=your_client_id
SMART_CLIENT_SECRET=your_client_secret
SMART_REDIRECT_URI=https://ecmo-cdss.hospital.org/callback

# Taiwan NHI Settings
NHI_CURRENCY=TWD
NHI_ICU_COST_PER_DAY=30000
NHI_WARD_COST_PER_DAY=8000
NHI_ECMO_DAILY_CONSUMABLE=15000
NHI_ECMO_SETUP_COST=100000

# Model Settings
MODEL_DIR=/opt/ecmo-cdss/models
MODEL_VERSION=1.0.0
RISK_THRESHOLD=0.5

# Feature Flags
ENABLE_NIRS_INTEGRATION=true
ENABLE_COST_ANALYSIS=true
ENABLE_VR_TRAINING=false
ENABLE_SMART_FHIR=true

# Logging
LOG_DIR=/var/log/ecmo-cdss
LOG_RETENTION_DAYS=90
```

### Directory Structure

```bash
# Create required directories
sudo mkdir -p /opt/ecmo-cdss/{models,logs,data,exports}
sudo mkdir -p /var/log/ecmo-cdss

# Set permissions
sudo chown -R ecmo-app:ecmo-app /opt/ecmo-cdss
sudo chown -R ecmo-app:ecmo-app /var/log/ecmo-cdss

# Link application
sudo ln -s /path/to/TAIWAN-ECMO-CDSS-NEXT /opt/ecmo-cdss/app
```

---

## Model Training

### Prepare Training Data

```bash
cd /opt/ecmo-cdss/app

# Extract ECMO features from MIMIC-IV
python nirs/data_loader.py \
  --db-host localhost \
  --db-name mimic4 \
  --output data/ecmo_features.csv

# Verify data extraction
head -n 5 data/ecmo_features.csv
wc -l data/ecmo_features.csv
```

### Train Risk Models

```bash
# Train VA and VV ECMO risk models
python nirs/train_models.py \
  --features-csv data/ecmo_features.csv \
  --output-dir models/ecmo_risk \
  --model-type gradient_boosting \
  --tune-hyperparameters \
  --use-smote \
  --use-feature-selection \
  --cv-folds 5

# Expected output:
# - models/ecmo_risk/va_risk_model.pkl
# - models/ecmo_risk/vv_risk_model.pkl
# - models/ecmo_risk/va_feature_names.json
# - models/ecmo_risk/vv_feature_names.json
# - models/ecmo_risk/va_training_report.txt
# - models/ecmo_risk/vv_training_report.txt
```

### Validate Models

```bash
# Run validation suite
python nirs/model_validation.py \
  --model-dir models/ecmo_risk \
  --test-data data/ecmo_features.csv

# Check calibration curves
python -c "
from nirs.risk_models import load_model
from nirs.model_validation import plot_calibration_curve

model = load_model('models/ecmo_risk/va_risk_model.pkl')
plot_calibration_curve(model, 'models/ecmo_risk/va_calibration.png')
"
```

**Acceptance Criteria**
- AUROC ≥ 0.75
- Calibration slope: 0.8-1.2
- Brier score ≤ 0.25
- No severe overfitting (train/val gap < 0.05)

### Demo Inference

```bash
# Run demo prediction
python nirs/demo.py \
  --model models/ecmo_risk/va_risk_model.pkl \
  --patient-data data/sample_patient.json

# Expected output:
# {
#   "survival_probability": 0.67,
#   "risk_score": 0.33,
#   "risk_quintile": 2,
#   "shap_values": {...},
#   "recommendations": [...]
# }
```

---

## Production Deployment

### Option 1: Docker Compose (Recommended)

**Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                         Nginx Proxy                         │
│                    (SSL Termination)                        │
└──────────────┬──────────────────────┬───────────────────────┘
               │                      │
    ┌──────────▼──────────┐  ┌───────▼──────────────┐
    │ Streamlit Dashboard │  │ SMART on FHIR App    │
    │    (Port 8501)      │  │    (Port 5000)       │
    └──────────┬──────────┘  └───────┬──────────────┘
               │                      │
               └──────────┬───────────┘
                          │
                ┌─────────▼──────────┐
                │   PostgreSQL DB    │
                │   (Port 5432)      │
                └────────────────────┘
```

**Start Services**
```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale dashboard replicas for high availability
docker-compose up -d --scale dashboard=3

# Monitor health
docker-compose ps
curl http://localhost/health
```

### Option 2: Systemd Services

**Dashboard Service**

Create `/etc/systemd/system/ecmo-dashboard.service`:

```ini
[Unit]
Description=ECMO CDSS Dashboard (Streamlit)
After=network.target postgresql.service

[Service]
Type=simple
User=ecmo-app
Group=ecmo-app
WorkingDirectory=/opt/ecmo-cdss/app
Environment="PATH=/opt/ecmo-cdss/.venv/bin"
ExecStart=/opt/ecmo-cdss/.venv/bin/streamlit run econ/dashboard.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true
Restart=always
RestartSec=10
StandardOutput=append:/var/log/ecmo-cdss/dashboard.log
StandardError=append:/var/log/ecmo-cdss/dashboard.error.log

[Install]
WantedBy=multi-user.target
```

**SMART App Service**

Create `/etc/systemd/system/ecmo-smart-app.service`:

```ini
[Unit]
Description=ECMO CDSS SMART on FHIR App
After=network.target postgresql.service

[Service]
Type=simple
User=ecmo-app
Group=ecmo-app
WorkingDirectory=/opt/ecmo-cdss/app/smart-on-fhir
Environment="PATH=/opt/ecmo-cdss/.venv/bin"
Environment="FLASK_ENV=production"
ExecStart=/opt/ecmo-cdss/.venv/bin/gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 4 \
  --timeout 120 \
  --access-logfile /var/log/ecmo-cdss/smart-access.log \
  --error-logfile /var/log/ecmo-cdss/smart-error.log \
  app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and Start**
```bash
sudo systemctl daemon-reload
sudo systemctl enable ecmo-dashboard ecmo-smart-app
sudo systemctl start ecmo-dashboard ecmo-smart-app

# Check status
sudo systemctl status ecmo-dashboard
sudo systemctl status ecmo-smart-app

# View logs
sudo journalctl -u ecmo-dashboard -f
sudo journalctl -u ecmo-smart-app -f
```

### Nginx Reverse Proxy

**Install Nginx**
```bash
sudo apt install nginx
```

**Configure** `/etc/nginx/sites-available/ecmo-cdss`:

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=dashboard_limit:10m rate=30r/s;

upstream dashboard {
    least_conn;
    server localhost:8501 max_fails=3 fail_timeout=30s;
}

upstream smart_app {
    least_conn;
    server localhost:5000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name ecmo-cdss.hospital.org;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ecmo-cdss.hospital.org;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/ecmo-cdss.crt;
    ssl_certificate_key /etc/ssl/private/ecmo-cdss.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/ecmo-cdss-access.log;
    error_log /var/log/nginx/ecmo-cdss-error.log;

    # Dashboard
    location / {
        limit_req zone=dashboard_limit burst=20 nodelay;

        proxy_pass http://dashboard;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_buffering off;
        proxy_read_timeout 86400;
    }

    # SMART on FHIR App
    location /smart {
        limit_req zone=api_limit burst=10 nodelay;

        rewrite ^/smart(/.*)$ $1 break;
        proxy_pass http://smart_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Static files
    location /static {
        alias /opt/ecmo-cdss/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Enable Site**
```bash
sudo ln -s /etc/nginx/sites-available/ecmo-cdss /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate Setup

**Option 1: Let's Encrypt (Free)**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d ecmo-cdss.hospital.org
```

**Option 2: Hospital CA**
```bash
# Copy certificates to server
sudo cp ecmo-cdss.crt /etc/ssl/certs/
sudo cp ecmo-cdss.key /etc/ssl/private/
sudo chmod 600 /etc/ssl/private/ecmo-cdss.key
```

---

## Monitoring and Logging

### Application Logging

**Configure Logging** (`logging_config.yaml`):

```yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  json:
    (): pythonjsonlogger.jsonlogger.JsonFormatter
    format: '%(asctime)s %(name)s %(levelname)s %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    formatter: standard
    level: INFO

  file:
    class: logging.handlers.RotatingFileHandler
    filename: /var/log/ecmo-cdss/app.log
    maxBytes: 104857600  # 100MB
    backupCount: 10
    formatter: json
    level: INFO

  error_file:
    class: logging.handlers.RotatingFileHandler
    filename: /var/log/ecmo-cdss/error.log
    maxBytes: 104857600
    backupCount: 10
    formatter: json
    level: ERROR

loggers:
  ecmo_cdss:
    level: INFO
    handlers: [console, file, error_file]
    propagate: false

root:
  level: WARNING
  handlers: [console, file]
```

### Health Monitoring

**Create Health Check Script** (`scripts/health_check.sh`):

```bash
#!/bin/bash

# Health check script for ECMO CDSS

DASHBOARD_URL="http://localhost:8501"
SMART_APP_URL="http://localhost:5000/health"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="mimic4"

# Check dashboard
if ! curl -sf "$DASHBOARD_URL" > /dev/null; then
    echo "ERROR: Dashboard not responding"
    exit 1
fi

# Check SMART app
if ! curl -sf "$SMART_APP_URL" > /dev/null; then
    echo "ERROR: SMART app not responding"
    exit 1
fi

# Check database
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" > /dev/null; then
    echo "ERROR: Database not accessible"
    exit 1
fi

echo "OK: All services healthy"
exit 0
```

**Setup Cron Job**:
```bash
# Check every 5 minutes
*/5 * * * * /opt/ecmo-cdss/scripts/health_check.sh >> /var/log/ecmo-cdss/health.log 2>&1
```

### Performance Monitoring

**Install Prometheus Node Exporter**:
```bash
sudo apt install prometheus-node-exporter
sudo systemctl enable prometheus-node-exporter
sudo systemctl start prometheus-node-exporter
```

**PostgreSQL Monitoring**:
```bash
# Install pg_stat_statements extension
psql -U ecmo_admin -d mimic4 -c "CREATE EXTENSION pg_stat_statements;"

# Monitor slow queries
psql -U ecmo_admin -d mimic4 -c "
SELECT query, calls, total_exec_time, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"
```

---

## Security Considerations

### Taiwan Medical Data Privacy Laws

**Personal Information Protection Act (PIPA)**
- Encrypt all PHI at rest and in transit
- Implement access controls based on role
- Log all data access for audit trail
- Obtain patient consent for data use

**Electronic Signatures Act**
- Use digital certificates for authentication
- Maintain non-repudiation for clinical decisions
- Archive signed reports for 7 years minimum

### HIPAA Compliance (International Standards)

**Administrative Safeguards**
```bash
# Create admin user with limited privileges
sudo adduser ecmo-admin
sudo usermod -aG ecmo-app ecmo-admin

# Enforce password policy
sudo chage -M 90 ecmo-admin  # 90-day password expiration
sudo passwd -l root          # Disable root login
```

**Technical Safeguards**
```bash
# Enable firewall
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw deny 5432/tcp  # Block external DB access

# Configure fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

**Audit Logging**
```python
# Add to application code
import logging
from datetime import datetime

audit_logger = logging.getLogger('audit')

def log_access(user_id, patient_id, action):
    audit_logger.info({
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': user_id,
        'patient_id': patient_id,
        'action': action,
        'ip_address': request.remote_addr
    })
```

### Database Security

**Encryption at Rest**:
```bash
# Enable PostgreSQL encryption
sudo vim /etc/postgresql/13/main/postgresql.conf

# Add:
ssl = on
ssl_cert_file = '/etc/ssl/certs/postgres.crt'
ssl_key_file = '/etc/ssl/private/postgres.key'
```

**Row-Level Security**:
```sql
-- Enable RLS for patient data
ALTER TABLE ecmo_episodes ENABLE ROW LEVEL SECURITY;

-- Create policy: users can only see their hospital's patients
CREATE POLICY hospital_isolation ON ecmo_episodes
  USING (hospital_id = current_setting('app.current_hospital_id')::integer);
```

### Secret Management

**Use Environment Variables (Development)**:
```bash
export DB_PASSWORD=$(cat /run/secrets/db_password)
export SMART_CLIENT_SECRET=$(cat /run/secrets/smart_secret)
```

**Use HashiCorp Vault (Production)**:
```bash
# Install Vault
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt install vault

# Store secrets
vault kv put secret/ecmo-cdss db_password="..."
vault kv put secret/ecmo-cdss smart_secret="..."

# Retrieve in application
vault kv get -field=db_password secret/ecmo-cdss
```

---

## Backup and Disaster Recovery

### Database Backup

**Automated Daily Backups**:
```bash
#!/bin/bash
# /opt/ecmo-cdss/scripts/backup_db.sh

BACKUP_DIR="/backup/ecmo-cdss"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="mimic4"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Perform backup
pg_dump -h localhost -U ecmo_admin -d "$DB_NAME" \
  | gzip > "$BACKUP_DIR/mimic4_$TIMESTAMP.sql.gz"

# Remove backups older than 30 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/mimic4_$TIMESTAMP.sql.gz"
```

**Schedule with Cron**:
```bash
# Daily at 2 AM
0 2 * * * /opt/ecmo-cdss/scripts/backup_db.sh >> /var/log/ecmo-cdss/backup.log 2>&1
```

### Model Backup

```bash
# Backup trained models
tar -czf models_$(date +%Y%m%d).tar.gz models/
aws s3 cp models_*.tar.gz s3://ecmo-cdss-backups/models/
```

### Disaster Recovery Plan

**RTO (Recovery Time Objective)**: 4 hours
**RPO (Recovery Point Objective)**: 24 hours

**Recovery Steps**:

1. **Database Recovery**:
```bash
# Restore from latest backup
gunzip -c /backup/ecmo-cdss/mimic4_20251005.sql.gz | \
  psql -h localhost -U ecmo_admin -d mimic4_restored
```

2. **Application Recovery**:
```bash
# Pull latest code
git clone https://github.com/your-org/TAIWAN-ECMO-CDSS-NEXT.git
cd TAIWAN-ECMO-CDSS-NEXT

# Restore configuration
cp /backup/ecmo-cdss/.env .

# Restore models
tar -xzf /backup/ecmo-cdss/models_20251005.tar.gz

# Start services
docker-compose up -d
```

3. **Verify Recovery**:
```bash
# Run health checks
./scripts/health_check.sh

# Test prediction
curl -X POST http://localhost:5000/api/ecmo-risk \
  -H "Content-Type: application/json" \
  -d @test_patient.json
```

---

## Troubleshooting

### Common Issues

**Issue 1: Dashboard won't start**

```bash
# Check logs
sudo journalctl -u ecmo-dashboard -n 50

# Common causes:
# - Port 8501 already in use
sudo lsof -i :8501
sudo kill -9 <PID>

# - Missing dependencies
source /opt/ecmo-cdss/.venv/bin/activate
pip install -r requirements.txt

# - Database connection failed
psql -h localhost -U ecmo_admin -d mimic4 -c "\conninfo"
```

**Issue 2: Model loading errors**

```bash
# Verify model files exist
ls -lh models/ecmo_risk/

# Check Python version compatibility
python --version  # Should be 3.11 or 3.12

# Retrain models if incompatible
python nirs/train_models.py --features-csv data/ecmo_features.csv
```

**Issue 3: SMART app authentication fails**

```bash
# Verify FHIR server connectivity
curl https://your-fhir-server.hospital.org/fhir/metadata

# Check client credentials
echo $SMART_CLIENT_ID
echo $SMART_CLIENT_SECRET

# Enable debug logging
export FLASK_DEBUG=1
python smart-on-fhir/app.py
```

**Issue 4: Slow query performance**

```sql
-- Analyze query plan
EXPLAIN ANALYZE SELECT * FROM ecmo_episodes WHERE ...;

-- Create indexes
CREATE INDEX idx_ecmo_patient ON ecmo_episodes(subject_id);
CREATE INDEX idx_ecmo_time ON ecmo_episodes(start_time);

-- Update statistics
ANALYZE ecmo_episodes;
```

### Performance Optimization

**Database Tuning**:
```bash
# Edit postgresql.conf
sudo vim /etc/postgresql/13/main/postgresql.conf

# Increase resources
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
work_mem = 256MB
max_connections = 100
```

**Application Caching**:
```python
# Add Redis caching
from redis import Redis
from functools import lru_cache

redis = Redis(host='localhost', port=6379)

@lru_cache(maxsize=1000)
def get_patient_risk(patient_id):
    # Cache expensive computations
    ...
```

### Support Contacts

**Development Team**:
- Email: ecmo-cdss-support@hospital.org
- GitHub Issues: https://github.com/your-org/TAIWAN-ECMO-CDSS-NEXT/issues

**Emergency Contacts** (24/7):
- On-call Engineer: +886-XXX-XXX-XXX
- Database Admin: +886-XXX-XXX-XXX
- Clinical Lead: +886-XXX-XXX-XXX

---

## Appendix

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_HOST` | Yes | localhost | PostgreSQL host |
| `DB_PORT` | Yes | 5432 | PostgreSQL port |
| `DB_NAME` | Yes | mimic4 | Database name |
| `DB_USER` | Yes | - | Database user |
| `DB_PASSWORD` | Yes | - | Database password |
| `FHIR_BASE_URL` | No | - | FHIR server URL |
| `SMART_CLIENT_ID` | No | - | SMART app client ID |
| `MODEL_DIR` | No | ./models | Model directory |
| `LOG_LEVEL` | No | INFO | Logging level |

### Port Reference

| Service | Port | Protocol | Access |
|---------|------|----------|--------|
| PostgreSQL | 5432 | TCP | Internal only |
| Streamlit Dashboard | 8501 | HTTP | Internal only |
| SMART App | 5000 | HTTP | Internal only |
| Nginx | 80, 443 | HTTP/HTTPS | Public |
| Prometheus | 9090 | HTTP | Internal only |

### Useful Commands

```bash
# Check disk space
df -h /opt/ecmo-cdss

# Monitor resource usage
htop

# View database size
psql -U ecmo_admin -d mimic4 -c "
SELECT pg_size_pretty(pg_database_size('mimic4'));
"

# Check Docker logs
docker-compose logs -f --tail=100

# Restart all services
sudo systemctl restart ecmo-dashboard ecmo-smart-app nginx
```

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-05
**Next Review**: 2025-11-05
