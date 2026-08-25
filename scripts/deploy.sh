#!/bin/bash
# ============================================================
# Script de Deploy - Sistema de Óbito Goianira
# Servidor: Ubuntu 22.04/24.04 LTS
# IP: 192.168.0.225 | Porta: 9010
# ============================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"; }
error() { echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"; exit 1; }

APP_USER="obito"
APP_DIR="/opt/sistema-obito"
REPO_URL="https://github.com/mmcerdan/svo.git"
PYTHON_VERSION="3.11"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="sistema-obito"
NGINX_SITE="/etc/nginx/sites-available/sistema-obito"
NGINX_SITE_ENABLED="/etc/nginx/sites-enabled/sistema-obito"

log "=== Iniciando Deploy do Sistema de Óbito ==="

if [[ $EUID -ne 0 ]]; then
   error "Execute como root (sudo)"
fi

# Limpa serviços anteriores se existirem
log "Parando serviços anteriores..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true

# Atualiza sistema
log "Atualizando pacotes..."
apt-get update -qq && apt-get upgrade -y -qq

# Instala dependências
log "Instalando dependências do sistema..."
apt-get install -y -qq \
    python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev \
    nginx \
    postgresql postgresql-contrib \
    redis-server \
    git curl wget \
    ufw \
    build-essential libpq-dev openssl

# Cria usuário
log "Configurando usuário..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -m -d "$APP_DIR" -s /bin/bash "$APP_USER"
    log "Usuário $APP_USER criado"
else
    log "Usuário $APP_USER já existe"
fi

# Diretórios
log "Criando diretórios..."
mkdir -p "$APP_DIR"/{app,logs,uploads,backups}
mkdir -p /var/log/gunicorn
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chown -R "$APP_USER:$APP_USER" /var/log/gunicorn

# PostgreSQL
log "Configurando PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE obito_db;" 2>/dev/null || warn "Banco já existe"
sudo -u postgres psql -c "CREATE USER obito_user WITH PASSWORD 'obito_prod_2026';" 2>/dev/null || warn "Usuário já existe"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE obito_db TO obito_user;" 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER obito_user CREATEDB;" 2>/dev/null || true

# Git clone
log "Clonando repositório..."
cd "$APP_DIR"
if [[ -d ".git" ]]; then
    sudo -u "$APP_USER" git pull origin main 2>/dev/null || sudo -u "$APP_USER" git pull 2>/dev/null || true
else
    rm -rf "$APP_DIR/app" "$APP_DIR/scripts" "$APP_DIR/requirements.txt" 2>/dev/null || true
    sudo -u "$APP_USER" git clone "$REPO_URL" .
fi
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# Remove arquivos obsoletos do app/ antigo (não devem estar lá)
rm -f "$APP_DIR/app.py" 2>/dev/null || true
rm -f "$APP_DIR/_check_ed.py" 2>/dev/null || true
rm -f "$APP_DIR/criar_testes.py" 2>/dev/null || true

# Ambiente virtual
log "Criando ambiente virtual..."
sudo -u "$APP_USER" python${PYTHON_VERSION} -m venv "$VENV_DIR"
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel -q
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt" -q

# .env
log "Configurando .env..."
if [[ ! -f "$APP_DIR/.env" ]]; then
    SECRET_KEY=$(openssl rand -hex 32)
    ADMIN_PASS=$(openssl rand -hex 8)
    cat > "$APP_DIR/.env" <<EOF
FLASK_ENV=production
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=postgresql://obito_user:obito_prod_2026@localhost:5432/obito_db
ADMIN_PASSWORD=${ADMIN_PASS}
UPLOAD_FOLDER=$APP_DIR/uploads
MAX_CONTENT_LENGTH=16777216
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
EOF
    chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    log "Admin password: ${ADMIN_PASS}"
else
    log ".env já existe"
fi

# Migrações / cria tabelas
log "Criando tabelas..."
cd "$APP_DIR"
sudo -u "$APP_USER" FLASK_ENV=production "$VENV_DIR/bin/python" -c "
from app import create_app
from app.extensions import db
app = create_app('production')
with app.app_context():
    db.create_all()
    from app.models import Usuario
    admin = Usuario.query.filter_by(usuario='admin').first()
    if not admin:
        admin = Usuario(nome='Administrador', usuario='admin', cargo='Admin', ativo=True)
        admin.set_senha('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Admin criado com sucesso')
    else:
        print('Admin ja existe')
"

# Gunicorn logs
mkdir -p /var/log/gunicorn
chown "$APP_USER:$APP_USER" /var/log/gunicorn

# systemd service - Type=simple (gunicorn NÃO suporta Type=notify)
log "Configurando systemd..."
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=Sistema de Óbito Goianira - Gunicorn
After=network.target postgresql.service redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=FLASK_ENV=production
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn \\
    --workers 4 \\
    --worker-class gthread \\
    --threads 2 \\
    --bind 127.0.0.1:5000 \\
    --timeout 120 \\
    --keep-alive 5 \\
    --max-requests 1000 \\
    --max-requests-jitter 50 \\
    --access-logfile /var/log/gunicorn/access.log \\
    --error-logfile /var/log/gunicorn/error.log \\
    --capture-output \\
    run:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Nginx - limit_req_zone NO BLOCO http, NÃO no server
log "Configurando Nginx (porta 9010)..."

# Adiciona limit_req_zone ao nginx.conf (http block) se não existir
if ! grep -q 'limit_req_zone.*zone=api' /etc/nginx/nginx.conf; then
    sed -i '/http {/a \    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;\n    limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;' /etc/nginx/nginx.conf
    log "limit_req_zone adicionado ao nginx.conf"
fi

# Configura o site (SEM limit_req_zone dentro do server)
cat > "$NGINX_SITE" <<EOF
server {
    listen 9010;
    server_name svo.goianira.go.gov.br 192.168.0.225 _;

    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    client_max_body_size 16M;

    location / {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_http_version 1.1;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    location /auth/login {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias $APP_DIR/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /uploads/ {
        alias $APP_DIR/uploads/;
        expires 1h;
        add_header Cache-Control "public";
    }

    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:5000/health;
    }
}
EOF

ln -sf "$NGINX_SITE" "$NGINX_SITE_ENABLED"
rm -f /etc/nginx/sites-enabled/default

# Testa nginx
nginx -t || error "Configuração do Nginx inválida"

# Firewall
log "Configurando firewall..."
ufw --force enable
ufw allow ssh
ufw allow 9010/tcp

# Backup cron
log "Configurando cron de backup..."
cat > /etc/cron.d/sistema-obito-backup <<EOF
0 2 * * * $APP_USER $VENV_DIR/bin/python $APP_DIR/scripts/backup.py >> $APP_DIR/logs/backup.log 2>&1
0 3 * * * root find $APP_DIR/logs -name "*.log" -mtime +30 -delete
EOF

# SSL renewal cron (self-signed, so just verify nginx is up)
cat > /etc/cron.d/sistema-obito-ssl-renew <<EOF
0 4 * * * root systemctl is-active --quiet nginx && echo "Nginx OK" >> /var/log/svo-health.log 2>&1
EOF

# Inicia serviços
log "Iniciando serviços..."
systemctl daemon-reload
systemctl enable postgresql redis-server nginx "$SERVICE_NAME"
systemctl restart postgresql redis-server

sleep 2

# Nginx
systemctl restart nginx
sleep 1

# Gunicorn
systemctl restart "$SERVICE_NAME"
sleep 3

# Verificações
log "=== Verificando serviços ==="
systemctl is-active --quiet postgresql && log "PostgreSQL: OK" || error "PostgreSQL falhou"
systemctl is-active --quiet redis-server && log "Redis: OK" || error "Redis falhou"
systemctl is-active --quiet nginx && log "Nginx: OK" || error "Nginx falhou"

if systemctl is-active --quiet "$SERVICE_NAME"; then
    log "Gunicorn: OK"
else
    warn "Gunicorn falhou - tentando corrigir..."
    journalctl -u "$SERVICE_NAME" -n 20 --no-pager
    error "Gunicorn não subiu. Verifique os logs acima."
fi

# Testa health check
log "Testando health check..."
sleep 2
if curl -sf http://127.0.0.1:5000/health > /dev/null 2>&1; then
    log "Health check Gunicorn (5000): OK"
else
    warn "Health check Gunicorn falhou"
fi

if curl -sf http://127.0.0.1:9010/health > /dev/null 2>&1; then
    log "Health check Nginx (9010): OK"
else
    warn "Health check Nginx falhou"
fi

if curl -sf http://192.168.0.225:9010/health > /dev/null 2>&1; then
    log "Health check Externo: OK"
else
    warn "Health check externo falhou (pode ser firewall/DNS)"
fi

# Tenta SSL com Let's Encrypt (opcional - só se DNS público)
log "Tentando SSL com Let's Encrypt..."
if certbot --nginx -d svo.goianira.go.gov.br --non-interactive --agree-tos --email admin@goianira.go.gov.br --redirect 2>/dev/null; then
    log "SSL Let's Encrypt configurado!"
else
    warn "SSL Let's Encrypt falhou (DNS pode não estar apontando)."
    warn "Sistema funciona sem SSL na porta 9010."
    warn "Para SSL futuro: certbot --nginx -d svo.goianira.go.gov.br"
fi

log "=== Deploy Concluído ==="
log ""
log "Acesso:"
log "  HTTP:  http://192.168.0.225:9010"
log "  Login: admin / admin123 (Altere após primeiro acesso!)"
log ""
log "Comandos úteis:"
log "  systemctl status $SERVICE_NAME"
log "  journalctl -u $SERVICE_NAME -f"
log "  systemctl restart $SERVICE_NAME"
log "  curl http://127.0.0.1:9010/health"
