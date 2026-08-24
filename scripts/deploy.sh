#!/bin/bash
# ============================================================
# Script de Deploy Automatizado - Sistema de Óbito Goianira
# Servidor: Ubuntu 22.04/24.04 LTS
# IP: 192.168.0.225
# ============================================================

set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() { echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"; }
error() { echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"; exit 1; }

# Configurações
APP_USER="obito"
APP_DIR="/opt/sistema-obito"
REPO_URL=""  # Preencher se usar git
PYTHON_VERSION="3.11"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="sistema-obito"
NGINX_CONF="/etc/nginx/sites-available/sistema-obito"

log "=== Iniciando Deploy do Sistema de Óbito ==="

# Verifica se é root
if [[ $EUID -ne 0 ]]; then
   error "Este script deve ser executado como root (sudo)"
fi

# Atualiza sistema
log "Atualizando pacotes do sistema..."
apt-get update && apt-get upgrade -y

# Instala dependências do sistema
log "Instalando dependências do sistema..."
apt-get install -y \
    python3.11 python3.11-venv python3.11-dev \
    nginx \
    postgresql postgresql-contrib \
    redis-server \
    git \
    curl \
    ufw \
    certbot python3-certbot-nginx \
    supervisor \
    build-essential libpq-dev

# Cria usuário da aplicação
log "Configurando usuário da aplicação..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -m -d "$APP_DIR" -s /bin/bash "$APP_USER"
    log "Usuário $APP_USER criado"
else
    log "Usuário $APP_USER já existe"
fi

# Cria diretórios
log "Criando estrutura de diretórios..."
mkdir -p "$APP_DIR"/{app,logs,uploads,backups}
mkdir -p /var/log/gunicorn
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chown -R "$APP_USER:$APP_USER" /var/log/gunicorn

# Configura PostgreSQL
log "Configurando PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE obito_db;" 2>/dev/null || warn "Banco já existe"
sudo -u postgres psql -c "CREATE USER obito_user WITH PASSWORD 'senha_segura_aqui';" 2>/dev/null || warn "Usuário já existe"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE obito_db TO obito_user;" 2>/dev/null
sudo -u postgres psql -c "ALTER USER obito_user CREATEDB;" 2>/dev/null

# Clona/Atualiza repositório (se REPO_URL definido)
if [[ -n "$REPO_URL" ]]; then
    log "Clonando repositório..."
    cd "$APP_DIR"
    if [[ -d ".git" ]]; then
        sudo -u "$APP_USER" git pull
    else
        sudo -u "$APP_USER" git clone "$REPO_URL" .
    fi
else
    warn "REPO_URL não definido - assumindo que arquivos já estão em $APP_DIR"
fi

# Cria ambiente virtual
log "Criando ambiente virtual Python..."
sudo -u "$APP_USER" python3.11 -m venv "$VENV_DIR"
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

# Configura arquivo .env
log "Configurando variáveis de ambiente..."
if [[ ! -f "$APP_DIR/.env" ]]; then
    cat > "$APP_DIR/.env" <<EOF
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://obito_user:senha_segura_aqui@localhost:5432/obito_db
ADMIN_PASSWORD=$(openssl rand -hex 16)
UPLOAD_FOLDER=$APP_DIR/uploads
MAX_CONTENT_LENGTH=16777216
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
EOF
    chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    warn "Arquivo .env criado - ALTERE AS SENHAS PADRÃO!"
else
    log "Arquivo .env já existe"
fi

# Executa migrações
log "Executando migrações do banco..."
cd "$APP_DIR"
sudo -u "$APP_USER" FLASK_ENV=production "$VENV_DIR/bin/flask" db upgrade 2>/dev/null || {
    warn "Flask-Migrate não configurado ou primeira execução - criando tabelas..."
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
        print('Admin criado')
"
}

# Configura Gunicorn
log "Configurando Gunicorn..."
cat > /etc/systemd/system/$SERVICE_NAME.service <<EOF
[Unit]
Description=Sistema de Óbito Goianira - Gunicorn
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=FLASK_ENV=production
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn \
    --workers 4 \
    --worker-class gthread \
    --threads 2 \
    --bind 127.0.0.1:5000 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log \
    --capture-output \
    run:app

Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF

# Configura Nginx
log "Configurando Nginx (porta 9010)..."
cat > "$NGINX_CONF" <<EOF
server {
    listen 9010;
    server_name svo.goianira.go.gov.br 192.168.0.225 _;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;
    
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
        alias $APP_DIR/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /uploads/ {
        alias $APP_DIR/uploads/;
        expires 1h;
        add_header Cache-Control "public";
    }
    
    # Health check
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:5000/health;
    }
}
EOF

ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Configura firewall
log "Configurando firewall..."
ufw --force enable
ufw allow ssh
ufw allow 9010/tcp  # Nginx na porta 9010 (svo.goianira.go.gov.br:9010)
# ufw allow 5432/tcp  # PostgreSQL (descomente se necessário externamente)
# ufw allow 6379/tcp  # Redis (descomente se necessário externamente)

# Configura backup automático
log "Configurando backup automático..."
cat > /etc/cron.d/sistema-obito-backup <<EOF
# Backup diário às 02:00
0 2 * * * $APP_USER $VENV_DIR/bin/python $APP_DIR/scripts/backup.py >> $APP_DIR/logs/backup.log 2>&1
# Limpeza de logs antigos (30 dias)
0 3 * * * root find $APP_DIR/logs -name "*.log" -mtime +30 -delete
EOF

# Configura renovação automática do certificado Let's Encrypt a cada 60 dias
log "Configurando renovação automática do certificado SSL (a cada 60 dias)..."
cat > /etc/cron.d/sistema-obito-ssl-renew <<EOF
# Renovação a cada 60 dias às 03:30 (certbot renew roda 2x/dia por padrão, mas forçamos a cada 60 dias)
0 3 */60 * * root certbot renew --quiet --nginx --post-hook "systemctl reload nginx" >> /var/log/letsencrypt-renew.log 2>&1
# Verificação diária adicional (padrão do certbot timer)
0 3 * * * root certbot renew --quiet --nginx >> /var/log/letsencrypt-renew-daily.log 2>&1
EOF

# Inicia serviços
log "Iniciando serviços..."
systemctl daemon-reload
systemctl enable postgresql redis-server nginx $SERVICE_NAME
systemctl restart postgresql redis-server nginx $SERVICE_NAME

# Aguarda serviços subirem
sleep 5

# Verifica status
log "Verificando status dos serviços..."
systemctl is-active --quiet postgresql && log "PostgreSQL: OK" || error "PostgreSQL falhou"
systemctl is-active --quiet redis-server && log "Redis: OK" || error "Redis falhou"
systemctl is-active --quiet nginx && log "Nginx: OK" || error "Nginx falhou"
systemctl is-active --quiet $SERVICE_NAME && log "Gunicorn: OK" || error "Gunicorn falhou"

# Testa endpoint
log "Testando endpoint..."
sleep 3
if curl -sf http://127.0.0.1:5000/health > /dev/null; then
    log "Health check: OK"
else
    warn "Health check falhou - verifique logs: journalctl -u $SERVICE_NAME"
fi

# Configura SSL com Let's Encrypt (automático)
log "Configurando SSL com Let's Encrypt para svo.goianira.go.gov.br..."
if certbot --nginx -d svo.goianira.go.gov.br --non-interactive --agree-tos --email admin@goianira.go.gov.br --redirect; then
    log "SSL configurado com sucesso! Certificado instalado."
    
    # Testa HTTPS
    sleep 2
    if curl -sf https://svo.goianira.go.gov.br:9010/health > /dev/null; then
        log "Health check HTTPS: OK"
    else
        warn "Health check HTTPS falhou - verifique configuração nginx"
    fi
else
    warn "Falha ao configurar SSL automaticamente."
    warn "Execute manualmente: certbot --nginx -d svo.goianira.go.gov.br"
fi

log "=== Deploy Concluído com Sucesso! ==="
log "Acesse: https://svo.goianira.go.gov.br:9010  ou  https://192.168.0.225:9010"
log "Login: admin / (senha definida em .env)"
log ""
log "⚠️  IMPORTANTE: Ao acessar pela primeira vez, o navegador avisará 'Site não seguro' / 'Conexão não é privada'."
log "   Isso é NORMAL para certificados Let's Encrypt em domínios internos/.gov.br sem HSTS pré-carregado."
log "   Clique em 'Avançado' → 'Prosseguir para svo.goianira.go.gov.br (não seguro)' para acessar."
log ""
log "✅ Renovação automática configurada: cron a cada 60 dias (03:30) + verificação diária (03:00)"
log "   Logs: /var/log/letsencrypt-renew.log  e  /var/log/letsencrypt-renew-daily.log"
log ""
log "Próximos passos:"
log "1. Altere senhas padrão no .env (ADMIN_PASSWORD, senha do PostgreSQL)"
log "2. Configure backup externo (S3, etc.)"
log "3. Monitore logs: journalctl -u $SERVICE_NAME -f"
log "4. Teste renovação: certbot renew --dry-run"